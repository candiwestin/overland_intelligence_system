"""
LLM Provider Registry
=====================
This is the ONLY file that changes when a new LLM provider is added.

To add a new provider:
    1. Add an LLMProviderConfig entry to LLM_REGISTRY below
    2. Add the required keys to .env
    3. Nothing else changes — factory, exceptions, and UI update automatically

Registry keys must match the values used in .env LLM_PROVIDER and the
runtime provider selector in the dashboard.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class LLMProviderConfig:
    """
    Configuration for a single LLM provider.

    Attributes:
        label           Human-readable name shown in the dashboard dropdown
        module          Python import path for the LangChain chat class
        class_name      Class to instantiate from the module
        api_key_setting settings.py attribute that holds the API key (None if no key needed)
        model_setting   settings.py attribute that holds the model name
        extra_settings  Additional settings attributes mapped to constructor kwargs
        env_inject      os.environ keys to inject from settings before instantiation
                        (for providers that read the environment directly)
        retry_message   Shown to the user when this provider fails — actionable guidance
    """
    label:           str
    module:          str
    class_name:      str
    model_setting:   str
    api_key_setting: str | None          = None
    extra_settings:  dict[str, str]      = field(default_factory=dict)
    env_inject:      dict[str, str]      = field(default_factory=dict)
    retry_message:   str                 = ""


# -----------------------------------------------------------------------------
# Registry — add new providers here only
# -----------------------------------------------------------------------------

LLM_REGISTRY: dict[str, LLMProviderConfig] = {

    "groq": LLMProviderConfig(
        label           = "Groq — llama-3.3-70b",
        module          = "langchain_groq",
        class_name      = "ChatGroq",
        api_key_setting = "groq_api_key",
        model_setting   = "groq_model",
        retry_message   = (
            "Groq daily limit may be reached (14,400 requests/day free tier). "
            "Switch to Ollama in the dashboard and re-run, "
            "or wait for your Groq quota to reset in 24 hours."
        ),
    ),

    "ollama_primary": LLMProviderConfig(
        label           = "Ollama — llama3.2",
        module          = "langchain_ollama",
        class_name      = "ChatOllama",
        api_key_setting = None,
        model_setting   = "ollama_model_primary",
        extra_settings  = {"base_url": "ollama_base_url"},
        retry_message   = (
            "Ollama is not responding. Make sure Ollama is running locally: "
            "open a terminal and run 'ollama serve', then re-run the analysis."
        ),
    ),

    "ollama_secondary": LLMProviderConfig(
        label           = "Ollama — mistral",
        module          = "langchain_ollama",
        class_name      = "ChatOllama",
        api_key_setting = None,
        model_setting   = "ollama_model_secondary",
        extra_settings  = {"base_url": "ollama_base_url"},
        retry_message   = (
            "Ollama is not responding. Make sure Ollama is running locally: "
            "open a terminal and run 'ollama serve', then re-run the analysis."
        ),
    ),

    # OpenAI — uncomment OPENAI block in .env to activate
    "openai_primary": LLMProviderConfig(
        label           = "OpenAI — gpt-4o",
        module          = "langchain_openai",
        class_name      = "ChatOpenAI",
        api_key_setting = "openai_api_key",
        model_setting   = "openai_model_primary",
        extra_settings  = {"base_url": "openai_base_url"},
        retry_message   = (
            "OpenAI API error. Verify OPENAI_API_KEY and OPENAI_MODEL_PRIMARY "
            "are set in .env, or switch to Groq/Ollama in the dashboard."
        ),
    ),

    "openai_secondary": LLMProviderConfig(
        label           = "OpenAI — gpt-4o-mini",
        module          = "langchain_openai",
        class_name      = "ChatOpenAI",
        api_key_setting = "openai_api_key",
        model_setting   = "openai_model_secondary",
        extra_settings  = {"base_url": "openai_base_url"},
        retry_message   = (
            "OpenAI API error. Verify OPENAI_API_KEY and OPENAI_MODEL_SECONDARY "
            "are set in .env, or switch to Groq/Ollama in the dashboard."
        ),
    ),
}