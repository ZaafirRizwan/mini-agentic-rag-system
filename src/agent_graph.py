import operator
from typing import Annotated, List, TypedDict, Union, Literal

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from dotenv import load_dotenv

from src.graph_rag import KnowledgeGraphRetriever
from src.tools import calculate, check_system_status

load_dotenv()

# 1. Initialize Components
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
kg = KnowledgeGraphRetriever()

@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the knowledge base for relevant information.
    Use this tool when the user asks questions that require external knowledge or specific documentation.
    """
    print(f"   ... 🔍 Graph Retrieval for: '{query}'")
    retrieved_data = kg.retrieve(query, hops=1)
    if not retrieved_data:
        return "No relevant context found."
    return retrieved_data

tools = [calculate, check_system_status, search_knowledge_base]
llm_with_tools = llm.bind_tools(tools)

# 2. Define State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    context: str # Kept for backward compatibility
    steps: List[str]
    verification_status: str # NEW: "PASS", "FAIL", or "SKIPPED"

# 3. Define Nodes

def reasoning_node(state: AgentState):
    """
    Decides whether to call a tool or answer directly.
    """
    messages = state["messages"]
    
    # System prompt to guide the agent
    system_prompt = (
        "You are a Staff Engineer for NeuralNexus. and you donot associate yourself with Google."
        "You have access to tools to calculate, check system status, and search the knowledge base. "
        "Use 'search_knowledge_base' if the user asks about technical concepts, documentation, or internal systems not covered by other tools. "
        "If you used a tool, explain the result clearly using the tool output. "
        "If the context explicitly mentions dependencies (like A needs B), highlight them."
    )
    
    # Check if we have a system message already, if not prepend it
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=system_prompt)] + messages
    
    response = llm_with_tools.invoke(messages)
    return {"messages": [response], "steps": ["reasoning_step"]}

def verification_node(state: AgentState):
    """
    Audits the answer against the retrieved context (if any).
    """
    messages = state["messages"]
    
    # Find the last AIMessage (the answer)
    agent_answer = messages[-1].content
    
    # Find context from the last ToolMessage if it was a search
    context = ""
    # Iterate backwards to find the last search result, but stop at the last HumanMessage
    # We ignore "CRITIQUE:" messages from the retry loop so we can still find the context
    for msg in reversed(messages[:-1]):
        if isinstance(msg, HumanMessage):
            if msg.content.startswith("CRITIQUE:"):
                continue
            break
        if isinstance(msg, ToolMessage) and msg.name == "search_knowledge_base":
            context = msg.content
            break
            
    if not context or context == "No relevant context found.":
        return {"steps": ["verification_skipped_no_context"], "verification_status": "SKIPPED"}

    verification_prompt = (
        "You are a Quality Assurance Auditor. "
        "Your job is to verify if the Agent's Answer is fully supported by the provided Context. "
        "Check for hallucinations or missing details. "
        "Output a brief assessment starting with 'VERIFICATION STATUS: [PASS/FAIL]' followed by your reasoning."
    )
    
    user_message = f"CONTEXT:\n{context}\n\nAGENT ANSWER:\n{agent_answer}"
    
    response = llm.invoke([SystemMessage(content=verification_prompt), HumanMessage(content=user_message)])
    
    # Parse status
    status = "PASS"
    if "VERIFICATION STATUS: FAIL" in response.content:
        status = "FAIL"
    
    return {
        "messages": [AIMessage(content=response.content)], 
        "steps": ["verification_complete"],
        "verification_status": status
    }

def retry_node(state: AgentState):
    """
    Analyzes the failure and generates a critique to guide the agent.
    """
    messages = state["messages"]
    last_verification = messages[-1].content
    
    critique_prompt = (
        "The previous answer failed verification. "
        "Analyze the verification failure and provide a specific instruction to the agent to fix the answer. "
        "Do not answer the user's question yourself, just provide the instruction."
    )
    
    response = llm.invoke([
        SystemMessage(content=critique_prompt), 
        HumanMessage(content=f"Verification Result:\n{last_verification}")
    ])
    
    # We add the critique as a HumanMessage (simulating a supervisor) so the agent sees it as a new instruction
    return {
        "messages": [HumanMessage(content=f"CRITIQUE: {response.content}")],
        "steps": ["retry_triggered"]
    }

# 4. Build Graph
workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("reasoning_node", reasoning_node)
workflow.add_node("tool_node", ToolNode(tools))
workflow.add_node("verification_node", verification_node)
workflow.add_node("retry_node", retry_node) # NEW NODE

# Edges
workflow.add_edge(START, "reasoning_node")

def route_logic(state):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tool_node"
    return "verification_node"

workflow.add_conditional_edges(
    "reasoning_node",
    route_logic,
    {
        "tool_node": "tool_node",
        "verification_node": "verification_node"
    }
)

workflow.add_edge("tool_node", "reasoning_node")

def check_verification(state):
    status = state.get("verification_status", "SKIPPED")
    if status == "FAIL":
        return "retry_node"
    return END

workflow.add_conditional_edges(
    "verification_node",
    check_verification,
    {
        "retry_node": "retry_node",
        END: END
    }
)

workflow.add_edge("retry_node", "reasoning_node") # Loop back

# 5. Compile with Checkpointer (Memory)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

def initialize_knowledge_base():
    # Load data once at startup
    if not kg.graph.nodes:
        print("⚠️ Knowledge Graph not found. Ingesting data...")
        kg.ingest("data/")
    else:
        print(f"✅ Knowledge Graph loaded with {len(kg.graph.nodes)} nodes.")