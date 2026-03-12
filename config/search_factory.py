"""
Search Factory
==============
Resolves and instantiates search clients from the registry.

This file contains zero provider-specific logic. All provider configuration
lives in config/search_registry.py. To add or modify a search provider, edit
the registry — this file never changes.
"""

import os
import importlib

from config.settings import settings
from config.search_registry import SEARCH_REGISTRY
from tools.exceptions import SearchProviderError


def get_search_client(provider: str = None):
    """
    Returns the configured search client based on provider selection.

    Provider is read exclusively from .env via settings and resolved through
    the search registry. To switch providers, change SEARCH_PROVIDER in .env
    only — no code changes needed.

    Args:
        provider: Runtime override. Must match a key in SEARCH_REGISTRY.
                  Defaults to SEARCH_PROVIDER in .env.

    Returns:
        A search client instance with a callable .invoke(query) interface.

    Raises:
        SearchProviderError: If the provider is unknown, a required key is
                             missing from .env, or the client fails to initialize.
    """
    resolved_provider = provider or settings.search_provider

    if not resolved_provider:
        raise SearchProviderError(
            provider="search",
            detail="SEARCH_PROVIDER is not set in .env",
        )

    config = SEARCH_REGISTRY.get(resolved_provider)
    if not config:
        valid = ", ".join(SEARCH_REGISTRY.keys())
        raise SearchProviderError(
            provider=resolved_provider,
            detail=f"Unknown provider '{resolved_provider}'. Valid options: {valid}",
        )

    try:
        # Validate API key if required
        if config.api_key_setting:
            api_key = getattr(settings, config.api_key_setting, "")
            if not api_key:
                raise SearchProviderError(
                    provider=resolved_provider,
                    detail=f"{config.api_key_setting.upper()} is not set in .env",
                    retry_message=config.retry_message,
                )

        # Inject environment variables for providers that read os.environ directly
        for env_key, settings_key in config.env_inject.items():
            value = getattr(settings, settings_key, "")
            if value:
                os.environ[env_key] = value

        # Import the provider class
        module = importlib.import_module(config.module)
        cls    = getattr(module, config.class_name)

        # Instantiate — use factory_method if specified (e.g. BraveSearch.from_api_key)
        if config.factory_method:
            api_key = getattr(settings, config.api_key_setting)
            return getattr(cls, config.factory_method)(
                api_key=api_key,
                **config.kwargs,
            )

        return cls(**config.kwargs)

    except SearchProviderError:
        raise
    except Exception as e:
        raise SearchProviderError(
            provider=resolved_provider,
            detail=str(e),
            retry_message=config.retry_message,
        )


def get_available_search_providers() -> list[dict]:
    """
    Returns all registered search providers for the /providers API endpoint.

    Returns:
        List of dicts with 'key' and 'label' for each registered provider.
    """
    return [
        {"key": key, "label": cfg.label}
        for key, cfg in SEARCH_REGISTRY.items()
    ]