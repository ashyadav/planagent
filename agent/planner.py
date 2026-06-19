from __future__ import annotations

from agent.llm import get_llm
from agent.schemas import Plan

_SYSTEM = (
    "You are a planning assistant. Given a task, decompose it into a minimal ordered list "
    "of concrete, executable steps. Return only the plan — no commentary."
)


class PlannerAgent:
    def __init__(self) -> None:
        self._chain = get_llm().with_structured_output(Plan, method="json_schema")

    def plan(self, task: str) -> Plan:
        return self._chain.invoke([
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": task},
        ])
