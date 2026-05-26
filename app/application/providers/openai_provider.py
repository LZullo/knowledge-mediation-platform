"""Provedor de geração via OpenAI (wrapper fino sobre o cliente existente)."""

from __future__ import annotations

from app.infrastructure.llm import OpenAIClientError, generate_from_prompt


class OpenAILLMProvider:
    """Expõe `generate(prompt) -> str` alinhado ao contrato dos demais provedores."""

    def generate(self, prompt: str) -> str:
        try:
            result = generate_from_prompt(prompt)
        except OpenAIClientError:
            raise
        except Exception as exc:
            raise OpenAIClientError(f"Falha ao gerar resposta com OpenAI: {exc!s}") from exc
        return result.text
