"""Seleção do provedor de LLM conforme `LLM_PROVIDER`."""

from __future__ import annotations

from app.application.providers.ollama_provider import OllamaLLMProvider
from app.application.providers.openai_provider import OpenAILLMProvider
from app.application.strategies.generation import (
    GenerationStrategy,
    OllamaGenerationStrategy,
    OpenAIGenerationStrategy,
)
from app.core.config import get_settings

_SUPPORTED = frozenset({"openai", "ollama"})


def get_llm_provider() -> OpenAILLMProvider | OllamaLLMProvider:
    provider = get_settings().llm_provider.strip().lower()
    if provider == "ollama":
        return OllamaLLMProvider()
    if provider == "openai":
        return OpenAILLMProvider()
    raise ValueError(
        f"LLM_PROVIDER inválido: {provider!r}. Valores suportados: {', '.join(sorted(_SUPPORTED))}."
    )


def get_generation_strategy() -> GenerationStrategy:
    provider = get_settings().llm_provider.strip().lower()
    if provider == "ollama":
        return OllamaGenerationStrategy()
    if provider == "openai":
        return OpenAIGenerationStrategy()
    raise ValueError(
        f"LLM_PROVIDER inválido: {provider!r}. Valores suportados: {', '.join(sorted(_SUPPORTED))}."
    )
