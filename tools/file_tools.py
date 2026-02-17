import os
import subprocess

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "write_file",
        "description": "Write content to a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
    "name": "edit_file",
    "description": "Make a precise edit to a file by replacing a unique string",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "old_str": {"type": "string", "description": "Exact string to find (must be unique in file)"},
            "new_str": {"type": "string", "description": "String to replace it with"}
        },
        "required": ["path", "old_str", "new_str"]
    }
    },
    {
        "name": "run_bash",
        "description": "Run a bash command",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to run"}
            },
            "required": ["command"]
        }
    }
]


def execute_tool(tool_name, input):
    if tool_name == "read_file":
        try:
            with open(input['path'], 'r') as file:
                return file.read()
        except Exception as e:
            return f"Error {e}"
    elif tool_name == "write_file":
        try:
            with open(input['path'], 'w') as file:
                file.write(input['content'])
                return f"Successfully written to file {input['path']}"
        except Exception as e:
            return f"Error {e}"
    elif tool_name == "edit_file":
        return edit_file(input['path'], input['old_str'], input['new_str'])
    elif tool_name == "run_bash":
        try:
            result = subprocess.run(
                input["command"], 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=20  # Added safety timeout
            )
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 20 seconds."
        except Exception as e:
            return f"Error running command: {e}"

def edit_file(path, old_str, new_str):
    with open(path, "r") as f:
        content = f.read()
    
    # Ensure the string is unique
    count = content.count(old_str)
    if count == 0:
        return f"Error: '{old_str}' not found in file"
    if count > 1:
        return f"Error: '{old_str}' found {count} times. Must be unique."
    
    new_content = content.replace(old_str, new_str)
    with open(path, "w") as f:
        f.write(new_content)
    
    return f"Successfully replaced text in {path}"