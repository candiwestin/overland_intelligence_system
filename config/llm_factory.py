"""
LLM Factory
===========
Resolves and instantiates LLM clients from the registry.

This file contains zero provider-specific logic. All provider configuration
lives in config/llm_registry.py. To add or modify an LLM provider, edit
the registry — this file never changes.
"""

import importlib

from config.settings import settings
from config.llm_registry import LLM_REGISTRY
from tools.exceptions import LLMProviderError


def get_llm(provider: str = None):
    """
    Returns the configured LLM client based on provider selection.

    Provider and all model names are read exclusively from .env via settings
    and resolved through the LLM registry. To switch providers or models,
    change .env only — no code changes needed.

    Args:
        provider: Runtime override. Must match a key in LLM_REGISTRY.
                  Defaults to LLM_PROVIDER in .env.

    Returns:
        A LangChain chat model instance ready for .invoke() calls.

    Raises:
        LLMProviderError: If the provider is unknown, a required setting is
                          missing from .env, or the client fails to initialize.
    """
    resolved_provider = provider or settings.llm_provider

    if not resolved_provider:
        raise LLMProviderError(
            provider="llm",
            detail="LLM_PROVIDER is not set in .env",
        )

    config = LLM_REGISTRY.get(resolved_provider)
    if not config:
        valid = ", ".join(LLM_REGISTRY.keys())
        raise LLMProviderError(
            provider=resolved_provider,
            detail=f"Unknown provider '{resolved_provider}'. Valid options: {valid}",
        )

    try:
        # Validate API key if required
        if config.api_key_setting:
            api_key = getattr(settings, config.api_key_setting, "")
            if not api_key:
                raise LLMProviderError(
                    provider=resolved_provider,
                    detail=f"{config.api_key_setting.upper()} is not set in .env",
                    retry_message=config.retry_message,
                )

        # Validate model name
        model = getattr(settings, config.model_setting, "")
        if not model:
            raise LLMProviderError(
                provider=resolved_provider,
                detail=f"{config.model_setting.upper()} is not set in .env",
                retry_message=config.retry_message,
            )

        # Build constructor kwargs
        kwargs = {"model": model}

        if config.api_key_setting:
            kwargs["api_key"] = getattr(settings, config.api_key_setting)

        for kwarg_key, settings_key in config.extra_settings.items():
            value = getattr(settings, settings_key, "")
            if value:
                kwargs[kwarg_key] = value

        # Import and instantiate
        module = importlib.import_module(config.module)
        cls    = getattr(module, config.class_name)
        return cls(**kwargs)

    except LLMProviderError:
        raise
    except Exception as e:
        raise LLMProviderError(
            provider=resolved_provider,
            detail=str(e),
            retry_message=config.retry_message,
        )


def get_available_llm_providers() -> list[dict]:
    """
    Returns all registered LLM providers for the /providers API endpoint.

    Returns:
        List of dicts with 'key' and 'label' for each registered provider.
    """
    return [
        {"key": key, "label": cfg.label}
        for key, cfg in LLM_REGISTRY.items()
    ]