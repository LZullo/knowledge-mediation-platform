"""Validação das métricas EM/F1 (padrão SQuAD)."""

from app.evaluation.metrics import exact_match_score, f1_score, normalize_answer


def test_normalize_lowercase_and_punctuation():
    assert normalize_answer("PostgreSQL.") == normalize_answer("postgresql")


def test_exact_match_synonym_normalized():
    assert exact_match_score("REST API", "rest api") == 1.0


def test_exact_match_mismatch():
    assert exact_match_score("Docker", "Kubernetes") == 0.0


def test_f1_partial_overlap():
    pred = "banco de dados relacional postgres"
    gold = "sistema gerenciador de banco de dados objeto relacional"
    assert 0.0 < f1_score(pred, gold) < 1.0


def test_f1_both_empty_normalized():
    assert f1_score("", "") == 1.0


def test_f1_one_empty():
    assert f1_score("resposta", "") == 0.0
