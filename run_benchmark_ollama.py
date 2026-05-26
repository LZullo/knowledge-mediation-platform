"""
Benchmark experimental com Ollama (sem OpenAI).

Configure no .env:
  LLM_PROVIDER=ollama
  OLLAMA_MODEL=phi3

Cenários: llm, rag_basic, rag_optimized, rag_rerank
"""

import argparse
import logging
from pathlib import Path

from app.application.use_cases.execute_rag import RAGScenario
from app.evaluation import run_benchmark_experiment
from app.infrastructure.db.connection import SessionLocal

logging.basicConfig(level=logging.INFO)

_DEFAULT_QUESTIONS_PATH = (
    Path(__file__).resolve().parent
    / "app"
    / "dados"
    / "benchmark_questions_v2_final.json"
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-version",
        default="wikipedia_benchmark_v1",
        help="Versão do corpus para filtro de retrieval",
    )
    parser.add_argument(
        "--questions-path",
        default=str(_DEFAULT_QUESTIONS_PATH),
        help="Arquivo JSON congelado com perguntas do benchmark final",
    )
    args = parser.parse_args()

    with SessionLocal() as session:
        out = run_benchmark_experiment(
            session,
            corpus_version=args.corpus_version,
            limit=None,
            questions_path=args.questions_path,
            scenarios=(
                RAGScenario.LLM,
                RAGScenario.RAG_BASIC,
                RAGScenario.RAG_RERANK,
            ),
            top_k=5,
            rerank_top_k=10,
            commit_each=True,
            safe_persistence=True,
        )

    for summary in out.report.summaries:
        print(summary)

    if out.json_path:
        print(f"\nJSON: {out.json_path}")
    if out.csv_path:
        print(f"CSV: {out.csv_path}")
