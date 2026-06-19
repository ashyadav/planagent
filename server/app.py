from __future__ import annotations

import json
import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agent.executor import ExecutorAgent
from agent.planner import PlannerAgent
from agent.schemas import Plan

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("VITE_API_BASE_URL", "http://localhost:5173").replace("8000", "5173"), "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PlanRequest(BaseModel):
    task: str


class ExecuteRequest(BaseModel):
    task: str
    plan: Plan


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.post("/api/plan")
def create_plan(req: PlanRequest) -> Plan:
    task = req.task.strip()
    if not task:
        raise HTTPException(status_code=422, detail="task must not be empty")
    try:
        return PlannerAgent().plan(task)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/execute")
async def execute_plan(req: ExecuteRequest) -> EventSourceResponse:
    executor = ExecutorAgent()

    async def event_generator():
        try:
            async for event in executor.stream(req.task, req.plan):
                yield {"data": json.dumps(event.model_dump())}
        except Exception as exc:
            yield {"data": json.dumps({"type": "error", "data": {"message": str(exc)}})}

    return EventSourceResponse(event_generator())
