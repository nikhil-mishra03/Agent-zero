#!/usr/bin/env python3
import os
import subprocess
import sys

from anthropic import Anthropic


def main() -> int:
    prompt = " ".join(sys.argv[1:]).strip()
    if not prompt:
        print('Usage: python agent-v0.py "your prompt"')
        return 1

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY is not set.")
        return 1

    client = Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\n"
                        "Respond with only a bash command. "
                        "No markdown, no explanation, no code blocks."
                    ),
                }
            ],
        )
    except Exception as exc:
        print(f"API request failed: {exc}", file=sys.stderr)
        return 1

    command_parts = [
        block.text for block in message.content if getattr(block, "type", "") == "text"
    ]
    command = "\n".join(command_parts).strip()
    if not command:
        print("Error: Model returned no command text.")
        return 1

    print(f"AI suggests: {command}")
    confirm = input("Run this command? (y/n) ").strip().lower()
    if confirm == "y":
        subprocess.run(command, shell=True, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

