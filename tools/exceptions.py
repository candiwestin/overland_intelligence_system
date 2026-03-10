class SearchProviderError(Exception):
    """
    Raised when a search provider fails — rate limit, quota exhaustion,
    invalid API key, or network failure.

    Caught in tools/search_tools.py.
    Surfaced to the user via the Streamlit UI with actionable recovery instructions.
    """

    RETRY_MESSAGES = {
        "tavily": (
            "Tavily quota may be exhausted (1,000 searches/mo free tier). "
            "Switch to DuckDuckGo in the sidebar and re-run, "
            "or wait for your Tavily quota to reset on the 1st of the month."
        ),
        "duckduckgo": (
            "DuckDuckGo rate limit hit. Wait 60 seconds and re-run, "
            "or switch to Tavily in the sidebar."
        ),
        "brave": (
            "Brave Search API error. Check your BRAVE_API_KEY in .env "
            "or switch to Tavily in the sidebar."
        ),
    }

    def __init__(self, provider: str, detail: str):
        self.provider = provider
        self.detail = detail
        self.retry_message = self.RETRY_MESSAGES.get(
            provider.lower(),
            f"Search provider '{provider}' failed. Switch providers in the sidebar.",
        )
        super().__init__(f"Search provider '{provider}' failed: {detail}")


class LLMProviderError(Exception):
    """
    Raised when an LLM provider fails — rate limit, daily quota exhaustion,
    invalid API key, or Ollama not running locally.

    Caught in agents/*.py.
    Surfaced to the user via the Streamlit UI with actionable recovery instructions.
    """

    RETRY_MESSAGES = {
        "groq": (
            "Groq daily limit may be reached (14,400 requests/day free tier). "
            "Switch to Ollama in the sidebar and re-run, "
            "or wait for your Groq quota to reset in 24 hours."
        ),
        "ollama": (
            "Ollama is not responding. Make sure Ollama is running locally: "
            "open a terminal and run 'ollama serve', then re-run the analysis."
        ),
        "openai": (
            "OpenAI API error. Check your OPENAI_API_KEY in .env "
            "or switch to Groq/Ollama in the sidebar."
        ),
    }

    def __init__(self, provider: str, detail: str):
        self.provider = provider
        self.detail = detail
        self.retry_message = self.RETRY_MESSAGES.get(
            provider.lower(),
            f"LLM provider '{provider}' failed. Switch providers in the sidebar.",
        )
        super().__init__(f"LLM provider '{provider}' failed: {detail}")


class DataIngestionError(Exception):
    """
    Raised when uploaded data cannot be parsed or profiled.
    Caught in tools/data_tools.py.
    """

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(f"Data ingestion failed: {detail}")


class RAGIngestionError(Exception):
    """
    Raised when a supporting document cannot be embedded.
    Caught in rag/ingest.py.
    """

    def __init__(self, filename: str, detail: str):
        self.filename = filename
        self.detail = detail
        super().__init__(f"RAG ingestion failed for '{filename}': {detail}")


class ReportGenerationError(Exception):
    """
    Raised when the report agent or PDF builder fails.
    Caught in agents/report_agent.py and output/pdf_builder.py.
    """

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(f"Report generation failed: {detail}")