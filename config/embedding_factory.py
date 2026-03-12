"""
Embedding Factory
=================
Resolves and instantiates embedding clients from the registry.

This file contains zero provider-specific logic. All provider configuration
lives in config/embedding_registry.py. To add or modify an embedding provider,
edit the registry — this file never changes.
"""

import importlib

from config.settings import settings
from config.embedding_registry import EMBEDDING_REGISTRY
from tools.exceptions import LLMProviderError


def get_embeddings(provider: str = None):
    """
    Returns the configured embedding client.

    Provider and model are read exclusively from .env via settings and
    resolved through the embedding registry. To switch providers, change
    EMBEDDING_PROVIDER in .env only — no code changes needed.

    Args:
        provider: Runtime override. Must match a key in EMBEDDING_REGISTRY.
                  Defaults to EMBEDDING_PROVIDER in .env.

    Returns:
        A LangChain embeddings instance ready for .embed_documents() calls.

    Raises:
        LLMProviderError: If the provider is unknown, a required setting is
                          missing from .env, or the client fails to initialize.
    """
    resolved_provider = provider or settings.embedding_provider

    if not resolved_provider:
        raise LLMProviderError(
            provider="embeddings",
            detail="EMBEDDING_PROVIDER is not set in .env",
        )

    config = EMBEDDING_REGISTRY.get(resolved_provider)
    if not config:
        valid = ", ".join(EMBEDDING_REGISTRY.keys())
        raise LLMProviderError(
            provider=resolved_provider,
            detail=f"Unknown embedding provider '{resolved_provider}'. Valid options: {valid}",
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