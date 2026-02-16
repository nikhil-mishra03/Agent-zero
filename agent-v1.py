# agent-v0.py was a simple agent. 
# The goal now is to create an agent loop
# while task is not complete 
#    1. AI decides what to do next
#    2. Executes the action
#    3. Show the AI result
#    4. Goes back to step 1

import os
import subprocess
import sys
import json

from anthropic import Anthropic


def extract_action_and_command(message):
    for block in message.content:
        if getattr(block, "type", "") != "text":
            continue
        try:
            data = json.loads(block.text)
            return data.get("action"), data.get("command")
        except json.JSONDecodeError:
            continue
    return None, None


def main() -> int:
    SYSTEM_PROMPT = """You are a helpful assitant that can run bash commands.
    
    When the user gives you a task, responsd with a JSON in ONLY this format:
    {"action": "bash", "command": "your command here"}
    
    When the task is complete, respond with a JSON in ONLY this format:
    {"action": "done", "command": "your message here"}
    
    ONLY respond with JSON. No other markdown, text, code """
    messages = []
    user_prompt = " ".join(sys.argv[1:]).strip()
    if not user_prompt:
        print('Usage: python agent-v1.py "your prompt"')
        return 1
    
    messages.append( {
        'role': 'user',
        'content': user_prompt
    }
    )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY is not set.")
        return 1

    client = Anthropic(api_key=api_key)

    while True:
        try:
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                system = SYSTEM_PROMPT,
                messages=messages,
            )
        except Exception as exc:
            print(f"API request failed: {exc}", file=sys.stderr)
            return 1

        # For Debugging the LLM response
        # print(message)
        # break
        # print(response.content)
        ai_text = response.content[0].text
        messages.append({
            'role': 'assistant',
            'content': ai_text,
        })

        action, command = extract_action_and_command(response)
        if action == 'bash':
            print(f"Running {command} ")
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output = True,
                text = True)
            
            # Feed result back to AI
            message = "Command Output:\n" + json.dumps(
                {
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            messages.append({
                'role': 'user',
                'content': message,
            })

        elif action == 'done':
            print(f"Task complete summary: {command}")
            break
        else:
            print(f"Unknown action: {action}. Please try again.")
            message = f'Unknown action: {action}. Please try again.'
            


        


if __name__ == "__main__":
    raise SystemExit(main())

