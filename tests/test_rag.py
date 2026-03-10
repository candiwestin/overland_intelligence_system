"""
Phase 6 validation — RAG ingest and retriever tested with mocks.
No Ollama or Qdrant server required.
Run with: pytest tests/test_rag.py -v
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock
import tempfile
import os

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.embeddings import Embeddings


class FakeEmbeddings(Embeddings):
    """
    Minimal Embeddings subclass that satisfies QdrantVectorStore's isinstance
    check without requiring Ollama or any real embedding model.
    """
    def __init__(self, vector_size: int = 8):
        self._size = vector_size

    def embed_documents(self, texts):
        return [[0.1] * self._size for _ in texts]

    def embed_query(self, text):
        return [0.1] * self._size


def make_temp_txt(content: str) -> str:
    tmp = tempfile.NamedTemporaryFile(
        delete=False, suffix=".txt", mode="w", encoding="utf-8"
    )
    tmp.write(content)
    tmp.close()
    return tmp.name


# -----------------------------------------------------------------------------
# ingest tests
# -----------------------------------------------------------------------------

def test_ingest_single_text_file():
    from rag.ingest import ingest_documents
    path = make_temp_txt("The Baja 1000 is the world's premier off-road race.")
    try:
        store = ingest_documents([path], FakeEmbeddings())
        assert store is not None
    finally:
        os.unlink(path)


def test_ingest_returns_none_for_empty_list():
    from rag.ingest import ingest_documents
    store = ingest_documents([], FakeEmbeddings())
    assert store is None


def test_ingest_multiple_files():
    from rag.ingest import ingest_documents
    paths = [
        make_temp_txt("Overlanding gear market grew 18% in 2024."),
        make_temp_txt("Pre-runner builds are increasingly popular in Southwest markets."),
    ]
    try:
        store = ingest_documents(paths, FakeEmbeddings())
        assert store is not None
    finally:
        for p in paths:
            os.unlink(p)


def test_ingest_raises_on_embedding_failure():
    from rag.ingest import ingest_documents
    from tools.exceptions import RAGIngestionError

    class BrokenEmbeddings(Embeddings):
        def embed_documents(self, texts):
            raise Exception("Ollama not running")
        def embed_query(self, text):
            raise Exception("Ollama not running")

    path = make_temp_txt("Some content here.")
    try:
        with pytest.raises(RAGIngestionError):
            ingest_documents([path], BrokenEmbeddings())
    finally:
        os.unlink(path)


def test_load_text_from_file_object():
    from rag.ingest import _load_text
    import io
    fake_file = io.BytesIO(b"High Desert Expeditions runs guided overland trips.")
    fake_file.name = "notes.txt"
    docs = _load_text(fake_file, "notes.txt")
    assert len(docs) == 1
    assert "High Desert" in docs[0].page_content
    assert docs[0].metadata["source_file"] == "notes.txt"


# -----------------------------------------------------------------------------
# retriever tests
# -----------------------------------------------------------------------------

def test_retrieve_context_returns_empty_when_no_store():
    from rag.retriever import retrieve_context
    result = retrieve_context(None, "What is the Baja revenue trend?")
    assert result == []


def test_retrieve_context_with_scores_returns_empty_when_no_store():
    from rag.retriever import retrieve_context_with_scores
    result = retrieve_context_with_scores(None, "test query")
    assert result == []


def test_build_context_block_returns_empty_string_when_no_store():
    from rag.retriever import build_context_block
    result = build_context_block(None, "test query")
    assert result == ""


def test_retrieve_context_calls_similarity_search():
    from rag.retriever import retrieve_context
    from langchain_core.documents import Document

    mock_store = MagicMock()
    mock_store.similarity_search.return_value = [
        Document(page_content="Baja revenue grew 64% in 2024.", metadata={}),
        Document(page_content="Southwest region leads pre-runner sales.", metadata={}),
    ]
    results = retrieve_context(mock_store, "Baja growth")
    assert len(results) == 2
    assert "Baja revenue" in results[0]


def test_build_context_block_formats_correctly():
    from rag.retriever import build_context_block
    from langchain_core.documents import Document

    mock_store = MagicMock()
    mock_store.similarity_search.return_value = [
        Document(page_content="First chunk content.", metadata={}),
        Document(page_content="Second chunk content.", metadata={}),
    ]
    block = build_context_block(mock_store, "test")
    assert "[Document 1]" in block
    assert "[Document 2]" in block
    assert "---" in block


def test_retrieve_context_with_scores_returns_scored_dicts():
    from rag.retriever import retrieve_context_with_scores
    from langchain_core.documents import Document

    mock_store = MagicMock()
    mock_store.similarity_search_with_score.return_value = [
        (Document(page_content="Chunk A", metadata={"source_file": "doc.pdf"}), 0.92),
    ]
    results = retrieve_context_with_scores(mock_store, "test")
    assert results[0]["score"] == 0.92
    assert results[0]["source"] == "doc.pdf"
    assert results[0]["content"] == "Chunk A"