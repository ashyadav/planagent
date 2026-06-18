# Plan: PlanAgent — Plan-then-Execute Agent with Web UI

## Context
Building a general-purpose AI agent from scratch that explicitly separates the **planning phase** (breaking a user task into steps) from the **execution phase** (running those steps using tools). The user wants a simple web UI, LangChain for model-agnostic orchestration, and OpenRouter as the LLM provider. An optional approval gate lets the user review and confirm the plan before execution begins.

---

## Architecture

```
planagent/
├── agent/
│   ├── __init__.py
│   ├── planner.py      # Generates structured plan from user task
│   ├── executor.py     # Runs each plan step using tools + LangChain agent
│   └── tools.py        # Tool definitions (web search, shell, file I/O)
├── ui/
│   └── app.py          # Streamlit web UI
├── requirements.txt
└── .env.example
```

---

## Implementation Plan

### 1. `requirements.txt`
```
langchain
langchain-openai
langchain-community
streamlit
duckduckgo-search
python-dotenv
```

### 2. `agent/tools.py`
Define three LangChain tools:
- **Web search**: `DuckDuckGoSearchRun` from `langchain_community.tools`
- **Shell execution**: `ShellTool` from `langchain_community.tools`
- **File I/O**: two simple custom tools — `ReadFileTool` and `WriteFileTool` wrapping Python `open()`

### 3. `agent/planner.py` — `PlannerAgent`
- Takes a user task string
- Calls the LLM once with a structured prompt instructing it to return a numbered JSON list of steps: `[{"step": 1, "description": "..."}]`
- Uses `langchain_openai.ChatOpenAI` pointed at OpenRouter (`openai_api_base="https://openrouter.ai/api/v1"`)
- Returns a `Plan` dataclass: `list[PlanStep]`

### 4. `agent/executor.py` — `ExecutorAgent`
- Takes a `Plan` and executes each step using a LangChain ReAct agent with the tools from `tools.py`
- Yields `(step_index, output)` tuples so the UI can stream progress step by step
- Each step is a separate agent invocation with the step description as the task

### 5. `ui/app.py` — Streamlit UI
Layout:
1. **Sidebar**: model selector (dropdown, defaults to `openai/gpt-4o`), approval toggle checkbox
2. **Main area**:
   - Text area: "Describe your task"
   - "Generate Plan" button → calls `PlannerAgent`, renders plan as numbered list
   - If approval toggle ON: "Approve & Execute" button; if OFF: auto-executes after plan renders
   - Execution output: expander per step showing the agent's tool calls and final answer
   - Stream output using `st.write_stream` or `st.empty()` + generator

### 6. `.env.example`
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

---

## Key Design Decisions
- **No agent framework** beyond LangChain core — keeps it simple and transparent
- **Streamlit** for the UI — zero frontend code, fast to build, works great for streaming text
- **Approval flag** is a UI toggle (checkbox), not a CLI flag, since the interface is web-based
- **ReAct agent per step** (not one agent for the whole plan) — makes each step's tool use isolated and visible

---

## Verification
1. `pip install -r requirements.txt`
2. Copy `.env.example` → `.env`, add OpenRouter API key
3. `streamlit run ui/app.py`
4. Enter a task like "Search the web for the latest Python release and save a summary to output.txt"
5. Verify: plan renders with numbered steps, approval toggle blocks execution until clicked, each step shows tool calls + output
