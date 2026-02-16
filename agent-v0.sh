#!/bin/bash
# agent-v1.sh - The simplest possible agent

PROMPT="$1"

if [ -z "$PROMPT" ]; then
  echo "Usage: bash agent-v0.sh \"your prompt\""
  exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "Error: ANTHROPIC_API_KEY is not set."
  exit 1
fi

RESPONSE=$(curl https://api.anthropic.com/v1/messages \
-H "x-api-key: $ANTHROPIC_API_KEY" \
-H "Content-Type: application/json" \
-H "anthropic-version: 2023-06-01" \
-d '{
  "model": "claude-opus-4-5",
  "max_tokens": 1024,
  "messages": [
    {
     "role": "user", 
     "content": "'"$PROMPT"'\n\n Respond with only a bash command. No markdown, no explaination, no code blocks."
     }
   ]
  }') 

# echo "$RESPONSE"

# # Extract the bash command from the response
COMMAND=$(echo "$RESPONSE" | jq -r '.content[0].text')

echo "AI suggests: $COMMAND"
read -r -p "Run this command? (y/n) " CONFIRM

if [ "$CONFIRM" = "y" ]; then
  eval "$COMMAND"
fi
