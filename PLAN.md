# Plan: PlanAgent — Simple Plan → Execute Agent

## Context
Build a **very simple** general-purpose agent that separates a **planning phase** (break a task into ordered steps) from an **execution phase** (run each step with tools). The goal is to learn how agents work by building one — specifically to see tool calls streaming into the UI in real time.

MVP scope (confirmed intent):
- **One tool: SearXNG** via a local instance — no API key, no external dependency.
- **No shell tool, no file I/O** — post-MVP.
- **No approval toggle** — execution starts automatically after planning.
- **Streaming execution log** is the core feature: watch each tool call arrive step by step.

Architecture:
- **One backend language (Python)**: FastAPI serves the agent directly — native Pydantic validation and native SSE streaming.
- **Thin React frontend** (Vite) talks directly to FastAPI over `fetch` + `EventSource`.
- **OpenRouter** wired the correct, documented way (no invented `langchain-openrouter` package).

Intended outcome: clone, set one `.env`, run two commands (`uvicorn` + `npm run dev`), type a task, watch it plan then execute with live streaming tool calls.

---

## Architecture

```
planagent/
├── agent/
│   ├── __init__.py
│   ├── schemas.py      # Pydantic: Plan, PlanStep, ExecutionEvent
│   ├── llm.py          # OpenRouter ChatOpenAI factory (env-driven)
│   ├── tools.py        # Brave search + restricted shell + workspace file I/O
│   ├── planner.py      # PlannerAgent: task -> Plan (structured output)
│   └── executor.py     # ExecutorAgent: Plan -> stream of ExecutionEvents
├── server/
│   └── app.py          # FastAPI: /api/plan, /api/execute (SSE), /api/health
├── web/
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx     # state machine: idle→planning→reviewing→executing→done/error
│       ├── api.ts      # typed fetch + EventSource wrappers
│       └── components/{TaskComposer,PlanReview,ExecutionLog}.tsx
├── requirements.txt
└── .env.example
```

One Python process is the whole backend. React is the only other runtime, and only because it's a real UI.

---

## Implementation

### 1. `requirements.txt`
```
langchain
langchain-openai
langchain-community
langgraph
fastapi
uvicorn[standard]
sse-starlette
python-dotenv
pydantic
```
No `langchain-openrouter` (does not exist). No `duckduckgo-search`.

### 2. `agent/schemas.py`
- `PlanStep`: `{ step: int (>=1), description: str (non-empty) }`
- `Plan`: `{ steps: list[PlanStep] }` — validators: ≥1 step, ≤ `MAX_STEPS` (env, default 10), step numbers positive and contiguous.
- `ExecutionEvent`: discriminated union with `type` in `{step_started, tool_started, tool_finished, step_finished, error, execution_finished}` plus a JSON-serializable `data` payload. Used for SSE.

### 3. `agent/llm.py`
Single factory so config lives in one place:
```python
from langchain_openai import ChatOpenAI
ChatOpenAI(
    base_url=os.environ["OPENROUTER_BASE_URL"],
    api_key=os.environ["OPENROUTER_API_KEY"],
    model=os.environ["OPENROUTER_MODEL"],
    temperature=0,
)
```
Confirmed against LangChain docs (OpenAI-compatible endpoint pattern). Keeps the app model-agnostic via `OPENROUTER_MODEL`.

### 4. `agent/tools.py`
- **SearXNG search**: `from langchain_community.utilities import SearxSearchWrapper` → `SearxSearchWrapper(searx_host=os.environ["SEARXNG_URL"])`, wrapped as a LangChain tool. Points at the local SearXNG instance. No API key needed.
- Shell and file I/O tools are **out of scope for MVP**.

### 5. `agent/planner.py` — `PlannerAgent`
- `llm.with_structured_output(Plan, method="json_schema")`.
- System prompt: decompose the task into a minimal ordered list of concrete, executable steps; no commentary.
- Returns a validated `Plan`. Raises on empty/oversized plans (schema enforces).

### 6. `agent/executor.py` — `ExecutorAgent`
- Builds a tool-calling agent via LangGraph `create_react_agent(model, tools)`.
- Iterates the **frozen** approved plan in order; each step is its own agent invocation with prior step outputs passed as context.
- `async` generator yielding `ExecutionEvent`s (step_started → tool_started/finished → step_finished …).
- On unrecoverable step failure: emit `error` event and stop; always end with `execution_finished`.

### 7. `server/app.py` — FastAPI
- `GET /api/health` → `{ "ok": true }`.
- `POST /api/plan` body `{ task }` → `{ plan }` (Pydantic validates in/out).
- `POST /api/execute` body `{ task, plan }` → **SSE** stream (`sse-starlette` `EventSourceResponse`) of `ExecutionEvent`s; cancels the generator if the client disconnects.
- Secrets/model config stay server-side via `.env`; never accepted from the client.
- CORS allows the Vite dev origin.

### 8. `web/` — thin React (Vite + TS)
- `api.ts`: `postPlan(task)` and `streamExecute(task, plan, onEvent)` (EventSource).
- `App.tsx`: state machine `idle → planning → reviewing → executing → done/error`; holds the approval toggle.
- `TaskComposer`: textarea + "Generate Plan" + approval toggle.
- `PlanReview`: numbered steps; if approval ON show "Approve & Execute", else auto-start execution on plan arrival.
- `ExecutionLog`: appends streamed events grouped by step, with tool calls and final output; loading/error states.

### 9. `.env.example`
```
OPENROUTER_API_KEY=your_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o
SEARXNG_URL=http://localhost:8080
MAX_STEPS=10
SERVER_PORT=8000
VITE_API_BASE_URL=http://localhost:8000
```

---

## Key Design Decisions
- **FastAPI, no Express, no CLI bridge**: one backend language; native Pydantic + native SSE. Removes the riskiest component (subprocess + stdout-NDJSON parsing) from the prior plan.
- **SearXNG over Brave Search**: local instance, no API key, removes an external dependency for MVP.
- **No approval toggle in MVP**: execution starts automatically after planning; keeps the flow simple while learning.
- **One tool only (MVP)**: SearXNG search is enough to see real tool calls streaming; shell and file I/O are post-MVP.
- **Env-driven, server-side config**: keys and model never touch the client, query string, or shell history.
- **Per-step agent invocation**: each step's tool use is isolated and individually streamable.

---

## Verification
1. `pip install -r requirements.txt`
2. `cp .env.example .env`; set `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `SEARXNG_URL` (default `http://localhost:8080`).
3. Backend smoke test (no UI):
   - `curl -s localhost:8000/api/health` → `{"ok":true}` after `uvicorn server.app:app --reload`.
   - `curl -s -XPOST localhost:8000/api/plan -H 'content-type: application/json' -d '{"task":"Search the web for the latest Python release and save a summary to summary.txt"}'` → JSON plan with numbered steps.
4. `cd web && npm install && npm run dev`; open the Vite URL.
5. End-to-end in the UI with task: *"Search the web for the latest Python release and summarize what's new"* — verify:
   - plan renders with numbered steps,
   - execution starts automatically (no approval step),
   - SearXNG tool calls stream into the log in real time,
   - missing `OPENROUTER_API_KEY` or unreachable `SEARXNG_URL` produces a clear error, not a hang.
