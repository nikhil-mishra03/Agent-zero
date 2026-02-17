import os
import sys
import json
from dotenv import load_dotenv
from anthropic import Anthropic
from tools.file_tools import TOOLS as FILE_TOOLS, execute_tool as exec_file_tool
from tools.search_codebase import SEARCH_TOOLS, execute_tool as exec_search_tool
from prompts import SYSTEM_PROMPT

load_dotenv()

MAX_HISTORY = 50
MODEL_NAME = "claude-opus-4-5-20251101"

# Subagent Tool
SUBAGENT_TOOL = {
    "name": "delegate_subagent",
    "description": "Delegate a complex sub-task to a focused sub-agent. Returns the final answer from the sub-agent.",
    "input_schema": {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "The description of the task for the sub-agent"},
        },
        "required": ["task"]
    }
}


# Combine schemas for all tools
ALL_TOOLS = FILE_TOOLS + SEARCH_TOOLS + [SUBAGENT_TOOL]

def check_permission(tool_name, tool_input):

    if tool_name == "run_bash":
        cmd = tool_input.get("command", "")
        print(f"\n !!! Bash Command: {cmd}")
        response = input("Allow? (y/n/reason): ").strip()
        if response.lower() == "y":
            return True, None
        return False, response if response else "User denied permission"
        
    elif tool_name == "write_file":
        path = tool_input.get("path", "")
        print(f"\n📝 Writing/Editing: {path}")
        response = input("Allow? (y/n): ").strip().lower()
        if response == "y":
            return True, None
        return False, "User denied permission"
        
    return True, None

HISTORY_FILE = "history.json"

def load_summary():
    """Load the summarized history from file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                data = json.load(f)
                return data.get("summary", "")
        except Exception:
            pass
    return ""

def save_summary(summary):
    """Save the summarized history to file."""
    with open(HISTORY_FILE, "w") as f:
        json.dump({"summary": summary}, f, indent=2)



def run_agent(task, tools=ALL_TOOLS, max_turns=10, depth=0):
    
    # track recursion depth to prevent infinite subagent loops. 
    if depth > 3:
        return "Error: Maximum subagent recursion depth reached."
          
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)
    
    formatted_system = SYSTEM_PROMPT.format(current_directory=os.getcwd())
    
    messages = [{"role": "user", "content": task}]
    final_answer = "No answer provided"
    turn_count = 0
    
    while turn_count < max_turns:
        turn_count += 1
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=2048,
                system=formatted_system,
                tools=tools,
                messages=messages
            )
            
            messages.append({"role": "assistant", "content": response.content})
            
            # Print text content
            for block in response.content:
                if block.type == "text":
                    print(f"\n🤖 {block.text}")
                    final_answer = block.text

            if response.stop_reason != "tool_use":
                return final_answer

            # Process tool calls
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    print(f"\n🔧 {tool_name}: {json.dumps(tool_input)}")

                    # Handle Subagent Delegation
                    if tool_name == "delegate_subagent":
                        sub_task = tool_input["task"]
                        # Recursively call run_agent
                        result = run_agent(sub_task, tools, max_turns, depth + 1)
                        result = f"Subagent Result: {result}"
                    else:
                        allowed, reason = check_permission(tool_name, tool_input)
                        if not allowed:
                            result = f"Permission denied: {reason}"
                            print(f"   🚫 {result}")
                        else:
                            try:
                                if any(t["name"] == tool_name for t in FILE_TOOLS):
                                    result = exec_file_tool(tool_name, tool_input)
                                elif any(t["name"] == tool_name for t in SEARCH_TOOLS):
                                    result = exec_search_tool(tool_name, tool_input)
                                else:
                                    result = f"Error: Unknown tool {tool_name}"
                            except Exception as e:
                                result = f"Error executing tool: {e}"
                    
                    # Display truncation
                    display = result[:200] + "..." if len(result) > 200 else result
                    print(f"   → {display}")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result
                    })

            if tool_results:
                messages.append({"role": "user", "content": tool_results})
            else:
                break
                
        except Exception as e:
            print(f"\n🔥 Critical Error: {e}")
            return f"Error: {e}"
            
    return final_answer

def main():
    load_dotenv()
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY not found. Please set it in .env or environment.")
        return 1
        
    # Get user prompt
    user_prompt = " ".join(sys.argv[1:]).strip()
    if not user_prompt:
        print('Usage: python agent-v3.py "your task"')
        return 1
        
    # Start the main agent loop
    result = run_agent(user_prompt)
    
    # Save a simple summary
    current_summary = load_summary()
    new_summary = f"{current_summary}\n- Task: {user_prompt}\n  Result: {result}\n"
    save_summary(new_summary)
    
    print(f"\n✅ Session finished. History updated.")

if __name__ == "__main__":
    sys.exit(main())
