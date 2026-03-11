"""
Phase 12 validation — FastAPI backend
Run with: pytest tests/test_api.py -v
"""
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient

SAMPLE_CSV = Path(__file__).resolve().parent.parent / "sample_data" / "hde_overland_sales_2022_2024.csv"


# ----------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    from app_api import app
    return TestClient(app)


@pytest.fixture(scope="module")
def uploaded_file_id(client):
    """Upload the sample CSV once and return the file_id."""
    with patch("app_api.get_llm") as mock_llm, \
         patch("agents.question_suggester.generate_suggested_questions") as mock_qs:

        mock_llm.return_value = MagicMock()
        mock_qs.return_value = ["Question 1?", "Question 2?", "Question 3?"]

        with open(SAMPLE_CSV, "rb") as f:
            res = client.post("/upload", files={"file": ("test.csv", f, "text/csv")})

    assert res.status_code == 200
    return res.json()["file_id"]


# ----------------------------------------------------------------
# Health
# ----------------------------------------------------------------

def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_health_returns_version(client):
    res = client.get("/health")
    assert "version" in res.json()


# ----------------------------------------------------------------
# Upload
# ----------------------------------------------------------------

def test_upload_returns_200(client):
    with patch("app_api.get_llm"), \
         patch("agents.question_suggester.generate_suggested_questions", return_value=["Q1?","Q2?"]):
        with open(SAMPLE_CSV, "rb") as f:
            res = client.post("/upload", files={"file": ("data.csv", f, "text/csv")})
    assert res.status_code == 200

def test_upload_returns_file_id(client):
    with patch("app_api.get_llm"), \
         patch("agents.question_suggester.generate_suggested_questions", return_value=["Q1?"]):
        with open(SAMPLE_CSV, "rb") as f:
            res = client.post("/upload", files={"file": ("data.csv", f, "text/csv")})
    data = res.json()
    assert "file_id" in data
    assert len(data["file_id"]) == 36   # UUID

def test_upload_returns_row_count(client):
    with patch("app_api.get_llm"), \
         patch("agents.question_suggester.generate_suggested_questions", return_value=["Q1?"]):
        with open(SAMPLE_CSV, "rb") as f:
            res = client.post("/upload", files={"file": ("data.csv", f, "text/csv")})
    assert res.json()["rows"] > 0

def test_upload_returns_suggested_questions(client):
    with patch("app_api.get_llm"), \
         patch("agents.question_suggester.generate_suggested_questions", return_value=["Q1?","Q2?","Q3?"]):
        with open(SAMPLE_CSV, "rb") as f:
            res = client.post("/upload", files={"file": ("data.csv", f, "text/csv")})
    assert len(res.json()["suggested_questions"]) >= 1

def test_upload_rejects_bad_extension(client):
    res = client.post("/upload", files={"file": ("bad.txt", b"data", "text/plain")})
    assert res.status_code == 400

def test_upload_falls_back_on_suggester_failure(client):
    with patch("app_api.get_llm", side_effect=Exception("LLM down")):
        with open(SAMPLE_CSV, "rb") as f:
            res = client.post("/upload", files={"file": ("data.csv", f, "text/csv")})
    assert res.status_code == 200
    assert len(res.json()["suggested_questions"]) >= 1


# ----------------------------------------------------------------
# Analyze stream
# ----------------------------------------------------------------

def test_analyze_stream_returns_200(client, uploaded_file_id):
    with patch("app_api.get_llm") as mock_llm, \
         patch("app_api.get_embeddings") as mock_emb, \
         patch("agents.research_agent.get_search_client") as mock_search:

        from tests.test_workflow import SmartLLM
        from langchain_core.embeddings import Embeddings

        class FakeEmb(Embeddings):
            def embed_documents(self, texts): return [[0.1]*8 for _ in texts]
            def embed_query(self, text): return [0.1]*8

        mock_llm.return_value   = SmartLLM()
        mock_emb.return_value   = FakeEmb()
        mock_search.return_value = MagicMock(invoke=MagicMock(return_value=[]))

        res = client.post("/analyze/stream", json={
            "file_id":           uploaded_file_id,
            "business_question": "Is Baja growing fast enough?",
            "llm_provider":      "groq",
            "search_provider":   "duckduckgo",
        })
    assert res.status_code == 200

def test_analyze_stream_content_type(client, uploaded_file_id):
    with patch("app_api.get_llm") as mock_llm, \
         patch("app_api.get_embeddings") as mock_emb, \
         patch("agents.research_agent.get_search_client") as mock_search:

        from tests.test_workflow import SmartLLM
        from langchain_core.embeddings import Embeddings

        class FakeEmb(Embeddings):
            def embed_documents(self, texts): return [[0.1]*8 for _ in texts]
            def embed_query(self, text): return [0.1]*8

        mock_llm.return_value    = SmartLLM()
        mock_emb.return_value    = FakeEmb()
        mock_search.return_value = MagicMock(invoke=MagicMock(return_value=[]))

        res = client.post("/analyze/stream", json={
            "file_id":           uploaded_file_id,
            "business_question": "Is Baja growing fast enough?",
            "llm_provider":      "groq",
            "search_provider":   "duckduckgo",
        })
    assert "text/event-stream" in res.headers.get("content-type", "")

def test_analyze_stream_yields_result_event(client, uploaded_file_id):
    with patch("app_api.get_llm") as mock_llm, \
         patch("app_api.get_embeddings") as mock_emb, \
         patch("agents.research_agent.get_search_client") as mock_search, \
         patch("output.pdf_builder.build_pdf", return_value="/tmp/test.pdf"), \
         patch("pathlib.Path.exists", return_value=True):

        from tests.test_workflow import SmartLLM
        from langchain_core.embeddings import Embeddings

        class FakeEmb(Embeddings):
            def embed_documents(self, texts): return [[0.1]*8 for _ in texts]
            def embed_query(self, text): return [0.1]*8

        mock_llm.return_value    = SmartLLM()
        mock_emb.return_value    = FakeEmb()
        mock_search.return_value = MagicMock(invoke=MagicMock(return_value=[]))

        res = client.post("/analyze/stream", json={
            "file_id":           uploaded_file_id,
            "business_question": "Is Baja growing fast enough?",
            "llm_provider":      "groq",
            "search_provider":   "duckduckgo",
        })

    events = _parse_sse(res.text)
    event_types = [e.get("type") for e in events]
    assert "result" in event_types

def test_analyze_stream_unknown_file_id_returns_404(client):
    res = client.post("/analyze/stream", json={
        "file_id":           "nonexistent-id",
        "business_question": "test?",
        "llm_provider":      "groq",
        "search_provider":   "duckduckgo",
    })
    assert res.status_code == 404


# ----------------------------------------------------------------
# Download
# ----------------------------------------------------------------

def test_download_unknown_run_returns_404(client):
    res = client.get("/download/nonexistent-run-id")
    assert res.status_code == 404


# ----------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------

def _parse_sse(text: str) -> list[dict]:
    """Parse SSE stream text into list of event dicts."""
    events = []
    for line in text.split("\n"):
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except Exception:
                pass
    return events