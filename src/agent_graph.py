import operator
from typing import Annotated, List, TypedDict, Union, Literal, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver
from dotenv import load_dotenv

from src.graph_rag import KnowledgeGraphRetriever
from src.tools import calculate, check_system_status
from langchain_groq import ChatGroq
from termcolor import colored


import getpass
import os



load_dotenv()

# 1. Initialize Components
llm_planner = ChatGoogleGenerativeAI(model="gemini-2.5-pro", temperature=0)
llm_flash = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
kg = KnowledgeGraphRetriever()

@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the LOCAL internal knowledge base for relevant information.
    This is NOT an internet search. It searches our internal documents.
    ALWAYS use this tool for any query about Nexus, models, specs, or internal systems.
    """
    print(f"   ... 🔍 Graph Retrieval for: '{query}'")
    retrieved_data = kg.retrieve(query, hops=1)
    if not retrieved_data:
        return "No relevant context found."
    return retrieved_data

# Define Tool Sets
research_tools = [search_knowledge_base]
ops_tools = [calculate, check_system_status]

# Bind tools to specific agent LLMs
research_llm = llm_flash.bind_tools(research_tools)
ops_llm = llm_flash.bind_tools(ops_tools)

from pydantic import BaseModel, Field
from langgraph.constants import Send

# 2. Define State & Structures

class Task(BaseModel):
    id: int
    description: str
    assigned_agent: Literal["ResearchAgent", "OpsAgent"]
    dependencies: List[int] = Field(default_factory=list)
    status: Literal["pending", "running", "completed"] = "pending"
    result: str = ""

class Plan(BaseModel):
    tasks: List[Task] = Field(default_factory=list)
    response: Optional[str] = Field(default=None, description="Direct response for greetings or simple questions that don't need tools.")

def smart_merge_results(current: dict, update: dict) -> dict:
    """
    Smart reducer for results that handles turn-based clearing.
    If update contains '__turn__' key, it means we're starting a new turn and should clear.
    """
    if "__turn__" in update:
        # New turn signal - return only the update without '__turn__' marker
        return {k: v for k, v in update.items() if k != "__turn__"}
    # Normal merge - combine current and update
    return {**current, **update}

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    plan: Plan
    results: Annotated[dict, smart_merge_results] # {task_id: result_string}
    steps: List[str]
    verification_status: str # "PASS", "FAIL", or "SKIPPED"
    next: str # For Supervisor routing (legacy, kept for now)
    turn_id: int # Track conversation turns

# 3. Define Nodes

def planner_node(state: AgentState):
    """
    Analyzes the user request and generates a plan of tasks.
    """
    messages = state["messages"]
    user_request = messages[-1].content
    
    # Calculate current turn ID based on number of HumanMessages
    current_turn = sum(1 for m in messages if isinstance(m, HumanMessage))
    previous_turn = state.get("turn_id", 0)
    
    # Clear results if this is a new turn
    clear_results = (current_turn != previous_turn)
    
    planner_prompt = (
        "You are a Planner Agent. Your job is to break down the user's request into a set of tasks. "
        "Available Agents:\n"
        "1. ResearchAgent: Searches the knowledge base. Use for finding information, specs, docs.\n"
        "2. OpsAgent: Calculates values or checks system status. Use for math or system checks.\n\n"
        "Rules:\n"
        "- If the user's request is a simple greeting (e.g., 'hi', 'hello') or a pure chitchat that requires NO specific knowledge, provide a 'response' and leave 'tasks' empty.\n"
        "- CRITICAL: CHECK THE ENTIRE CONVERSATION HISTORY. If the answer is in previous messages (e.g., user told you their name), YOU MUST answer directly using 'response'. DO NOT create a ResearchAgent task for things you already know from history.\n"
        "- IF THE REQUEST REQUIRES NEW KNOWLEDGE (e.g., 'what is X', 'details about Y') AND is not in history, YOU MUST CREATE A TASK for the ResearchAgent. DO NOT answer directly.\n"
        "- Otherwise, create a list of tasks and leave 'response' empty.\n"
        "- Assign each task to the appropriate agent.\n"
        "- Identify dependencies. If Task B needs the result of Task A, add Task A's ID to Task B's dependencies.\n"
        "- If tasks are independent, they should have no dependencies (or only previous independent tasks).\n"
        "- Be granular. 'Research X and Calculate Y' should be two tasks."
    )
    
    planner_llm = llm_planner.with_structured_output(Plan)
    
    plan = planner_llm.invoke([SystemMessage(content=planner_prompt), HumanMessage(content=user_request)])
    
    if plan.response:
        print(colored(f"   [Planner]: Direct Response: {plan.response}", "cyan", attrs=['bold']))
        return {
            "plan": plan, 
            "messages": [AIMessage(content=plan.response)], 
            "results": {"__turn__": True} if clear_results else {},
            "turn_id": current_turn,
            "steps": ["planning_complete_direct"]
        }
    
    print(colored(f"   [Planner]: Generated {len(plan.tasks)} tasks.", "cyan", attrs=['bold']))
    for task in plan.tasks:
        print(colored(f"      - Task {task.id}: {task.description} (Agent: {task.assigned_agent}, Deps: {task.dependencies})", "cyan"))
    
    # Signal turn change if needed
    return {
        "plan": plan, 
        "results": {"__turn__": True} if clear_results else {},
        "turn_id": current_turn,
        "steps": ["planning_complete"]
    }

def scheduler_node(state: AgentState):
    """
    Pass-through node to trigger the scheduling logic.
    """
    return {}

def schedule_tasks(state: AgentState):
    """
    Determines which tasks are ready to run and schedules them.
    """
    try:
        plan = state["plan"]
        results = state["results"]
        
        # Check if all tasks are done
        all_done = all(t.id in results for t in plan.tasks)
        if all_done:
            return "synthesis_node"
        
        # Handle empty task list
        if not plan.tasks:
            print(colored("   [Scheduler]: No tasks to schedule, routing to synthesis", "yellow"))
            return "synthesis_node"
            
        # Find executable tasks
        scheduled_tasks = []
        for task in plan.tasks:
            if task.id in results:
                continue # Already done
                
            # Check dependencies
            dependencies_met = all(dep_id in results for dep_id in task.dependencies)
            
            if dependencies_met:
                # Schedule it!
                # Map agent name to node name
                node_name = "research_agent" if task.assigned_agent == "ResearchAgent" else "ops_agent"
                # We pass the task and the current results (so it can use dependency outputs)
                scheduled_tasks.append(Send(node_name, {"task": task, "results": results}))
                
        if not scheduled_tasks:
            # No tasks ready, but not all done? Possible deadlock or circular dependency
            print(colored("   [Scheduler]: Deadlock detected or circular dependencies. Forcing synthesis.", "red"))
            return "synthesis_node"
            
        return scheduled_tasks
    except Exception as e:
        print(colored(f"   [ERROR] Scheduler failed: {str(e)}. Routing to synthesis.", "red"))
        return "synthesis_node"

# Worker Input Schema
class WorkerInput(TypedDict):
    task: Task
    results: dict

def research_agent(state: WorkerInput):
    """
    Worker specialized in research.
    """
    task = state["task"]
    print(colored(f"   [ResearchAgent]: Starting Task {task.id}: {task.description}", "blue"))
    
    try:
        # Construct prompt with context from dependencies
        context = ""
        if task.dependencies:
            context = "Context from previous tasks:\n"
            for dep_id in task.dependencies:
                context += f"- Task {dep_id} Result: {state['results'].get(dep_id)}\n"
                
        system_prompt = (
            "You are a ResearchAgent. You have access to a tool called 'search_knowledge_base'. "
            "This tool searches our INTERNAL database. It is NOT the internet. "
            "Your goal is to complete the assigned task using the tool. "
            "Task: " + task.description + "\n" + context + "\n"
            "If you find relevant information, summarize it as the result. "
            "If no information is found, clearly state that."
        )
        
        # 1. Decide tool call
        msg = research_llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content="Please execute the task.")])
        
        result = msg.content
        if msg.tool_calls:
            # Execute tool
            tool_call = msg.tool_calls[0]
            if tool_call["name"] == "search_knowledge_base":
                try:
                    tool_output = search_knowledge_base.invoke(tool_call["args"])
                    # 2. Synthesize answer
                    final_msg = research_llm.invoke([
                        SystemMessage(content=system_prompt), 
                        HumanMessage(content="Please execute the task."),
                        msg,
                        ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"])
                    ])
                    result = final_msg.content
                except Exception as tool_error:
                    result = f"I encountered an error while searching: {str(tool_error)}. I cannot complete this task."
                
        return {"results": {task.id: result}}
    except Exception as e:
        error_msg = f"ResearchAgent encountered an error: {str(e)}. Unable to complete task '{task.description}'."
        print(colored(f"   [ERROR] {error_msg}", "red"))
        return {"results": {task.id: error_msg}}

def ops_agent(state: WorkerInput):
    """
    Worker specialized in operations.
    """
    task = state["task"]
    print(colored(f"   [OpsAgent]: Starting Task {task.id}: {task.description}", "magenta"))
    
    try:
        context = ""
        if task.dependencies:
            context = "Context from previous tasks:\n"
            for dep_id in task.dependencies:
                context += f"- Task {dep_id} Result: {state['results'].get(dep_id)}\n"
                
        system_prompt = (
            "You are an OpsAgent. You have access to 'calculate' and 'check_system_status'. "
            f"Task: {task.description}\n"
            f"{context}\n"
            "If the context contains multiple values (e.g., 500 billion and 7 billion), "
            "perform the operation on EACH value and report all results. "
            "Use the tools if needed."
        )
        
        # Build message history for tool pattern
        messages = [SystemMessage(content=system_prompt), HumanMessage(content="Execute the task.")]
        
        # First call
        response = ops_llm.invoke(messages)
        
        #If no tool calls, return the response
        if not response.tool_calls:
            return {"results": {task.id: response.content}}
        
        # Execute tools
        tool_results = []
        for tool_call in response.tool_calls:
            try:
                if tool_call["name"] == "calculate":
                    output = calculate.invoke(tool_call["args"])
                    tool_results.append(ToolMessage(content=str(output), tool_call_id=tool_call["id"]))
                elif tool_call["name"] == "check_system_status":
                    output = check_system_status.invoke(tool_call["args"])
                    tool_results.append(ToolMessage(content=str(output), tool_call_id=tool_call["id"]))
                else:
                    tool_results.append(ToolMessage(content=f"Unknown tool: {tool_call['name']}", tool_call_id=tool_call["id"]))
            except Exception as tool_error:
                tool_results.append(ToolMessage(content=f"Tool error: {str(tool_error)}", tool_call_id=tool_call["id"]))
        
        # Second call with tool results
        messages.append(response)
        messages.extend(tool_results)
        final_response = ops_llm.invoke(messages)
        
        return {"results": {task.id: final_response.content}}
    except Exception as e:
        error_msg = f"OpsAgent encountered an error: {str(e)}. Unable to complete task '{task.description}'."
        print(colored(f"   [ERROR] {error_msg}", "red"))
        return {"results": {task.id: error_msg}}

def verification_node(state: AgentState):
    """
    Audits the answer against the retrieved context (if any).
    """
    messages = state["messages"]
    
    # Find the last AIMessage (the answer)
    agent_answer = messages[-1].content
    
    # Find context from the last ToolMessage if it was a search
    context = ""
    # Iterate backwards to find the last search result
    for msg in reversed(messages[:-1]):
        if isinstance(msg, HumanMessage):
            if msg.content.startswith("CRITIQUE:"):
                continue
            # Don't break immediately on HumanMessage, as the Supervisor might have added intermediate messages?
            # Actually, in this new flow, Supervisor doesn't add messages to state, it just routes.
            # But the user input is a HumanMessage.
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
    
    response = llm_flash.invoke([SystemMessage(content=verification_prompt), HumanMessage(content=user_message)])
    
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
    
    response = llm_flash.invoke([
        SystemMessage(content=critique_prompt), 
        HumanMessage(content=f"Verification Result:\n{last_verification}")
    ])
    
    return {
        "messages": [HumanMessage(content=f"CRITIQUE: {response.content}")],
        "steps": ["retry_triggered"]
    }

def synthesis_node(state: AgentState):
    """
    Aggregates the responses from all agents into a final, cohesive answer.
    """
    # In the new flow, 'results' dict holds task outputs, not messages.
    # The original user request is in messages[0]
    user_request = state["messages"][0].content
    
    # Collect all results from the 'results' dict
    combined_info = "\n\n".join([f"Task {task_id}: {result}" for task_id, result in state["results"].items()])
    
    synthesis_prompt = (
        "You are a Senior Staff Engineer. donot associate yourself with google."
        "Your team of agents has gathered information to answer the user's request. "
        "Synthesize their findings into a single, complete, and professional response. "
        "Ensure you address ALL parts of the user's request. "
        "Do not mention 'ResearchAgent' or 'OpsAgent' by name, just present the information."
    )
    
    user_message = f"USER REQUEST: {user_request}\n\nAGENT FINDINGS:\n{combined_info}"
    
    response = llm_flash.invoke([SystemMessage(content=synthesis_prompt), HumanMessage(content=user_message)])
    
    return {"messages": [response], "steps": ["synthesis_complete"]}

# 4. Build Graph
workflow = StateGraph(AgentState)

# Nodes
workflow.add_node("planner_node", planner_node)
workflow.add_node("scheduler_node", scheduler_node)
workflow.add_node("research_agent", research_agent)
workflow.add_node("ops_agent", ops_agent)
workflow.add_node("synthesis_node", synthesis_node)
workflow.add_node("verification_node", verification_node)
workflow.add_node("retry_node", retry_node)

# Edges
workflow.add_edge(START, "planner_node")

def route_planner(state):
    plan = state["plan"]
    if plan.response:
        return "verification_node"
    return "scheduler_node"

workflow.add_conditional_edges(
    "planner_node",
    route_planner,
    {
        "verification_node": "verification_node",
        "scheduler_node": "scheduler_node"
    }
)

# Conditional Edge from Scheduler
workflow.add_conditional_edges(
    "scheduler_node",
    schedule_tasks,
    [
        "research_agent", 
        "ops_agent", 
        "synthesis_node"
    ]
)

# Workers return to Scheduler
workflow.add_edge("research_agent", "scheduler_node")
workflow.add_edge("ops_agent", "scheduler_node")

workflow.add_edge("synthesis_node", "verification_node")

# Verification Flow
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

workflow.add_edge("retry_node", "scheduler_node") # Loop back to scheduler to re-evaluate tasks

# 5. Compile with Checkpointer (Memory)
# 5. Compile with Checkpointer (Sqlite)
import sqlite3
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)
app = workflow.compile(checkpointer=memory)

def initialize_knowledge_base():
    # Load data once at startup
    if not kg.graph.nodes:
        print("⚠️ Knowledge Graph not found. Ingesting data...")
        kg.ingest("data/")
    else:
        print(f"✅ Knowledge Graph loaded with {len(kg.graph.nodes)} nodes.")