"""
Phase 5 validation — search_tools tested with mocks, no API calls required.
Run with: pytest tests/test_search_tools.py -v
"""
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# -----------------------------------------------------------------------------
# Provider factory tests
# -----------------------------------------------------------------------------

def test_get_search_client_duckduckgo():
    from tools.search_tools import get_search_client
    with patch("langchain_community.tools.DuckDuckGoSearchRun") as mock:
        mock.return_value = MagicMock()
        client = get_search_client("duckduckgo")
        assert client is not None


def test_get_search_client_unknown_raises():
    from tools.search_tools import get_search_client
    from tools.exceptions import SearchProviderError
    with pytest.raises(SearchProviderError) as exc_info:
        get_search_client("nonexistent_provider")
    assert exc_info.value.provider == "nonexistent_provider"


def test_search_provider_error_has_retry_message():
    from tools.exceptions import SearchProviderError
    err = SearchProviderError(provider="tavily", detail="429")
    assert len(err.retry_message) > 0
    assert "tavily" in err.retry_message.lower()


# -----------------------------------------------------------------------------
# run_search normalization tests
# -----------------------------------------------------------------------------

def test_run_search_with_list_results():
    from tools.search_tools import run_search
    mock_client = MagicMock()
    mock_client.invoke.return_value = [
        {"title": "Test", "content": "Some content", "url": "https://example.com"},
    ]
    results = run_search(mock_client, "overlanding market trends")
    assert len(results) == 1
    assert results[0]["content"] == "Some content"
    assert results[0]["url"] == "https://example.com"


def test_run_search_with_string_result():
    from tools.search_tools import run_search
    mock_client = MagicMock()
    mock_client.invoke.return_value = "DuckDuckGo plain text result"
    results = run_search(mock_client, "Baja 1000 2024")
    assert len(results) == 1
    assert results[0]["content"] == "DuckDuckGo plain text result"


def test_run_search_raises_on_failure():
    from tools.search_tools import run_search
    from tools.exceptions import SearchProviderError
    mock_client = MagicMock()
    mock_client.invoke.side_effect = Exception("Rate limit exceeded")
    with pytest.raises(SearchProviderError):
        run_search(mock_client, "test query")


# -----------------------------------------------------------------------------
# run_multi_search deduplication tests
# -----------------------------------------------------------------------------

def test_run_multi_search_deduplicates():
    from tools.search_tools import run_multi_search
    mock_client = MagicMock()
    mock_client.invoke.return_value = [
        {"title": "Same", "content": "Content", "url": "https://same.com"},
    ]
    results = run_multi_search(mock_client, ["query one", "query two"])
    urls = [r["url"] for r in results if r["url"]]
    assert len(urls) == len(set(urls))


def test_run_multi_search_combines_results():
    from tools.search_tools import run_multi_search
    mock_client = MagicMock()
    mock_client.invoke.side_effect = [
        [{"title": "A", "content": "Content A", "url": "https://a.com"}],
        [{"title": "B", "content": "Content B", "url": "https://b.com"}],
    ]
    results = run_multi_search(mock_client, ["query one", "query two"])
    assert len(results) == 2


# -----------------------------------------------------------------------------
# Normalization edge cases
# -----------------------------------------------------------------------------

def test_normalize_handles_snippet_key():
    from tools.search_tools import _normalize_results
    mock_client = MagicMock()
    raw = [{"title": "T", "snippet": "Snippet content", "link": "https://x.com"}]
    results = _normalize_results(raw, mock_client)
    assert results[0]["content"] == "Snippet content"
    assert results[0]["url"] == "https://x.com"


def test_normalize_handles_empty_list():
    from tools.search_tools import _normalize_results
    mock_client = MagicMock()
    results = _normalize_results([], mock_client)
    assert results == []