"""
Embedding Provider Registry
============================
This is the ONLY file that changes when a new embedding provider is added.

To add a new provider:
    1. Add an EmbeddingProviderConfig entry to EMBEDDING_REGISTRY below
    2. Add the required keys to .env
    3. Nothing else changes — factory, exceptions, and UI update automatically

Registry keys must match the values used in .env EMBEDDING_PROVIDER.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EmbeddingProviderConfig:
    """
    Configuration for a single embedding provider.

    Attributes:
        label            Human-readable name for logging and error messages
        module           Python import path for the LangChain embeddings class
        class_name       Class to instantiate from the module
        api_key_setting  settings.py attribute that holds the API key (None if no key needed)
        model_setting    settings.py attribute that holds the model name
        extra_settings   Additional settings attributes mapped to constructor kwargs
        retry_message    Shown to the user when this provider fails — actionable guidance
    """
    label:           str
    module:          str
    class_name:      str
    model_setting:   str
    api_key_setting: str | None      = None
    extra_settings:  dict[str, str]  = field(default_factory=dict)
    retry_message:   str             = ""


# -----------------------------------------------------------------------------
# Registry — add new providers here only
# -----------------------------------------------------------------------------

EMBEDDING_REGISTRY: dict[str, EmbeddingProviderConfig] = {

    "ollama": EmbeddingProviderConfig(
        label           = "Ollama — nomic-embed-text",
        module          = "langchain_ollama",
        class_name      = "OllamaEmbeddings",
        api_key_setting = None,
        model_setting   = "embedding_model",
        extra_settings  = {"base_url": "ollama_base_url"},
        retry_message   = (
            "Ollama embeddings are not responding. Make sure Ollama is running locally: "
            "open a terminal and run 'ollama serve', then re-run the analysis."
        ),
    ),

    # OpenAI embeddings — set EMBEDDING_PROVIDER=openai in .env to activate
    "openai": EmbeddingProviderConfig(
        label           = "OpenAI — text-embedding-3-small",
        module          = "langchain_openai",
        class_name      = "OpenAIEmbeddings",
        api_key_setting = "openai_api_key",
        model_setting   = "embedding_model",
        retry_message   = (
            "OpenAI embeddings API error. Verify OPENAI_API_KEY and EMBEDDING_MODEL "
            "are set in .env, or switch EMBEDDING_PROVIDER=ollama in .env."
        ),
    ),
}