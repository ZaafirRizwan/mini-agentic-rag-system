import uuid
from src.agent_graph import app, initialize_knowledge_base
from langchain_core.messages import HumanMessage
from termcolor import colored

def print_step(step_name):
    print(colored(f"   [Node Execution]: {step_name}", "cyan"))

def main():
    print(colored("🚀 Initializing Staff Agent System...", "green", attrs=['bold']))
    
    # 1. Ingest Data
    initialize_knowledge_base()
    
    # 2. Setup Thread for Memory (Persists across this session)
    # Use a fixed thread_id to allow persistence across restarts
    thread_id = "default_user_session"
    config = {"configurable": {"thread_id": thread_id}}
    
    print(colored("\nSystem Ready! (Type 'quit' to exit)", "green"))
    print(colored("----------------------------------------------------", "grey"))

    while True:
        user_input = input(colored("\nUser (You): ", "yellow"))
        if user_input.lower() in ["quit", "exit"]:
            break
            
        # Prepare state
        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        print(colored("\n--- 🤖 Agent Processing ---", "blue"))
        
        # Tracking variables
        nodes_traversed = []
        tools_used = []
        context_retrieved = "None"
        final_answer = ""
        
        # Stream execution
        try:
            for event in app.stream(inputs, config=config):
                for key, value in event.items():
                    nodes_traversed.append(key)
                    print_step(key)
                    
                    # Debugging output for specific nodes
                    if key in ["research_tools", "ops_tools"]:
                        # Inspect tool output
                        last_msg = value['messages'][-1]
                        tool_name = getattr(last_msg, 'name', 'unknown_tool')
                        tools_used.append(tool_name)
                        print(colored(f"      Tool Used: {tool_name}", "magenta"))
                        print(colored(f"      Tool Result: {last_msg.content[:100]}...", "magenta"))
                        
                        if tool_name == "search_knowledge_base":
                            context_retrieved = last_msg.content[:200] + "..." if len(last_msg.content) > 200 else last_msg.content

                    if key == "planner_node":
                        plan = value.get("plan")
                        if plan:
                            if plan.response:
                                print(colored(f"\n📝 Direct Response: {plan.response}", "green", attrs=['bold']))
                                final_answer = plan.response
                            else:
                                print(colored(f"   [Planner]: Generated {len(plan.tasks)} tasks", "cyan", attrs=['bold']))
                                for task in plan.tasks:
                                    print(colored(f"      - Task {task.id}: {task.description} (Agent: {task.assigned_agent})", "cyan"))

                    if key == "scheduler_node":
                        # Scheduler doesn't output much unless we want to see what's scheduled
                        pass

                    if key in ["research_agent", "ops_agent"]:
                        # Workers now return 'results', not messages
                        results = value.get("results", {})
                        for task_id, result in results.items():
                            print(colored(f"\n{key} (Task {task_id}): {result[:200]}...", "green", attrs=['bold']))
                    
                    if key == "synthesis_node":
                        final_answer = value['messages'][-1].content
                        print(colored(f"\n📝 Synthesis: {final_answer}", "green", attrs=['bold']))

                    if key == "verification_node":
                        if 'messages' in value:
                            audit_res = value['messages'][-1].content
                            print(colored(f"\n📝 {audit_res}", "yellow"))
                        else:
                            print(colored(f"\n📝 Verification Skipped", "yellow"))

                    if key == "retry_node":
                        critique = value['messages'][-1].content
                        print(colored(f"\n🔄 RETRY TRIGGERED: {critique}", "red", attrs=['bold']))
            
            # Print Workflow Summary
            print(colored("\n--- 📊 Workflow Trace ---", "white", attrs=['bold']))
            print(colored(f"Nodes Traversed: { ' -> '.join(nodes_traversed) }", "cyan"))
            print(colored(f"Tools Used: { ', '.join(tools_used) if tools_used else 'None' }", "magenta"))
            print(colored(f"Context Retrieved: {context_retrieved.replace(chr(10), ' ')}", "grey"))
            print(colored(f"Final Answer: {final_answer}", "green"))
            print(colored("-------------------------", "white"))
                        
        except Exception as e:
            print(colored(f"❌ Error: {str(e)}", "red"))

if __name__ == "__main__":
    main()