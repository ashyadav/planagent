from unittest.mock import MagicMock, patch

from agent.planner import PlannerAgent
from agent.schemas import Plan, PlanStep


def test_planner_returns_valid_plan():
    fixture = Plan(steps=[
        PlanStep(step=1, description="Search for latest Python release"),
        PlanStep(step=2, description="Summarize findings"),
    ])

    with patch("agent.planner.get_llm") as mock_get_llm:
        mock_llm = MagicMock()
        mock_llm.with_structured_output.return_value.invoke.return_value = fixture
        mock_get_llm.return_value = mock_llm

        agent = PlannerAgent()
        result = agent.plan("Find the latest Python release")

    assert isinstance(result, Plan)
    assert len(result.steps) == 2
    assert result.steps[0].step == 1
