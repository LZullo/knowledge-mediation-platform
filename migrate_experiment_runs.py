"""
Aplica migração idempotente em `experiment_runs` (TEXT + colunas de latência/provedor).

Uso:
  python migrate_experiment_runs.py
"""

import logging

from app.infrastructure.db.connection import create_tables, engine
from app.infrastructure.db.schema_migrations import migrate_experiment_runs

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    create_tables(migrate=False)
    migrate_experiment_runs(engine)
    print("Migração experiment_runs concluída.")
