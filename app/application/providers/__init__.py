"""Provedores de LLM (OpenAI, Ollama local)."""

from app.application.providers.ollama_provider import OllamaLLMProvider, OllamaProviderError
from app.application.providers.openai_provider import OpenAILLMProvider

# factory importa generation; generation importa ollama_provider — evitar ciclo no __init__.
# Use: from app.application.providers.factory import get_generation_strategy, get_llm_provider

__all__ = [
    "OllamaLLMProvider",
    "OllamaProviderError",
    "OpenAILLMProvider",
]
