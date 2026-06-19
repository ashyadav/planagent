from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.executor import ExecutorAgent
from agent.schemas import ExecutionFinishedEvent, Plan, PlanStep


@pytest.mark.asyncio
async def test_executor_emits_execution_finished():
    plan = Plan(steps=[PlanStep(step=1, description="Search for Python release notes")])

    async def fake_astream_events(messages, version):
        yield {"event": "on_tool_start", "name": "web_search", "data": {"input": {"query": "Python release"}}}
        yield {"event": "on_tool_end", "name": "web_search", "data": {"output": "Python 3.13 released"}}
        yield {"event": "on_chat_model_end", "name": "llm", "data": {"output": MagicMock(content="Done")}}

    mock_agent = MagicMock()
    mock_agent.astream_events = fake_astream_events

    with (
        patch("agent.executor.get_llm", return_value=MagicMock()),
        patch("agent.executor.create_react_agent", return_value=mock_agent),
    ):
        executor = ExecutorAgent()
        events = [e async for e in executor.stream("Find Python release", plan)]

    types = [e.type for e in events]
    assert "execution_finished" in types

    finished = next(e for e in events if e.type == "execution_finished")
    assert isinstance(finished, ExecutionFinishedEvent)
    assert finished.data["success"] is True
