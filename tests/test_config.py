"""
Phase 1 validation — settings and exceptions load without errors.
Run with: pytest tests/test_config.py -v
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_settings_loads():
    from config.settings import settings
    assert settings.app_name == "Overland Intelligence System"
    assert settings.app_version == "1.0.0"
    assert settings.llm_provider in ("groq", "ollama", "openai")
    assert settings.search_provider in ("tavily", "duckduckgo", "brave")
    assert settings.embedding_provider == "ollama"
    assert settings.rag_chunk_size > 0
    assert settings.rag_top_k > 0


def test_settings_defaults_are_safe():
    from config.settings import settings
    assert settings.max_rows > 0
    assert settings.suggested_question_count > 0
    assert settings.rag_chunk_overlap < settings.rag_chunk_size


def test_exceptions_import():
    from tools.exceptions import (
        SearchProviderError,
        LLMProviderError,
        DataIngestionError,
        RAGIngestionError,
        ReportGenerationError,
    )
    assert SearchProviderError
    assert LLMProviderError
    assert DataIngestionError
    assert RAGIngestionError
    assert ReportGenerationError


def test_search_provider_error_has_retry_message():
    from tools.exceptions import SearchProviderError
    err = SearchProviderError(provider="tavily", detail="429 Too Many Requests")
    assert "tavily" in err.retry_message.lower()
    assert err.provider == "tavily"
    assert "429" in err.detail


def test_llm_provider_error_has_retry_message():
    from tools.exceptions import LLMProviderError
    err = LLMProviderError(provider="groq", detail="rate limit exceeded")
    assert "groq" in err.retry_message.lower()
    assert err.provider == "groq"


def test_project_structure_exists():
    root = Path(__file__).resolve().parent.parent
    required_dirs = [
        "config", "graph", "agents", "tools",
        "prompts", "rag", "output", "ui",
        "tests", "sample_data",
    ]
    required_files = [
        ".env.example",
        "requirements.txt",
        ".gitignore",
        "config/settings.py",
        "config/llm_factory.py",
        "config/embedding_factory.py",
        "tools/exceptions.py",
    ]
    for d in required_dirs:
        assert (root / d).is_dir(), f"Missing directory: {d}"
    for f in required_files:
        assert (root / f).is_file(), f"Missing file: {f}"