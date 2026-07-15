"""
Objetivo:
Validação qualitativa manual do retrieval vetorial para análise experimental do TCC.

Este script NÃO avalia respostas geradas pelo LLM.
Ele avalia:
- relevância semântica dos chunks recuperados
- qualidade do top-k
- adequação do retrieval ao corpus experimental
"""

import logging
import argparse
import time
from pathlib import Path
from typing import TextIO

from app.application.strategies.retrieval.pgvector import PgVectorRetrievalStrategy
from app.dados.chunking import parse_wikipedia_source
from app.dados.corpus_registry import effective_retrieval_versions, resolve_corpus_version
from app.infrastructure.db.connection import SessionLocal

logging.basicConfig(level=logging.INFO)

QUESTIONS = [
    "O que é machine learning?",
    "O que é PostgreSQL?",
    "O que é uma API REST?",
    "Como funciona Docker?",
    "O que é inteligência artificial?",
    "O que é pgvector?",
    "Como funciona recuperação da informação?",
    "O que são embeddings?",
    "Qual a função da busca semântica?",
]


def _make_dual_printer(output_file: TextIO | None):
    """
    Imprime no console e, se habilitado, também escreve no arquivo.
    Mantém a formatação das chamadas `out_print("...")`.
    """

    def out_print(message: str) -> None:
        print(message)
        if output_file is not None:
            output_file.write(message + "\n")

    return out_print


def _diversidade_chunks_label(*, unique_urls_count: int, total_chunks: int) -> str:
    if total_chunks <= 0:
        return "baixa"
    ratio = unique_urls_count / total_chunks
    if ratio >= 0.8:
        return "boa"
    if ratio >= 0.4:
        return "média"
    return "baixa"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspector experimental de retrieval qualitativo (pgvector) filtrando por corpus_version."
    )
    parser.add_argument(
        "--corpus-version",
        default="wikipedia_benchmark_v3",
        help="Versão alvo do corpus (ex.: wikipedia_benchmark_v3).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Quantidade de chunks a recuperar por pergunta.",
    )
    parser.add_argument(
        "--save-output",
        action="store_true",
        help="Salva a saída textual em results/retrieval_validation_<corpus_version>.txt",
    )
    args = parser.parse_args()

    # Este script continua sendo apenas uma ferramenta qualitativa auxiliar.
    # Ele não avalia respostas geradas pelo LLM; ele foca em relevância do retrieval.
    # Importância do top-1: ele tende a refletir cobertura semântica imediata do corpus
    # e costuma influenciar fortemente a qualidade do contexto enviado ao RAG.
    resolved_corpus_version = resolve_corpus_version(args.corpus_version)
    retrieval_versions = effective_retrieval_versions(args.corpus_version)

    # Garantia explícita do mapeamento cumulativo (v1, v2 e v3).
    expected = {
        "wikipedia_benchmark_v1": ("wikipedia_benchmark_v1",),
        "wikipedia_benchmark_v2": ("wikipedia_benchmark_v1", "wikipedia_benchmark_v2"),
        "wikipedia_benchmark_v3": (
            "wikipedia_benchmark_v1",
            "wikipedia_benchmark_v2",
            "wikipedia_benchmark_v3",
        ),
    }.get(resolved_corpus_version)
    if expected is not None and tuple(retrieval_versions) != expected:
        raise RuntimeError(
            "Inconsistência no mapeamento de effective_retrieval_versions. "
            f"Esperado={expected!r}, recebido={tuple(retrieval_versions)!r}."
        )

    repo_root = Path(__file__).resolve().parents[2]
    output_file_path: Path | None = None
    output_file: TextIO | None = None
    if args.save_output:
        output_dir = repo_root / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file_path = output_dir / f"retrieval_validation_{resolved_corpus_version}.txt"
        output_file = output_file_path.open("w", encoding="utf-8")

    out_print = _make_dual_printer(output_file)

    out_print("=" * 100)
    out_print(f"Corpus alvo (filtro lógico): {resolved_corpus_version}")
    out_print(f"Corpus versions efetivamente usadas na busca: {', '.join(retrieval_versions)}")
    out_print(f"top_k={args.top_k}")
    out_print("=" * 100)
    if output_file_path is not None:
        out_print(f"Saída salva em: {output_file_path.as_posix()}")

    strategy = PgVectorRetrievalStrategy(corpus_versions=retrieval_versions)

    with SessionLocal() as session:
        try:
            for question in QUESTIONS:
                out_print("")
                out_print("=" * 100)
                out_print(f"PERGUNTA: {question}")
                out_print("-" * 100)
                out_print(f"(filtrando corpus_versions={retrieval_versions})")

                t0 = time.perf_counter()
                docs = strategy.retrieve(session, question, top_k=args.top_k)
                t1 = time.perf_counter()

                out_print(f"Tempo retrieval: {t1 - t0:.3f}s")
                out_print(f"Quantidade de chunks retornados: {len(docs)}")

                docs_corpus_versions: dict[str, int] = {}
                for doc in docs:
                    meta = parse_wikipedia_source(doc.source)
                    corpus_version = meta.get("corpus_version", "?")
                    docs_corpus_versions[corpus_version] = docs_corpus_versions.get(
                        corpus_version, 0
                    ) + 1

                if docs_corpus_versions:
                    mix = ", ".join([f"{k}={v}" for k, v in docs_corpus_versions.items()])
                    out_print(f"Mix de corpus na saída top-k: {mix}")

                chunk_infos: list[dict[str, str | int | float | None]] = []
                for i, doc in enumerate(docs, start=1):
                    meta = parse_wikipedia_source(doc.source)
                    corpus_version = meta.get("corpus_version", "?")
                    title = meta.get("title", "?")
                    topic = meta.get("topic", "?")
                    url = meta.get("url", "?")

                    chunk_infos.append(
                        {
                            "i": i,
                            "corpus_version": corpus_version,
                            "title": title,
                            "topic": topic,
                            "url": url,
                            "content": doc.content,
                            "cosine_distance": getattr(doc, "cosine_distance", None),
                        }
                    )

                    out_print("")
                    out_print(f"--- CHUNK {i}/{len(docs)} ---")
                    out_print(f"Título : {title}")
                    out_print(f"Tópico : {topic}")
                    out_print(f"URL    : {url}")
                    out_print(f"Corpus version: {corpus_version}")

                    if hasattr(doc, "similarity_score"):
                        out_print(f"Similarity: {doc.similarity_score:.4f}")
                    elif hasattr(doc, "cosine_distance"):
                        out_print(
                            f"Cosine distance: {doc.cosine_distance:.4f} (menor = mais similar)"
                        )

                    out_print(doc.content[:400])

                unique_urls = {c["url"] for c in chunk_infos if c["url"]}
                diversity_label = _diversidade_chunks_label(
                    unique_urls_count=len(unique_urls),
                    total_chunks=len(chunk_infos),
                )
                repeated_detected = "sim" if len(unique_urls) < len(chunk_infos) else "não"

                out_print("")
                out_print("Resumo (preencher manualmente):")
                out_print("Top-1 relevante? [manual]")
                out_print(f"Diversidade dos chunks: {diversity_label}")
                out_print(f"Chunks repetidos detectados? {repeated_detected}")

                if chunk_infos:
                    top1 = chunk_infos[0]
                    out_print(f"Top-1 (título): {top1['title']}")
                    out_print(f"Top-1 (corpus): {top1['corpus_version']}")
                    out_print(f"Top-1 (URL): {top1['url']}")
        finally:
            if output_file is not None:
                output_file.close()


if __name__ == "__main__":
    main()
