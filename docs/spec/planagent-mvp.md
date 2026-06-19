# Spec: PlanAgent MVP

## Objective
Build a personal learning project: a plan→execute agent that takes a task, breaks it into steps
using an LLM, then executes each step using SearXNG web search — with every tool call streaming
into the UI in real time.

**User:** You, alone. The UI makes the agent easy to drive and makes the internals visible.

**Success:** Type a task → see a plan → watch SearXNG tool calls arrive step by step in the
execution log.

## Tech Stack
- **Backend:** Python 3.11+, FastAPI, LangGraph, LangChain, `sse-starlette`
- **LLM:** OpenRouter via `langchain-openai` (OpenAI-compatible endpoint)
- **Search:** SearXNG at `https://searxng.merino-stork.ts.net/` via `langchain-community` `SearxSearchWrapper`
- **Frontend:** React 18, TypeScript, Vite

## Commands
```
# Install dependencies (creates/syncs virtualenv automatically)
uv sync
cd web && npm install

# Backend
uv run uvicorn server.app:app --reload --port 8000

# Frontend
cd web && npm run dev

# Tests
uv run pytest tests/

# One-off tools (no install needed)
uvx ruff check .
uvx ruff format .
```

## Project Structure
```
planagent/
├── agent/
│   ├── __init__.py
│   ├── schemas.py      # Pydantic: Plan, PlanStep, ExecutionEvent
│   ├── llm.py          # OpenRouter ChatOpenAI factory
│   ├── tools.py        # SearXNG search tool only
│   ├── planner.py      # task → Plan (structured output)
│   └── executor.py     # Plan → async stream of ExecutionEvents
├── server/
│   └── app.py          # FastAPI: /api/plan, /api/execute (SSE), /api/health
├── web/
│   └── src/
│       ├── App.tsx              # state: idle → planning → executing → done/error
│       ├── api.ts               # fetch + EventSource wrappers
│       └── components/
│           ├── TaskComposer.tsx # textarea + "Generate Plan" button
│           ├── PlanDisplay.tsx  # shows plan steps; execution auto-starts, no click required
│           └── ExecutionLog.tsx # streams events grouped by step
├── tests/
│   ├── test_planner.py
│   └── test_executor.py
├── docs/
│   ├── intent/planagent-mvp.md
│   └── spec/planagent-mvp.md
├── pyproject.toml  # dependencies + project metadata (uv managed)
├── uv.lock
└── .env.example
```

## Code Style
```python
# agent/tools.py — one tool, clearly named
from langchain_community.utilities import SearxSearchWrapper
from langchain_core.tools import tool
import os

_searx = SearxSearchWrapper(searx_host=os.environ["SEARXNG_URL"])

@tool
def web_search(query: str) -> str:
    """Search the web for current information."""
    return _searx.run(query)
```
- Type-annotate everything; use Pydantic models at all boundaries
- `async` throughout the FastAPI layer; sync is fine inside agent/tools
- React components: functional only, typed props, no `any`

## .env.example
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o
SEARXNG_URL=https://searxng.merino-stork.ts.net/
MAX_STEPS=10
SERVER_PORT=8000
VITE_API_BASE_URL=http://localhost:8000
```

## Testing Strategy
- **Framework:** pytest (backend), no frontend tests for MVP
- **Coverage:** smoke tests only — planner returns a valid `Plan`, executor emits `execution_finished`
- **Location:** `tests/` at repo root
- **MVP bar:** `uv run pytest tests/` passes before commit

## Boundaries
- **Always:** validate task input server-side before sending to LLM; keep API keys server-side only
- **Ask first:** adding tools beyond SearXNG, changing the SSE event schema, adding a database
- **Never:** accept API keys or model config from the client; expose raw LLM errors to the UI

## Success Criteria
1. `GET /api/health` returns `{"ok": true}`
2. `POST /api/plan` with a task returns a JSON plan with ≥1 numbered steps
3. `POST /api/execute` streams SSE events: `step_started` → `tool_started` → `tool_finished` → `step_finished` → `execution_finished`
4. UI displays each tool call as it arrives (not batched at the end)
5. Plan is shown in the UI before execution begins; execution starts automatically (no approval click)
6. Unreachable SearXNG or missing `OPENROUTER_API_KEY` produces a readable error in the UI, not a hang
