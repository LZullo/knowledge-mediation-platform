"""Testes do carregador de perguntas de benchmark."""

from __future__ import annotations

import json
from pathlib import Path

from app.dados.benchmark_loader import load_benchmark_questions

_V3_PATH = Path(__file__).resolve().parents[1] / "app" / "dados" / "benchmark_questions_v3.json"


def test_benchmark_v3_loads_18_questions():
    questions = load_benchmark_questions(path=_V3_PATH)
    assert len(questions) == 18


def test_benchmark_v3_core_5_subset():
    core = load_benchmark_questions(path=_V3_PATH, subset="core_5")
    assert len(core) == 5
    assert all(q.subset == "core_5" for q in core)


def test_benchmark_v3_extended_subset():
    extended = load_benchmark_questions(path=_V3_PATH, subset="extended")
    assert len(extended) == 13


def test_benchmark_v3_has_ids():
    questions = load_benchmark_questions(path=_V3_PATH)
    assert all(q.question_id for q in questions)


def test_benchmark_v3_json_schema():
    raw = json.loads(_V3_PATH.read_text(encoding="utf-8"))
    subsets = {item["subset"] for item in raw}
    assert subsets == {"core_5", "extended"}
