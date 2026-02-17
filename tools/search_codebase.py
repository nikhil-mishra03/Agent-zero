SEARCH_TOOLS = [
    {
        "name": "glob",
        "description": "Find files matching a pattern",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern (e.g., '**/*.py')"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "grep",
        "description": "Search for a pattern in files",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "path": {"type": "string", "description": "Directory or file to search in"}
            },
            "required": ["pattern"]
        }
    }
]

import glob
import os
import re

def execute_tool(tool_name, input):
    if tool_name == "glob":
        try:
            files = glob.glob(input['pattern'], recursive=True)
            return "\n".join(files) if files else "No files found matching pattern."
        except Exception as e:
            return f"Error executing glob: {e}"
            
    elif tool_name == "grep":
        try:
            pattern = input['pattern']
            path = input.get('path', '.')
            
            # Simple python-based grep for cross-platform compatibility
            results = []
            if os.path.isfile(path):
                search_files = [path]
            else:
                search_files = []
                for root, _, files in os.walk(path):
                    for file in files:
                        search_files.append(os.path.join(root, file))
            
            for file_path in search_files:
                try:
                    with open(file_path, 'r', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                results.append(f"{file_path}:{i}: {line.strip()}")
                except Exception:
                    continue  # Skip unreadable files
                    
            return "\n".join(results[:100]) if results else "No matches found."
            
        except Exception as e:
            return f"Error executing grep: {e}"
