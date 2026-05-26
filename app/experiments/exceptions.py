"""Exceções do pipeline experimental (retrieval, LLM, persistência, benchmark)."""


class ExperimentalError(Exception):
    """Base para falhas no fluxo experimental."""


class RetrievalError(ExperimentalError):
    """Falha na recuperação vetorial ou rerank."""


class LLMError(ExperimentalError):
    """Falha na geração com o provedor de LLM."""


class PersistenceError(ExperimentalError):
    """Falha ao gravar em `experiment_runs`."""


class BenchmarkError(ExperimentalError):
    """Falha na orquestração do benchmark (carregamento, agregação, export)."""


class ExperimentalValidationError(ExperimentalError):
    """Estado inválido antes ou depois da execução (corpus vazio, resposta vazia, etc.)."""
