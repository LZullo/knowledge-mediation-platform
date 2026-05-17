"""Benchmark SQuAD-pt contra o endpoint /ask."""

from __future__ import annotations

import difflib
from typing import Any

import requests

from app.dados.squad_pt_loader import get_questions

API_URL = "http://127.0.0.1:8000/ask"


def similarity(a: str, b: str) -> float:
    """Compara resposta esperada e gerada; retorna score entre 0 e 1."""
    return difflib.SequenceMatcher(None, a.strip(), b.strip()).ratio()


def run_squad_benchmark(
    scenario: str,
    limit: int = 100,
    *,
    api_url: str = API_URL,
    timeout: float = 120.0,
) -> list[dict[str, Any]]:
    """
    Carrega perguntas do SQuAD-pt, chama /ask e compara respostas com similarity.

    O contexto do SQuAD não é enviado à API — o RAG continua usando os documentos
    indexados em `documents` (ex.: São Manuel).
    """
    questions = get_questions(limit=limit)
    results: list[dict[str, Any]] = []

    for item in questions:
        resp = requests.post(
            api_url,
            json={
                "question": item.question,
                "scenario": scenario,
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        model_answer = data.get("answer", "")

        score = similarity(item.expected_answer, model_answer)

        results.append(
            {
                "question": item.question,
                "expected_answer": item.expected_answer,
                "model_answer": model_answer,
                "scenario": scenario,
                "score": score,
            }
        )

    return results
