"""
Phase 7 validation — research_agent tested with mocks.
No API keys or Ollama required.
Run with: pytest tests/test_research_agent.py -v
"""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def make_mock_llm(market_findings=None, market_summary="Test summary.", market_gaps=None):
    payload = {
        "market_summary": market_summary,
        "market_findings": market_findings or ["Finding 1", "Finding 2"],
        "market_gaps": market_gaps or ["Gap 1"],
        "supporting_data_alignment": "Aligns well.",
        "search_queries_used": [],
    }
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content=json.dumps(payload))
    return mock


def make_mock_search_client(results=None):
    mock = MagicMock()
    mock.invoke.return_value = results or [
        {"title": "Overlanding Market 2024", "content": "Market grew 22%.", "url": "https://example.com"},
    ]
    return mock


BASE_STATE = {
    "business_question": "Is the Baja segment growing fast enough to justify dedicated product lines?",
    "data_findings": [
        "Baja revenue grew 64% year-over-year in 2024",
        "Southwest region dominates pre-runner sales",
    ],
    "vector_store": None,
    "errors": [],
}


# -----------------------------------------------------------------------------
# Core output tests
# -----------------------------------------------------------------------------

def test_research_agent_returns_market_findings():
    from agents.research_agent import run_research_agent
    llm = make_mock_llm()
    with patch("agents.research_agent.get_search_client", return_value=make_mock_search_client()):
        result = run_research_agent(dict(BASE_STATE), llm)
    assert "market_findings" in result
    assert len(result["market_findings"]) >= 1


def test_research_agent_returns_market_summary():
    from agents.research_agent import run_research_agent
    llm = make_mock_llm(market_summary="The Baja segment is growing fast.")
    with patch("agents.research_agent.get_search_client", return_value=make_mock_search_client()):
        result = run_research_agent(dict(BASE_STATE), llm)
    assert result["market_summary"] == "The Baja segment is growing fast."


def test_research_agent_returns_market_gaps():
    from agents.research_agent import run_research_agent
    llm = make_mock_llm(market_gaps=["No dedicated pre-runner product line exists in market"])
    with patch("agents.research_agent.get_search_client", return_value=make_mock_search_client()):
        result = run_research_agent(dict(BASE_STATE), llm)
    assert len(result["market_gaps"]) >= 1


def test_research_agent_stores_search_results():
    from agents.research_agent import run_research_agent
    llm = make_mock_llm()
    mock_results = [{"title": "T", "content": "C", "url": "https://x.com"}]
    with patch("agents.research_agent.get_search_client",
               return_value=make_mock_search_client(mock_results)):
        result = run_research_agent(dict(BASE_STATE), llm)
    assert "search_results" in result
    assert len(result["search_results"]) >= 1


# -----------------------------------------------------------------------------
# Fallback and error handling tests
# -----------------------------------------------------------------------------

def test_research_agent_falls_back_to_duckduckgo_on_search_failure():
    from agents.research_agent import run_research_agent
    from tools.exceptions import SearchProviderError
    llm = make_mock_llm()

    ddg_client = make_mock_search_client()

    def provider_side_effect(provider=None):
        if provider == "duckduckgo":
            return ddg_client
        raise SearchProviderError(provider="tavily", detail="Rate limit")

    with patch("agents.research_agent.get_search_client", side_effect=provider_side_effect):
        result = run_research_agent(dict(BASE_STATE), llm, search_provider="tavily")

    assert "market_findings" in result


def test_research_agent_records_search_error_in_state():
    from agents.research_agent import run_research_agent
    from tools.exceptions import SearchProviderError
    llm = make_mock_llm()

    def always_fail(provider=None):
        raise SearchProviderError(provider=provider or "tavily", detail="Unavailable")

    with patch("agents.research_agent.get_search_client", side_effect=always_fail):
        result = run_research_agent(dict(BASE_STATE), llm)

    assert len(result.get("errors", [])) >= 1


def test_research_agent_raises_on_llm_failure():
    from agents.research_agent import run_research_agent
    from tools.exceptions import LLMProviderError

    bad_llm = MagicMock()
    bad_llm.invoke.side_effect = Exception("LLM offline")

    with patch("agents.research_agent.get_search_client", return_value=make_mock_search_client()):
        with pytest.raises(LLMProviderError):
            run_research_agent(dict(BASE_STATE), bad_llm)


# -----------------------------------------------------------------------------
# Query builder tests
# -----------------------------------------------------------------------------

def test_build_search_queries_returns_list():
    from agents.research_agent import _build_search_queries
    queries = _build_search_queries(
        "Is the Baja segment growing fast enough to justify dedicated product lines?",
        ["Baja revenue grew 64% in 2024"]
    )
    assert isinstance(queries, list)
    assert len(queries) >= 1
    assert len(queries) <= 4


def test_build_search_queries_caps_at_four():
    from agents.research_agent import _build_search_queries
    queries = _build_search_queries(
        "Long question about Baja pre-runner growth in Southwest and Rocky Mountain regions",
        ["Baja grew 64%", "Southwest dominates", "Rocky Mountain growing"]
    )
    assert len(queries) <= 4


def test_extract_search_keywords_removes_stop_words():
    from agents.research_agent import _extract_search_keywords
    result = _extract_search_keywords("Is the Baja segment growing fast enough?")
    assert "is" not in result.lower()
    assert "the" not in result.lower()
    assert "baja" in result.lower()