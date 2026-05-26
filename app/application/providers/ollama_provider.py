"""Provedor de geração via Ollama local (sem OPENAI_API_KEY)."""

from __future__ import annotations

import logging
from functools import lru_cache
import time

import requests
from langchain_ollama import ChatOllama

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class OllamaProviderError(Exception):
    """Falha ao usar o Ollama (serviço indisponível, modelo ou rede)."""


def is_ollama_available(base_url: str | None = None, *, timeout: float = 3.0) -> bool:
    """Verifica se o servidor Ollama responde em `/api/tags`."""
    settings = get_settings()
    url = (base_url or settings.ollama_base_url).rstrip("/")
    try:
        response = requests.get(f"{url}/api/tags", timeout=timeout)
        return response.status_code == 200
    except requests.RequestException:
        return False


@lru_cache(maxsize=4)
def _build_chat_ollama(
    *,
    model: str,
    base_url: str,
    temperature: float,
    seed: int | None,
) -> ChatOllama:
    kwargs: dict = {
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
    }
    if seed is not None:
        kwargs["seed"] = seed
    return ChatOllama(**kwargs)


class OllamaLLMProvider:
    """Gera texto via ChatOllama apontando para instância local."""

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        temperature: float | None = None,
        seed: int | None = None,
    ) -> None:
        settings = get_settings()
        self._model = model if model is not None else settings.ollama_model
        self._base_url = (base_url if base_url is not None else settings.ollama_base_url).rstrip("/")
        self._temperature = (
            temperature if temperature is not None else settings.llm_temperature
        )
        self._seed = seed if seed is not None else settings.ollama_seed

    @property
    def model(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    def _ensure_available(self) -> None:
        if is_ollama_available(self._base_url):
            return
        raise OllamaProviderError(
            f"Ollama não está acessível em {self._base_url}. "
            "Inicie o serviço (ex.: `ollama serve` ou o app Ollama no Windows) "
            f"e confirme que o modelo `{self._model}` está instalado (`ollama pull {self._model}`)."
        )

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise OllamaProviderError("O prompt não pode ser vazio.")
        last_exc: Exception | None = None

        attempts = 3
        sleep_seconds = 5

        for attempt in range(1, attempts + 1):
            try:
                if not is_ollama_available(self._base_url):
                    logger.warning(
                        "Ollama healthcheck falhou (tentativa %s/%s) em %s; aguardando %ss",
                        attempt,
                        attempts,
                        self._base_url,
                        sleep_seconds,
                    )
                    time.sleep(sleep_seconds)
                    continue

                llm = _build_chat_ollama(
                    model=self._model,
                    base_url=self._base_url,
                    temperature=self._temperature,
                    seed=self._seed,
                )

                message = llm.invoke(prompt)
                text = getattr(message, "content", None) or str(message)
                return text.strip()
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "Falha ao gerar resposta com Ollama (tentativa %s/%s; modelo=%s): %s",
                    attempt,
                    attempts,
                    self._model,
                    exc,
                )
                if attempt < attempts:
                    time.sleep(sleep_seconds)

        raise OllamaProviderError(
            f"Falha ao gerar resposta com Ollama após {attempts} tentativas (modelo={self._model})."
        ) from last_exc
