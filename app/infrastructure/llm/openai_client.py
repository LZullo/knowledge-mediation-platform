"""Cliente OpenAI para geração de texto (camada isolada; sem regras de negócio)."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from openai import OpenAI
from openai import APIError, APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError, RateLimitError

from app.core.config import get_settings


class OpenAIClientError(Exception):
    """Falha ao chamar a API OpenAI (configuração, rede ou resposta)."""


@dataclass(frozen=True)
class LLMGenerationResult:
    """Resultado de uma geração de texto."""

    text: str
    model: str
    tokens_used: int | None
    """Total de tokens quando a API informa `usage`; caso contrário `None`."""


@dataclass(frozen=True)
class ChatCompletionParams:
    """Parâmetros opcionais da API chat.completions (None = omitir / default da API)."""

    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None


@lru_cache(maxsize=1)
def _build_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key.strip():
        raise OpenAIClientError(
            "OPENAI_API_KEY não configurada. Defina a variável de ambiente ou o arquivo .env."
        )
    kwargs: dict = {"api_key": settings.openai_api_key}
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    return OpenAI(**kwargs)


def _execute_chat_completion(
    *,
    model: str,
    messages: list[dict[str, str]],
    params: ChatCompletionParams | None,
) -> LLMGenerationResult:
    if not messages or not (messages[0].get("content") or "").strip():
        raise OpenAIClientError("O prompt não pode ser vazio.")

    body: dict = {"model": model, "messages": messages}
    p = params or ChatCompletionParams()
    if p.temperature is not None:
        body["temperature"] = p.temperature
    if p.max_tokens is not None:
        body["max_tokens"] = p.max_tokens
    if p.top_p is not None:
        body["top_p"] = p.top_p
    if p.frequency_penalty is not None:
        body["frequency_penalty"] = p.frequency_penalty
    if p.presence_penalty is not None:
        body["presence_penalty"] = p.presence_penalty

    try:
        client = _build_client()
        response = client.chat.completions.create(**body)
    except AuthenticationError as e:
        raise OpenAIClientError("Autenticação OpenAI falhou (chave inválida ou revogada).") from e
    except RateLimitError as e:
        raise OpenAIClientError("Limite de taxa da OpenAI atingido; tente novamente mais tarde.") from e
    except APITimeoutError as e:
        raise OpenAIClientError("Tempo esgotado ao aguardar a OpenAI.") from e
    except APIConnectionError as e:
        raise OpenAIClientError("Não foi possível conectar à API OpenAI.") from e
    except BadRequestError as e:
        raise OpenAIClientError(
            f"Requisição rejeitada pela OpenAI (modelo ou parâmetros): {e}"
        ) from e
    except APIError as e:
        raise OpenAIClientError(f"Erro da API OpenAI: {e}") from e
    except Exception as e:
        raise OpenAIClientError(f"Falha ao chamar a OpenAI: {e!s}") from e

    choice = response.choices[0].message
    text = (choice.content or "").strip()

    tokens_used: int | None = None
    if response.usage is not None:
        tokens_used = response.usage.total_tokens

    return LLMGenerationResult(
        text=text,
        model=model,
        tokens_used=tokens_used,
    )


def generate_from_prompt(
    prompt: str,
    *,
    params: ChatCompletionParams | None = None,
) -> LLMGenerationResult:
    """
    Envia um único prompt como mensagem de usuário e devolve o texto gerado.

    `model` vem de `OPENAI_MODEL`, salvo override em `params.model`.
    """
    settings = get_settings()
    p = params or ChatCompletionParams()
    model = p.model if p.model else settings.openai_model
    return _execute_chat_completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        params=p,
    )
