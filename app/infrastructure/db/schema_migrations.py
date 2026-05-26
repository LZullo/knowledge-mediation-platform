"""
Migrações idempotentes do schema experimental (sem Alembic).

Corrige colunas VARCHAR legadas para TEXT e adiciona campos de latência/provedor.
"""

from __future__ import annotations

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

_TEXT_COLUMNS = (
    "question",
    "scenario",
    "parameters",
    "retrieved_chunks",
    "similarity_scores",
    "prompt",
    "response",
)

_NEW_COLUMNS: tuple[tuple[str, str], ...] = (
    ("llm_provider", "TEXT"),
    ("llm_model", "TEXT"),
    ("retrieval_latency", "DOUBLE PRECISION"),
    ("generation_latency", "DOUBLE PRECISION"),
    ("total_latency", "DOUBLE PRECISION"),
)


def migrate_experiment_runs(engine: Engine) -> None:
    """Aplica ALTER/ADD em `experiment_runs` de forma segura e repetível."""
    inspector = inspect(engine)
    if "experiment_runs" not in inspector.get_table_names():
        logger.info("Tabela experiment_runs ausente; create_all deve criá-la.")
        return

    existing = {c["name"] for c in inspector.get_columns("experiment_runs")}

    with engine.begin() as conn:
        for col in _TEXT_COLUMNS:
            if col not in existing:
                continue
            conn.execute(
                text(
                    f"ALTER TABLE experiment_runs "
                    f"ALTER COLUMN {col} TYPE TEXT USING {col}::TEXT"
                )
            )
            logger.info("experiment_runs.%s -> TEXT", col)

        has_total_latency = "total_latency" in existing
        for col_name, col_type in _NEW_COLUMNS:
            if col_name in existing:
                continue
            conn.execute(
                text(
                    f"ALTER TABLE experiment_runs "
                    f"ADD COLUMN {col_name} {col_type}"
                )
            )
            if col_name == "total_latency":
                has_total_latency = True
            logger.info("experiment_runs: coluna %s adicionada", col_name)

        if has_total_latency and "latency" in existing:
            conn.execute(
                text(
                    "UPDATE experiment_runs "
                    "SET total_latency = latency "
                    "WHERE total_latency IS NULL AND latency IS NOT NULL"
                )
            )


_DOCUMENTS_NEW_COLUMNS: tuple[tuple[str, str], ...] = (
    ("content_hash", "TEXT"),
    ("source_url", "TEXT"),
    ("source_topic", "TEXT"),
    ("corpus_version", "TEXT"),
)


def migrate_documents(engine: Engine) -> None:
    """Adiciona colunas de rastreio em `documents` e marca legado como v1."""
    inspector = inspect(engine)
    if "documents" not in inspector.get_table_names():
        logger.info("Tabela documents ausente; create_all deve criá-la.")
        return

    existing = {c["name"] for c in inspector.get_columns("documents")}

    with engine.begin() as conn:
        for col_name, col_type in _DOCUMENTS_NEW_COLUMNS:
            if col_name in existing:
                continue
            conn.execute(
                text(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")
            )
            logger.info("documents: coluna %s adicionada", col_name)

        conn.execute(
            text(
                "UPDATE documents SET corpus_version = 'wikipedia_benchmark_v1' "
                "WHERE corpus_version IS NULL"
            )
        )
        logger.info(
            "documents: registros legados marcados como wikipedia_benchmark_v1"
        )

        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_documents_content_hash "
                "ON documents (content_hash)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_documents_source_topic "
                "ON documents (source_topic)"
            )
        )
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_documents_corpus_version "
                "ON documents (corpus_version)"
            )
        )

        # Metadados legados: extrair topic/url do campo `source` quando possível
        conn.execute(
            text(
                """
                UPDATE documents
                SET source_topic = substring(source from 'topic=([^|]+)')
                WHERE source_topic IS NULL
                  AND source LIKE 'wikipedia|topic=%'
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE documents
                SET source_url = substring(source from 'url=([^|]+)')
                WHERE source_url IS NULL
                  AND source LIKE '%|url=%'
                """
            )
        )
        logger.info("documents: metadados legados backfill (source_topic, source_url)")
