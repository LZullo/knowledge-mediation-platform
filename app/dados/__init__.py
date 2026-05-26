"""Dados e corpus — imports leves no pacote (evita carregar indexador/LLM no `import app.dados`)."""

from app.dados.benchmark_loader import BenchmarkQuestion, load_benchmark_questions
from app.dados.corpus_registry import CORPUS_VERSIONS, get_corpus_definition, resolve_corpus_version

__all__ = [
    "BenchmarkQuestion",
    "CORPUS_VERSIONS",
    "get_corpus_definition",
    "load_benchmark_questions",
    "resolve_corpus_version",
]
