from __future__ import annotations

from typing import AsyncGenerator

from langgraph.prebuilt import create_react_agent

from agent.llm import get_llm
from agent.schemas import (
    ErrorEvent,
    ExecutionFinishedEvent,
    Plan,
    StepFinishedEvent,
    StepStartedEvent,
    ToolFinishedEvent,
    ToolStartedEvent,
)
from agent.tools import tools

ExecutionEvent = (
    StepStartedEvent
    | ToolStartedEvent
    | ToolFinishedEvent
    | StepFinishedEvent
    | ErrorEvent
    | ExecutionFinishedEvent
)


class ExecutorAgent:
    def __init__(self) -> None:
        self._agent = create_react_agent(get_llm(), tools)

    async def stream(self, task: str, plan: Plan) -> AsyncGenerator[ExecutionEvent, None]:
        prior_outputs: list[str] = []

        for plan_step in plan.steps:
            yield StepStartedEvent(type="step_started", data={
                "step": plan_step.step,
                "description": plan_step.description,
            })

            context = "\n".join(
                f"Step {i + 1} output: {o}" for i, o in enumerate(prior_outputs)
            )
            prompt = (
                f"Overall task: {task}\n\n"
                f"{('Prior steps:\n' + context + '\n\n') if context else ''}"
                f"Current step {plan_step.step}: {plan_step.description}"
            )

            step_output = ""
            try:
                async for event in self._agent.astream_events(
                    {"messages": [{"role": "user", "content": prompt}]},
                    version="v2",
                ):
                    kind = event["event"]

                    if kind == "on_tool_start":
                        yield ToolStartedEvent(type="tool_started", data={
                            "step": plan_step.step,
                            "tool": event["name"],
                            "input": event.get("data", {}).get("input", {}),
                        })

                    elif kind == "on_tool_end":
                        output = event.get("data", {}).get("output", "")
                        step_output = str(output)
                        yield ToolFinishedEvent(type="tool_finished", data={
                            "step": plan_step.step,
                            "tool": event["name"],
                            "output": step_output,
                        })

                    elif kind == "on_chat_model_end":
                        msg = event.get("data", {}).get("output")
                        if msg and not step_output:
                            step_output = str(msg.content) if hasattr(msg, "content") else str(msg)

            except Exception as exc:
                yield ErrorEvent(type="error", data={
                    "step": plan_step.step,
                    "message": str(exc),
                })
                yield ExecutionFinishedEvent(type="execution_finished", data={"success": False})
                return

            prior_outputs.append(step_output)
            yield StepFinishedEvent(type="step_finished", data={
                "step": plan_step.step,
                "output": step_output,
            })

        yield ExecutionFinishedEvent(type="execution_finished", data={"success": True})
