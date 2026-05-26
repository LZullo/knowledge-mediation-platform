"""
Benchmark preliminar (5 perguntas, 3 cenários) com persistência segura.

Cenários: llm, rag_basic, rag_rerank
Configure no .env: LLM_PROVIDER=ollama, OLLAMA_MODEL=phi3, LLM_TEMPERATURE=0

Teste 1 (histórico): corpus_version=wikipedia_benchmark_v1
Teste 2+ (corpus expandido): corpus_version=wikipedia_benchmark_v2
"""

import argparse
import logging

from app.evaluation.benchmark_runner import run_benchmark_preliminary

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--corpus-version",
        default="wikipedia_benchmark_v1",
        help="Versão do corpus (v1=reproduz Teste 1 com índice v1)",
    )
    args = parser.parse_args()

    from app.infrastructure.db.connection import SessionLocal

    with SessionLocal() as session:
        out = run_benchmark_preliminary(
            session,
            corpus_version=args.corpus_version,
        )

    print("\n=== Resumo preliminar ===")
    print(f"corpus_version={out.report.corpus_version}")
    print(f"documentos no índice={out.report.corpus_document_count}")
    for summary in out.report.summaries:
        print(
            f"{summary.scenario}: EM={summary.mean_exact_match:.4f} "
            f"F1={summary.mean_f1:.4f} latência={summary.mean_latency_seconds:.2f}s"
        )

    if out.json_path:
        print(f"\nJSON: {out.json_path}")
    if out.csv_path:
        print(f"CSV: {out.csv_path}")
