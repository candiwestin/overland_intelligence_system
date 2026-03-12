"""
Search Provider Registry
========================
This is the ONLY file that changes when a new search provider is added.

To add a new provider:
    1. Add a SearchProviderConfig entry to SEARCH_REGISTRY below
    2. Add the required keys to .env
    3. Nothing else changes — factory, exceptions, and UI update automatically

Registry keys must match the values used in .env SEARCH_PROVIDER and the
runtime provider selector in the dashboard.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchProviderConfig:
    """
    Configuration for a single search provider.

    Attributes:
        label            Human-readable name shown in the dashboard dropdown
        module           Python import path for the LangChain search class
        class_name       Class to instantiate from the module
        factory_method   Alternative class method to use instead of __init__ (e.g. from_api_key)
        api_key_setting  settings.py attribute that holds the API key (None if no key needed)
        env_inject       os.environ keys to inject from settings before instantiation
                         (for providers that read the environment directly)
        kwargs           Static constructor kwargs (e.g. max_results, search_kwargs)
        fallback         Provider key to fall back to if this provider fails
        retry_message    Shown to the user when this provider fails — actionable guidance
    """
    label:           str
    module:          str
    class_name:      str
    api_key_setting: str | None          = None
    factory_method:  str | None          = None
    env_inject:      dict[str, str]      = field(default_factory=dict)
    kwargs:          dict                = field(default_factory=dict)
    fallback:        str | None          = None
    retry_message:   str                 = ""


# -----------------------------------------------------------------------------
# Registry — add new providers here only
# -----------------------------------------------------------------------------

SEARCH_REGISTRY: dict[str, SearchProviderConfig] = {

    "tavily": SearchProviderConfig(
        label           = "Tavily",
        module          = "langchain_community.tools.tavily_search",
        class_name      = "TavilySearchResults",
        api_key_setting = "tavily_api_key",
        env_inject      = {"TAVILY_API_KEY": "tavily_api_key"},
        kwargs          = {"max_results": 5},
        fallback        = "duckduckgo",
        retry_message   = (
            "Tavily quota may be exhausted (1,000 searches/mo free tier). "
            "Automatically falling back to DuckDuckGo. "
            "To switch permanently, set SEARCH_PROVIDER=duckduckgo in .env "
            "or select DuckDuckGo (fallback) in the dashboard. "
            "Tavily quota resets on the 1st of each month."
        ),
    ),

    "duckduckgo": SearchProviderConfig(
        label           = "DuckDuckGo (fallback)",
        module          = "langchain_community.tools",
        class_name      = "DuckDuckGoSearchRun",
        api_key_setting = None,
        retry_message   = (
            "DuckDuckGo rate limit hit. Wait 60 seconds and re-run, "
            "or switch to Tavily in the dashboard."
        ),
    ),

    # Brave Search — uncomment BRAVE_API_KEY in .env to activate
    "brave": SearchProviderConfig(
        label           = "Brave Search",
        module          = "langchain_community.tools",
        class_name      = "BraveSearch",
        factory_method  = "from_api_key",
        api_key_setting = "brave_api_key",
        kwargs          = {"search_kwargs": {"count": 5}},
        retry_message   = (
            "Brave Search API error. Verify BRAVE_API_KEY is set in .env, "
            "or switch to Tavily in the dashboard."
        ),
    ),
}