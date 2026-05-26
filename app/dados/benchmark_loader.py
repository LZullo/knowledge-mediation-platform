"""
Carregamento de perguntas de benchmark manuais (JSON).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_QUESTIONS_PATH = Path(__file__).resolve().parent / "benchmark_questions.json"


@dataclass(frozen=True, slots=True)
class BenchmarkQuestion:
    question: str
    expected_answer: str
    question_id: str | None = None
    subset: str | None = None


def load_benchmark_questions(
    *,
    path: Path | str | None = None,
    limit: int | None = None,
    subset: str | None = None,
) -> list[BenchmarkQuestion]:
    """
    Carrega perguntas e respostas de referência do arquivo JSON.

    `limit` restringe a quantidade avaliada (útil para testes rápidos).
    `subset` filtra por campo `subset` (ex.: `core_5`, `extended`).
    """
    json_path = Path(path) if path is not None else _DEFAULT_QUESTIONS_PATH
    if not json_path.is_file():
        raise FileNotFoundError(f"arquivo de benchmark não encontrado: {json_path}")

    raw = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("benchmark_questions.json deve ser uma lista de objetos")

    questions: list[BenchmarkQuestion] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            logger.warning("Entrada ignorada (não é objeto) na linha %s", idx)
            continue
        question = str(item.get("question", "")).strip()
        answer = str(item.get("answer", "")).strip()
        item_subset = item.get("subset")
        subset_str = str(item_subset).strip() if item_subset is not None else None
        if subset is not None and subset_str != subset:
            continue
        if not question or not answer:
            logger.warning("Entrada ignorada (pergunta ou resposta vazia) na linha %s", idx)
            continue
        qid = item.get("id")
        questions.append(
            BenchmarkQuestion(
                question=question,
                expected_answer=answer,
                question_id=str(qid).strip() if qid is not None else None,
                subset=subset_str,
            )
        )

    if limit is not None:
        if limit < 1:
            raise ValueError("limit deve ser >= 1")
        questions = questions[:limit]

    logger.info(
        "Benchmark manual: %s perguntas carregadas de %s (subset=%s)",
        len(questions),
        json_path.name,
        subset or "all",
    )
    return questions
