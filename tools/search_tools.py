"""
Search Tools
============
Executes search queries and normalizes results across providers.

This file handles search execution only — client creation lives in
config/search_factory.py. Provider configuration lives in
config/search_registry.py.
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.search_registry import SEARCH_REGISTRY
from tools.exceptions import SearchProviderError


# -----------------------------------------------------------------------------
# Search execution
# -----------------------------------------------------------------------------

def run_search(client, query: str) -> list[dict]:
    """
    Executes a search query using the provided client.

    If the primary provider has a fallback defined in the registry and fails,
    automatically retries with the fallback provider before raising an error.

    Args:
        client: Search client from config/search_factory.get_search_client().
        query:  The search query string.

    Returns:
        List of result dicts with keys: title, content, url.

    Raises:
        SearchProviderError: If the provider (and any fallback) fails.
    """
    try:
        raw = client.invoke(query)
        return _normalize_results(raw)

    except SearchProviderError:
        raise
    except Exception as e:
        provider_name = _get_provider_name(client)
        config        = SEARCH_REGISTRY.get(provider_name)

        # Attempt automatic fallback if the registry defines one
        if config and config.fallback:
            fallback_key    = config.fallback
            fallback_config = SEARCH_REGISTRY.get(fallback_key)

            warnings.warn(
                f"{config.retry_message} Falling back to {fallback_key}.",
                stacklevel=2,
            )

            try:
                import importlib, os
                if fallback_config.env_inject:
                    from config.settings import settings
                    for env_key, settings_key in fallback_config.env_inject.items():
                        value = getattr(settings, settings_key, "")
                        if value:
                            os.environ[env_key] = value

                module   = importlib.import_module(fallback_config.module)
                cls      = getattr(module, fallback_config.class_name)
                fallback = cls(**fallback_config.kwargs)
                raw      = fallback.invoke(query)
                return _normalize_results(raw)

            except Exception as fallback_error:
                raise SearchProviderError(
                    provider=fallback_key,
                    detail=(
                        f"Primary provider '{provider_name}' failed: {e}. "
                        f"Fallback '{fallback_key}' also failed: {fallback_error}."
                    ),
                    retry_message=fallback_config.retry_message if fallback_config else "",
                )

        raise SearchProviderError(
            provider=provider_name,
            detail=str(e),
            retry_message=config.retry_message if config else "",
        )


def run_multi_search(client, queries: list[str]) -> list[dict]:
    """
    Executes multiple search queries and returns deduplicated results.

    Args:
        client:  Search client from config/search_factory.get_search_client().
        queries: List of query strings — typically 2 to 4 per agent run.

    Returns:
        Flat deduplicated list of result dicts.

    Raises:
        SearchProviderError: If any query fails.
    """
    all_results = []
    seen_urls   = set()

    for query in queries:
        results = run_search(client, query)
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(result)
            elif not url:
                all_results.append(result)

    return all_results


# -----------------------------------------------------------------------------
# Normalization helpers
# -----------------------------------------------------------------------------

def _normalize_results(raw) -> list[dict]:
    """
    Normalizes search results from any provider into a consistent shape.

    Output format per result:
        {
            "title":   str,
            "content": str,
            "url":     str,
        }
    """
    if isinstance(raw, str):
        # DuckDuckGoSearchRun returns a plain string
        return [{"title": "", "content": raw, "url": ""}]

    if isinstance(raw, list):
        normalized = []
        for item in raw:
            if isinstance(item, dict):
                normalized.append({
                    "title":   item.get("title", ""),
                    "content": item.get("content", item.get("snippet", "")),
                    "url":     item.get("url", item.get("link", "")),
                })
            elif isinstance(item, str):
                normalized.append({"title": "", "content": item, "url": ""})
        return normalized

    return [{"title": "", "content": str(raw), "url": ""}]


def _get_provider_name(client) -> str:
    """Extracts a registry-compatible provider name from the client class name."""
    name = type(client).__name__.lower()
    if "tavily"     in name: return "tavily"
    if "duckduckgo" in name: return "duckduckgo"
    if "brave"      in name: return "brave"
    return name