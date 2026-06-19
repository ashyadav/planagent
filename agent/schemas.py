from __future__ import annotations

import os
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, Field, field_validator

MAX_STEPS = int(os.environ.get("MAX_STEPS", "10"))


class PlanStep(BaseModel):
    step: Annotated[int, Field(ge=1)]
    description: Annotated[str, Field(min_length=1)]


class Plan(BaseModel):
    steps: list[PlanStep]

    @field_validator("steps")
    @classmethod
    def validate_steps(cls, steps: list[PlanStep]) -> list[PlanStep]:
        if not steps:
            raise ValueError("Plan must have at least one step")
        if len(steps) > MAX_STEPS:
            raise ValueError(f"Plan exceeds MAX_STEPS ({MAX_STEPS})")
        nums = [s.step for s in steps]
        if nums != list(range(1, len(steps) + 1)):
            raise ValueError("Step numbers must be contiguous starting from 1")
        return steps


class StepStartedEvent(BaseModel):
    type: Literal["step_started"]
    data: dict[str, Any]


class ToolStartedEvent(BaseModel):
    type: Literal["tool_started"]
    data: dict[str, Any]


class ToolFinishedEvent(BaseModel):
    type: Literal["tool_finished"]
    data: dict[str, Any]


class StepFinishedEvent(BaseModel):
    type: Literal["step_finished"]
    data: dict[str, Any]


class ErrorEvent(BaseModel):
    type: Literal["error"]
    data: dict[str, Any]


class ExecutionFinishedEvent(BaseModel):
    type: Literal["execution_finished"]
    data: dict[str, Any]


ExecutionEvent = Annotated[
    Union[
        StepStartedEvent,
        ToolStartedEvent,
        ToolFinishedEvent,
        StepFinishedEvent,
        ErrorEvent,
        ExecutionFinishedEvent,
    ],
    Field(discriminator="type"),
]
