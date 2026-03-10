from config.settings import settings
from tools.exceptions import LLMProviderError


def get_llm(provider: str = None, ollama_model: str = None):
    """
    Returns the configured LLM client based on provider selection.

    Args:
        provider: Override the default from settings. Accepts 'groq' or 'ollama'.
                  Passed in from the Streamlit sidebar at runtime.
        ollama_model: Specific Ollama model to use when provider is 'ollama'.
                      Defaults to settings.ollama_model_primary.

    Returns:
        A LangChain chat model instance ready for .invoke() calls.

    Raises:
        LLMProviderError: If the provider is unknown or the client fails to init.
    """
    resolved_provider = provider or settings.llm_provider

    try:
        if resolved_provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=settings.groq_model,
                api_key=settings.groq_api_key,
            )

        if resolved_provider == "ollama":
            from langchain_ollama import ChatOllama
            model = ollama_model or settings.ollama_model_primary
            return ChatOllama(
                model=model,
                base_url=settings.ollama_base_url,
            )

        # OpenAI — built and ready, activate by:
        # 1. Setting LLM_PROVIDER=openai in .env
        # 2. Uncommenting OPENAI_API_KEY in .env
        # 3. Uncommenting the block below
        # 4. Uncommenting langchain-openai in requirements.txt
        #
        # if resolved_provider == "openai":
        #     from langchain_openai import ChatOpenAI
        #     return ChatOpenAI(
        #         model=settings.openai_model,
        #         api_key=settings.openai_api_key,
        #     )

        raise LLMProviderError(
            provider=resolved_provider,
            detail=f"Unknown provider '{resolved_provider}'. Valid options: groq, ollama",
        )

    except LLMProviderError:
        raise
    except Exception as e:
        raise LLMProviderError(provider=resolved_provider, detail=str(e))