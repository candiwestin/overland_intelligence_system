from config.settings import settings
from tools.exceptions import LLMProviderError


def get_embeddings(provider: str = None):
    """
    Returns the configured embedding client.

    Args:
        provider: Override the default from settings. Currently supports 'ollama'.

    Returns:
        A LangChain embeddings instance ready for .embed_documents() calls.

    Raises:
        LLMProviderError: If the provider is unknown or fails to initialize.
    """
    resolved_provider = provider or settings.embedding_provider

    try:
        if resolved_provider == "ollama":
            from langchain_ollama import OllamaEmbeddings
            return OllamaEmbeddings(
                model=settings.embedding_model,
                base_url=settings.ollama_base_url,
            )

        # OpenAI embeddings — built and ready, activate by:
        # 1. Setting EMBEDDING_PROVIDER=openai in .env
        # 2. Uncommenting OPENAI_API_KEY in .env
        # 3. Uncommenting the block below
        #
        # if resolved_provider == "openai":
        #     from langchain_openai import OpenAIEmbeddings
        #     return OpenAIEmbeddings(
        #         model="text-embedding-3-small",
        #         api_key=settings.openai_api_key,
        #     )

        raise LLMProviderError(
            provider=resolved_provider,
            detail=f"Unknown embedding provider '{resolved_provider}'. Valid options: ollama",
        )

    except LLMProviderError:
        raise
    except Exception as e:
        raise LLMProviderError(provider=resolved_provider, detail=str(e))