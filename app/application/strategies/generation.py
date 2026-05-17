"""Estratégia de geração (parâmetros da chamada ao LLM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

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

    params: ChatCompletionParams = field(default_factory=ChatCompletionParams)

    def generate(self, prompt: str) -> LLMGenerationResult:
        return generate_from_prompt(prompt, params=self.params)
