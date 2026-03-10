import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from tools.exceptions import SearchProviderError


# -----------------------------------------------------------------------------
# Provider factory
# -----------------------------------------------------------------------------

def get_search_client(provider: str = None):
    """
    Returns the configured search client based on provider selection.

    Args:
        provider: Override the default from settings. Accepts 'tavily',
                  'duckduckgo', or 'brave'. Passed in from the Streamlit
                  sidebar at runtime.

    Returns:
        A search client instance with a callable .invoke(query) interface.

    Raises:
        SearchProviderError: If the provider is unknown or fails to initialize.
    """
    resolved_provider = provider or settings.search_provider

    try:
        if resolved_provider == "tavily":
            from langchain_community.tools.tavily_search import TavilySearchResults
            return TavilySearchResults(
                api_key=settings.tavily_api_key,
                max_results=5,
            )

        if resolved_provider == "duckduckgo":
            from langchain_community.tools import DuckDuckGoSearchRun
            return DuckDuckGoSearchRun()

        # Brave Search — built and ready, activate by:
        # 1. Setting SEARCH_PROVIDER=brave in .env or sidebar
        # 2. Uncommenting BRAVE_API_KEY in .env
        # 3. Uncommenting the block below
        # 4. Uncommenting brave-search in requirements.txt
        #
        # if resolved_provider == "brave":
        #     from langchain_community.tools import BraveSearch
        #     return BraveSearch.from_api_key(
        #         api_key=settings.brave_api_key,
        #         search_kwargs={"count": 5},
        #     )

        raise SearchProviderError(
            provider=resolved_provider,
            detail=f"Unknown provider '{resolved_provider}'. Valid options: tavily, duckduckgo",
        )

    except SearchProviderError:
        raise
    except Exception as e:
        raise SearchProviderError(provider=resolved_provider, detail=str(e))


# -----------------------------------------------------------------------------
# Search execution
# -----------------------------------------------------------------------------

def run_search(client, query: str) -> list[dict]:
    """
    Executes a search query using the provided client.

    Args:
        client: Search client from get_search_client().
        query: The search query string.

    Returns:
        List of result dicts. Each dict contains at minimum:
            - 'content' or 'snippet': the result text
            - 'url' or 'link': source URL where available

    Raises:
        SearchProviderError: On rate limit, quota exhaustion, or network failure.
    """
    try:
        raw = client.invoke(query)

        # Normalize output — different providers return different shapes
        return _normalize_results(raw, client)

    except SearchProviderError:
        raise
    except Exception as e:
        provider_name = _get_provider_name(client)
        raise SearchProviderError(provider=provider_name, detail=str(e))


def run_multi_search(client, queries: list[str]) -> list[dict]:
    """
    Executes multiple search queries and returns deduplicated results.

    Args:
        client: Search client from get_search_client().
        queries: List of query strings — typically 2 to 4 per agent run.

    Returns:
        Flat deduplicated list of result dicts.

    Raises:
        SearchProviderError: If any query fails.
    """
    all_results = []
    seen_urls = set()

    for query in queries:
        results = run_search(client, query)
        for result in results:
            url = result.get("url", result.get("link", ""))
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append(result)
            elif not url:
                all_results.append(result)

    return all_results


# -----------------------------------------------------------------------------
# Normalization helpers
# -----------------------------------------------------------------------------

def _normalize_results(raw, client) -> list[dict]:
    """
    Normalizes search results from different providers into a consistent shape.

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
    """Extracts a readable provider name from the client class name."""
    name = type(client).__name__.lower()
    if "tavily" in name:
        return "tavily"
    if "duckduckgo" in name:
        return "duckduckgo"
    if "brave" in name:
        return "brave"
    return name