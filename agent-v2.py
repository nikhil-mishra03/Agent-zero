# agent-v1 was a self sufficient agent which could reason and act
# But it exists without any security measures.
# No Perimission control - can access sensitive files / delete important data
# No timeout protection. Long running queries will stall other tasks. 
# No Output size controls. Large bash outputs - like errors or cat commands can exceed the context window of model


import os
import subprocess
import sys
import json
import re
from dotenv import load_dotenv

load_dotenv()

from anthropic import Anthropic

RISK_PATTERNS = [
    (r"(^|\s)(sudo|rm|mkfs|fdisk|dd|shutdown|reboot|poweroff|userdel|usermod|chmod|chown)(\s|$)", "sensitive command"),
    (r"\b(curl|wget)\b[^\n]*\|\s*(bash|sh)\b", "download-and-execute pattern"),
    (r"\brm\b[^\n]*\s-(?:[^\s]*[rf]|[^\s]*[fr])", "recursive/forced delete"),
    # (r"[;&`]|(\|\|)|(&&)|\$\(", "shell chaining/substitution"),
    (r"(^|\s)(/|/etc|/usr|/bin|/sbin|/var|/boot|~/.ssh)(/|\s|$)", "sensitive path"),
]

COMMAND_TIMEOUT_SEC = 15
MAX_OUTPUT_CHARS = 2000


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


def is_dangerous(cmd: str):

    # check if command seems dangereous
    cmd = cmd.strip()
    if not cmd:
        return True
    # for commands in SENSITIVE_PATTERNS:
    #     if re.search(commands, cmd):
    #         permission = True
    #         break

    for pattern,reason in RISK_PATTERNS:
        if re.search(pattern, cmd, flags = re.IGNORECASE):
            return True, reason
    
    return False, "ok"


def run_bash_command(command: str):
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output = True,
            text = True,
            timeout = COMMAND_TIMEOUT_SEC)
        
        # Feed result back to AI
        message = "Command Output:\n" + json.dumps(
            {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        return message

    except subprocess.TimeoutExpired as exc:

        # Feed result back in case of Timeout
        stdout = (exc.stdout or "")[:MAX_OUTPUT_CHARS]
        stderr = (exc.stderr or "")[:MAX_OUTPUT_CHARS]
        message = "Command Output:\n" + json.dumps({
            "exit_code": 124,
            "timed_out": True,
            "timeout_seconds": COMMAND_TIMEOUT_SEC,
            "stdout": stdout,
            "stderr": stderr,
        })
        return message


    




def main() -> int:
    SYSTEM_PROMPT = """You are a helpful assistant that can run bash commands.
    
    When the user gives you a task, respond with a JSON in ONLY this format:
    {"action": "bash", "command": "your command here"}
    
    When the task is complete, respond with a JSON in ONLY this format:
    {"action": "done", "command": "your message here"}
    
    ONLY respond with JSON. No other markdown, text, code """
    
    # Inefficient way of managing memeory but this will work for now
    # This will be improved in v3
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
            # print(f"Running {command} ")

            is_unsafe, reason = is_dangerous(command)    
            if is_unsafe:
                permission = input(f"Dangerous command detected. \n\n {command}\n{reason}\n\n Do you want to run it? (y/n) ")
                permission = permission.lower()
                if permission == 'y':
                    message = run_bash_command(command)
                else:
                    reason_input = input("Why did you deny permission? (optional, press Enter for default): ").strip()
                    if reason_input:
                        message = f"Permission denied. User reason: {reason_input}"
                    else:
                        message = "Permission denied to execute command. Use only safe commands"
        
            else:
                message = run_bash_command(command)

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

