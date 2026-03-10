"""
Phase 8 validation — insights_agent tested with mocks.
Run with: pytest tests/test_insights_agent.py -v
"""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def make_mock_llm(recommendations=None, executive_summary="HDE should act now.",
                  opportunities=None, risks=None, confidence_score=82):
    payload = {
        "executive_summary": executive_summary,
        "recommendations": recommendations or [
            {
                "rank": 1,
                "action": "Launch a dedicated Baja product line in Q2",
                "rationale": "Baja revenue grew 64% YoY and market research confirms segment expansion",
                "priority": "high",
                "timeframe": "short_term",
            },
            {
                "rank": 2,
                "action": "Prioritize Southwest and Texas/Mexico Border regions for distribution",
                "rationale": "These regions drive 58% of pre-runner sales and show continued growth",
                "priority": "high",
                "timeframe": "immediate",
            },
        ],
        "opportunities": opportunities or [
            "Pre-runner segment underserved by current gear manufacturers"
        ],
        "risks": risks or ["Segment could remain niche if Baja racing attendance declines"],
        "confidence_score": confidence_score,
    }
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content=json.dumps(payload))
    return mock


BASE_STATE = {
    "business_question": "Is the Baja segment growing fast enough to justify dedicated product lines?",
    "data_findings": [
        "Baja revenue grew 64% year-over-year in 2024",
        "Southwest and Texas/Mexico Border account for 58% of pre-runner transactions",
    ],
    "market_findings": [
        "Off-road racing participation up 31% nationally since 2021",
        "Pre-runner vehicle registrations grew 18% in Southwest states in 2024",
    ],
    "market_gaps": [
        "No major gear manufacturer has a dedicated pre-runner product line",
    ],
    "data_health_score": 91,
    "errors": [],
}


# -----------------------------------------------------------------------------
# Core output tests
# -----------------------------------------------------------------------------

def test_insights_agent_returns_recommendations():
    from agents.insights_agent import run_insights_agent
    result = run_insights_agent(dict(BASE_STATE), make_mock_llm())
    assert "recommendations" in result
    assert len(result["recommendations"]) >= 1


def test_insights_agent_returns_executive_summary():
    from agents.insights_agent import run_insights_agent
    result = run_insights_agent(dict(BASE_STATE), make_mock_llm())
    assert "executive_summary" in result
    assert len(result["executive_summary"]) > 0


def test_insights_agent_returns_confidence_score():
    from agents.insights_agent import run_insights_agent
    result = run_insights_agent(dict(BASE_STATE), make_mock_llm(confidence_score=82))
    assert result["confidence_score"] == 82


def test_insights_agent_returns_opportunities():
    from agents.insights_agent import run_insights_agent
    result = run_insights_agent(dict(BASE_STATE), make_mock_llm())
    assert "opportunities" in result
    assert len(result["opportunities"]) >= 1


def test_insights_agent_carries_gaps_forward():
    from agents.insights_agent import run_insights_agent
    result = run_insights_agent(dict(BASE_STATE), make_mock_llm())
    assert result["gaps"] == BASE_STATE["market_gaps"]


# -----------------------------------------------------------------------------
# Recommendation structure tests
# -----------------------------------------------------------------------------

def test_recommendations_have_required_keys():
    from agents.insights_agent import run_insights_agent
    result = run_insights_agent(dict(BASE_STATE), make_mock_llm())
    for rec in result["recommendations"]:
        assert "rank" in rec
        assert "action" in rec
        assert "rationale" in rec
        assert "priority" in rec
        assert "timeframe" in rec


def test_recommendations_normalized_when_keys_missing():
    from agents.insights_agent import run_insights_agent
    incomplete_recs = [{"action": "Do something", "rationale": "Because reasons"}]
    result = run_insights_agent(dict(BASE_STATE), make_mock_llm(recommendations=incomplete_recs))
    rec = result["recommendations"][0]
    assert rec["priority"] == "medium"
    assert rec["timeframe"] == "short_term"
    assert rec["rank"] == 1


def test_confidence_score_clamped_to_100():
    from agents.insights_agent import run_insights_agent
    result = run_insights_agent(dict(BASE_STATE), make_mock_llm(confidence_score=150))
    assert result["confidence_score"] == 100


def test_confidence_score_clamped_to_zero():
    from agents.insights_agent import run_insights_agent
    result = run_insights_agent(dict(BASE_STATE), make_mock_llm(confidence_score=-10))
    assert result["confidence_score"] == 0


# -----------------------------------------------------------------------------
# Error handling
# -----------------------------------------------------------------------------

def test_insights_agent_raises_on_llm_failure():
    from agents.insights_agent import run_insights_agent
    from tools.exceptions import LLMProviderError
    bad_llm = MagicMock()
    bad_llm.invoke.side_effect = Exception("Model not available")
    with pytest.raises(LLMProviderError):
        run_insights_agent(dict(BASE_STATE), bad_llm)


def test_insights_agent_raises_on_invalid_json():
    from agents.insights_agent import run_insights_agent
    from tools.exceptions import LLMProviderError
    bad_llm = MagicMock()
    bad_llm.invoke.return_value = MagicMock(content="not valid json {{{")
    with pytest.raises(LLMProviderError):
        run_insights_agent(dict(BASE_STATE), bad_llm)


# -----------------------------------------------------------------------------
# Helper unit tests
# -----------------------------------------------------------------------------

def test_clamp_within_bounds():
    from agents.insights_agent import _clamp
    assert _clamp(50, 0, 100) == 50
    assert _clamp(150, 0, 100) == 100
    assert _clamp(-5, 0, 100) == 0


def test_clamp_handles_bad_input():
    from agents.insights_agent import _clamp
    assert _clamp(None, 0, 100) == 0
    assert _clamp("bad", 0, 100) == 0