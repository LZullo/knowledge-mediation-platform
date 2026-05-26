"""
Métricas de avaliação no padrão SQuAD (EM e F1).

Normalização: minúsculas, remoção de pontuação, artigos (PT/EN), colapso de espaços.
Não remove stopwords gerais — alinhado a benchmarks QA tradicionais (SQuAD oficial).
"""

from __future__ import annotations

import re
import string
from collections import Counter

# Artigos em inglês (SQuAD original) e português (SQuAD-pt)
_ARTICLES_RE = re.compile(
    r"\b(a|an|the|o|a|os|as|um|uma|uns|umas)\b",
    flags=re.IGNORECASE | re.UNICODE,
)


def normalize_answer(text: str) -> str:
    """
    Normalização SQuAD: minúsculas, sem pontuação, sem artigos, espaços colapsados.
    """
    if not text:
        return ""

    text = text.lower()
    text = "".join(ch for ch in text if ch not in string.punctuation)
    text = _ARTICLES_RE.sub(" ", text)
    return " ".join(text.split())


def exact_match_score(prediction: str, ground_truth: str) -> float:
    """1.0 se respostas normalizadas forem iguais; caso contrário 0.0."""
    return float(normalize_answer(prediction) == normalize_answer(ground_truth))


def f1_score(prediction: str, ground_truth: str) -> float:
    """F1 por sobreposição de tokens após normalização SQuAD."""
    pred_tokens = normalize_answer(prediction).split()
    gold_tokens = normalize_answer(ground_truth).split()

    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0

    common = Counter(pred_tokens) & Counter(gold_tokens)
    num_same = sum(common.values())
    if num_same == 0:
        return 0.0

    precision = num_same / len(pred_tokens)
    recall = num_same / len(gold_tokens)
    return 2 * precision * recall / (precision + recall)
