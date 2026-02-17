# Mini-Claude: Building a Tool-Using Custom Agent

This repository documents the journey of building a **Mini-Claude** agent from scratch, heavily inspired by [Nader Dabit's experiment](https://x.com/dabit3/status/2009668398691582315).

The goal was to create a lightweight, autonomous coding agent that can read/write files, search the codebase, and even delegate tasks to itself recursively—mirroring the core capabilities of advanced agents like Claude Code or Devin, but in a simple Python script.

## The Evolution

### 1. Agent v1: The Basics (Simple LLM Loop)
We started with a simple loop:
- **Input**: User prompt.
- **Processing**: Send to Anthropic API.
- **Output**: Print response.
*Limitation*: It could only "talk", not "do". It had no access to the outside world.

### 2. Agent v2: Safe Command Execution
To make it useful, we gave it a **Bash Tool**.
- **Capability**: It could run shell commands (`ls`, `cat`, `grep`).
- **Safety**: We implemented a `check_permission` guardrail. Any potentially dangerous command (like `rm`, `mv` or `>`) triggers a user confirmation prompt.
- **Context**: We started managing `history` manually, appending tool outputs back to the conversation so the agent knew what happened.

### 3. Agent v3: Native Tools & Structure (The "Mini-Claude")
This is the current robust version. We moved from "prompt engineering" tool use to **Anthropic's Native Tool Use API**.

#### Key Features & Architecture

**🛠️ Tool Abstraction**
Instead of just running bash, we created specific, safer tools:
- `read_file`, `write_file`, `edit_file`: Atomic file operations.
- `glob`, `grep`: Codebase navigation.
- `run_bash`: Fallback for complex commands (still sandboxed by permission checks).

**🧠 Context Management**
As the conversation grows, the context window fills up.
- **Solution**: We implemented a **Sliding Window** (or pruning) in early versions, but v3 relies on a more intelligent "Session Summary" approach.
- **Token Efficiency**: Instead of re-reading every file every time, the agent reads only what it needs (`read_file`), keeping the context lean.

**💾 Memory persistence**
We wanted the agent to "remember" past sessions without keeping the entire history (which costs tokens).
- **Implementation**: `history.json`
- **Mechanism**: At the end of a session, we save a **text summary** of what was accomplished.
- **Injection**: When you start a new run, this summary is injected into the **System Prompt**, giving the agent "long-term memory" of the project state.

**🤖 Recursive Sub-Agents (`delegate_subagent`)**
Perhaps the most powerful feature.
- **Problem**: Complex tasks (e.g., "Refactor this entire module") confuse a single agent loop or fill context too fast.
- **Solution**: We added a `delegate_subagent` tool.
- **How it works**: The main agent can spawn a **fresh instance** of itself (a sub-call to `run_agent`) with a specific sub-task.
- **Benefit**: The sub-agent has a **fresh, empty context**. It solves its specific problem, returns the *final answer string* to the parent, and then dies. The parent gets the result without the token bloat of the sub-agent's internal reasoning.

## How to Run

1.  **Install Dependencies**:
    ```bash
    pip install anthropic python-dotenv
    ```
2.  **Set API Key**:
    Create `.env` with `ANTHROPIC_API_KEY=sk-...`
3.  **Run**:
    ```bash
    python3 agent-v3.py "Analyze the tools directory and summarize the capabilities"
    ```

## Files Structure
- `agent-v3.py`: The core agent loop and logic.
- `prompts.py`: The System Prompt (personality and guidelines).
- `tools/`:
  - `file_tools.py`: File system operations.
  - `search_codebase.py`: Search capabilities.
- `history.json`: Persistent memory file.
