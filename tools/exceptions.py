"""
Custom Exceptions
=================
All retry messages are sourced from the provider registries, not hardcoded here.
This file contains pure error-handling logic only.

Registry files:
    config/llm_registry.py      — LLM retry messages
    config/search_registry.py   — Search retry messages
    config/embedding_registry.py — Embedding retry messages
"""


class SearchProviderError(Exception):
    """
    Raised when a search provider fails — rate limit, quota exhaustion,
    invalid API key, or network failure.

    The retry_message is sourced from config/search_registry.py and passed
    in at raise time, giving the user actionable recovery instructions.
    """

    def __init__(self, provider: str, detail: str, retry_message: str = ""):
        self.provider      = provider
        self.detail        = detail
        self.retry_message = retry_message or (
            f"Search provider '{provider}' failed. "
            "Switch providers in the dashboard or check your .env configuration."
        )
        super().__init__(f"Search provider '{provider}' failed: {detail}")


class LLMProviderError(Exception):
    """
    Raised when an LLM provider fails — rate limit, daily quota exhaustion,
    invalid API key, or Ollama not running locally.

    The retry_message is sourced from config/llm_registry.py and passed
    in at raise time, giving the user actionable recovery instructions.
    """

    def __init__(self, provider: str, detail: str, retry_message: str = ""):
        self.provider      = provider
        self.detail        = detail
        self.retry_message = retry_message or (
            f"LLM provider '{provider}' failed. "
            "Switch providers in the dashboard or check your .env configuration."
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
        self.detail   = detail
        super().__init__(f"RAG ingestion failed for '{filename}': {detail}")


class ReportGenerationError(Exception):
    """
    Raised when the report agent or PDF builder fails.
    Caught in agents/report_agent.py and output/pdf_builder.py.
    """

    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(f"Report generation failed: {detail}")