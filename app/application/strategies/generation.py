"""Estratégia de geração (parâmetros da chamada ao LLM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.application.providers.ollama_provider import OllamaLLMProvider, OllamaProviderError
from app.core.config import get_settings
from app.infrastructure.llm import ChatCompletionParams, LLMGenerationResult, generate_from_prompt


@runtime_checkable
class GenerationStrategy(Protocol):
    """Define como executar a geração dado o prompt (modelo, temperatura, etc.)."""

    def generate(self, prompt: str) -> LLMGenerationResult:
        ...


@dataclass
class OpenAIGenerationStrategy:
    """
    Usa o cliente OpenAI com parâmetros fixos por instância (intercambiável com outras implementações).

    Experimentos variam `params` ou substituem a classe inteira.
    """

    params: ChatCompletionParams = field(
        default_factory=lambda: ChatCompletionParams(
            temperature=get_settings().llm_temperature,
        )
    )

    def generate(self, prompt: str) -> LLMGenerationResult:
        return generate_from_prompt(prompt, params=self.params)


@dataclass
class OllamaGenerationStrategy:
    """Usa Ollama local; intercambiável com `OpenAIGenerationStrategy`."""

    provider: OllamaLLMProvider | None = None

    def generate(self, prompt: str) -> LLMGenerationResult:
        settings = get_settings()
        prov = self.provider or OllamaLLMProvider()
        try:
            text = prov.generate(prompt)
        except OllamaProviderError:
            raise
        except Exception as exc:
            raise OllamaProviderError(f"Falha na geração Ollama: {exc!s}") from exc
        return LLMGenerationResult(
            text=text,
            model=prov.model,
            tokens_used=None,
        )
