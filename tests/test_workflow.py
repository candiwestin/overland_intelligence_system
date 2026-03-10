"""
Phase 9 validation — LangGraph workflow tested with mocked agents.
Run with: pytest tests/test_workflow.py -v
"""
import json
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

SAMPLE_CSV = str(
    Path(__file__).resolve().parent.parent / "sample_data" / "hde_overland_sales_2022_2024.csv"
)

DEMO_QUESTION = (
    "Is the Baja and pre-runner segment growing fast enough to justify "
    "dedicated product lines?"
)


class SmartLLM:
    """
    Class-based LLM stub that routes responses by system prompt content.
    Avoids MagicMock side_effect exhaustion across multiple test invocations.
    """
    def invoke(self, messages):
        content = messages[0].content if messages else ""
        lower = content.lower()
        if "market research" in lower and "strategy consultant" not in lower:
            payload = {
                "market_summary": "Market research complete.",
                "market_findings": ["Finding A", "Finding B"],
                "supporting_data_alignment": "Aligned.",
                "market_gaps": ["Gap 1"],
                "search_queries_used": [],
            }
        elif "strategy consultant" in lower:
            payload = {
                "executive_summary": "HDE should act.",
                "recommendations": [{
                    "rank": 1,
                    "action": "Launch Baja line",
                    "rationale": "Strong growth signal",
                    "priority": "high",
                    "timeframe": "short_term",
                }],
                "opportunities": ["Pre-runner market gap"],
                "risks": ["Niche risk"],
                "confidence_score": 80,
            }
        else:
            payload = {
                "summary": "Data looks clean and revenue is growing.",
                "findings": ["Baja grew 64% YoY", "Southwest dominates"],
                "anomalies": [],
                "data_quality_notes": [],
                "recommended_deep_dives": [],
            }
        return MagicMock(content=json.dumps(payload))


def make_mock_llm():
    return SmartLLM()


def make_mock_embeddings():
    from langchain_core.embeddings import Embeddings

    class FakeEmbeddings(Embeddings):
        def embed_documents(self, texts):
            return [[0.1] * 8 for _ in texts]
        def embed_query(self, text):
            return [0.1] * 8

    return FakeEmbeddings()


# -----------------------------------------------------------------------------
# Graph construction tests
# -----------------------------------------------------------------------------

def test_build_graph_returns_compiled_graph():
    from graph.workflow import build_graph
    llm = make_mock_llm()
    embeddings = make_mock_embeddings()
    graph = build_graph(llm, embeddings)
    assert graph is not None


def test_graph_has_expected_nodes():
    from graph.workflow import build_graph
    llm = make_mock_llm()
    embeddings = make_mock_embeddings()
    graph = build_graph(llm, embeddings)
    node_names = set(graph.get_graph().nodes.keys())
    assert "ingest_rag" in node_names
    assert "data_analyst" in node_names
    assert "research" in node_names
    assert "insights" in node_names


# -----------------------------------------------------------------------------
# State schema tests
# -----------------------------------------------------------------------------

def test_bi_agent_state_has_required_keys():
    from graph.workflow import BIAgentState
    import typing
    hints = typing.get_type_hints(BIAgentState)
    required = [
        "uploaded_file_path", "business_question", "supporting_docs",
        "data_profile", "data_findings", "market_findings",
        "recommendations", "executive_summary", "confidence_score",
        "status", "errors",
    ]
    for key in required:
        assert key in hints, f"Missing key in BIAgentState: {key}"


# -----------------------------------------------------------------------------
# Full pipeline tests
# -----------------------------------------------------------------------------

def test_run_pipeline_completes():
    from graph.workflow import run_pipeline
    with patch("agents.research_agent.get_search_client") as mock_search:
        mock_search.return_value = MagicMock(
            invoke=MagicMock(return_value=[
                {"title": "T", "content": "C", "url": "https://x.com"}
            ])
        )
        result = run_pipeline(
            uploaded_file_path=SAMPLE_CSV,
            business_question=DEMO_QUESTION,
            llm=make_mock_llm(),
            embeddings=make_mock_embeddings(),
        )
    assert result is not None


def test_run_pipeline_returns_data_findings():
    from graph.workflow import run_pipeline
    with patch("agents.research_agent.get_search_client") as mock_search:
        mock_search.return_value = MagicMock(
            invoke=MagicMock(return_value=[])
        )
        result = run_pipeline(
            uploaded_file_path=SAMPLE_CSV,
            business_question=DEMO_QUESTION,
            llm=make_mock_llm(),
            embeddings=make_mock_embeddings(),
        )
    assert len(result.get("data_findings", [])) >= 1


def test_run_pipeline_returns_recommendations():
    from graph.workflow import run_pipeline
    with patch("agents.research_agent.get_search_client") as mock_search:
        mock_search.return_value = MagicMock(invoke=MagicMock(return_value=[]))
        result = run_pipeline(
            uploaded_file_path=SAMPLE_CSV,
            business_question=DEMO_QUESTION,
            llm=make_mock_llm(),
            embeddings=make_mock_embeddings(),
        )
    assert len(result.get("recommendations", [])) >= 1


def test_run_pipeline_status_set():
    from graph.workflow import run_pipeline
    with patch("agents.research_agent.get_search_client") as mock_search:
        mock_search.return_value = MagicMock(invoke=MagicMock(return_value=[]))
        result = run_pipeline(
            uploaded_file_path=SAMPLE_CSV,
            business_question=DEMO_QUESTION,
            llm=make_mock_llm(),
            embeddings=make_mock_embeddings(),
        )
    assert result.get("status") != "starting"


def test_run_pipeline_no_supporting_docs_skips_rag():
    from graph.workflow import run_pipeline
    with patch("agents.research_agent.get_search_client") as mock_search:
        mock_search.return_value = MagicMock(invoke=MagicMock(return_value=[]))
        result = run_pipeline(
            uploaded_file_path=SAMPLE_CSV,
            business_question=DEMO_QUESTION,
            llm=make_mock_llm(),
            embeddings=make_mock_embeddings(),
            supporting_docs=[],
        )
    assert result.get("vector_store") is None


def test_run_pipeline_errors_list_is_present():
    from graph.workflow import run_pipeline
    with patch("agents.research_agent.get_search_client") as mock_search:
        mock_search.return_value = MagicMock(invoke=MagicMock(return_value=[]))
        result = run_pipeline(
            uploaded_file_path=SAMPLE_CSV,
            business_question=DEMO_QUESTION,
            llm=make_mock_llm(),
            embeddings=make_mock_embeddings(),
        )
    assert isinstance(result.get("errors"), list)