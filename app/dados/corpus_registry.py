"""
Registro versionado de corpora experimentais (Wikipédia técnica PT).

Cada versão define tópicos, parâmetros de chunking e linhagem para retrieval cumulativo.
O Teste 1 (benchmark preliminar) corresponde a `wikipedia_benchmark_v1`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

# Alias legado usado no relatório do Teste 1 (20260525_160434).
LEGACY_CORPUS_LABEL = "wikipedia_benchmark"

CorpusTier = Literal["initial", "expanded", "refined"]

# --- Tópicos v1 (corpus inicial — reproduz o Teste 1) ---
WIKI_TOPICS_V1: tuple[str, ...] = (
    "Aprendizado_de_máquina",
    "Inteligência_artificial",
    "Rede_neural_artificial",
    "PostgreSQL",
    "Docker_(software)",
    "Interface_de_programação_de_aplicações",
    "REST",
    "Banco_de_dados",
    "Algoritmo",
)

# Títulos MediaWiki em PT para expansão v2 (tópicos RAG / vetores / stack).
WIKI_TOPICS_V2_ADDITIONS: tuple[str, ...] = (
    "Embedding",
    "Sentence-BERT",
    "Banco_de_dados_vetorial",
    "Busca_semântica",
    "Recuperação_de_informação",
    "Similaridade_do_cosseno",
    "Transformer_(modelo_de_linguagem)",
    "LangChain",
    "FastAPI",
    "Serviço_web",
    "Geração_de_texto",
)

# v3: mesmos tópicos que v2, chunking refinado (maior overlap, menos fragmentação).
WIKI_TOPICS_V2_ALL: tuple[str, ...] = tuple(
    dict.fromkeys(WIKI_TOPICS_V1 + WIKI_TOPICS_V2_ADDITIONS)
)


@dataclass(frozen=True, slots=True)
class CorpusVersionDefinition:
    """Definição imutável de uma versão experimental do corpus."""

    version_id: str
    tier: CorpusTier
    topics: tuple[str, ...]
    chunk_size: int
    chunk_overlap: int
    parent_version: str | None
    added_topics: tuple[str, ...]
    motivation: str
    expected_impact: str
    chunking_notes: str


CORPUS_VERSIONS: dict[str, CorpusVersionDefinition] = {
    "wikipedia_benchmark_v1": CorpusVersionDefinition(
        version_id="wikipedia_benchmark_v1",
        tier="initial",
        topics=WIKI_TOPICS_V1,
        chunk_size=500,
        chunk_overlap=100,
        parent_version=None,
        added_topics=(),
        motivation=(
            "Corpus inicial controlado para o benchmark preliminar (Teste 1), "
            "com tópicos técnicos amplos da Wikipédia em português."
        ),
        expected_impact=(
            "Baseline de cobertura documental; evidenciou ganhos de RAG e lacunas "
            "(ex.: pgvector ausente no índice)."
        ),
        chunking_notes=(
            "chunk_size=500, overlap=100 — alinhado à indexação usada antes do Teste 1."
        ),
    ),
    "wikipedia_benchmark_v2": CorpusVersionDefinition(
        version_id="wikipedia_benchmark_v2",
        tier="expanded",
        topics=WIKI_TOPICS_V2_ALL,
        chunk_size=500,
        chunk_overlap=100,
        parent_version="wikipedia_benchmark_v1",
        added_topics=WIKI_TOPICS_V2_ADDITIONS,
        motivation=(
            "Expansão incremental com tópicos de embeddings e busca vetorial, APIs e "
            "ferramentas do pipeline RAG, sem remover documentos da v1."
        ),
        expected_impact=(
            "Melhorar cobertura em perguntas sobre embeddings e retrieval; "
            "permitir comparar benchmarks v1 vs. v2 com filtro de versão."
        ),
        chunking_notes=(
            "Mesmos parâmetros de chunk da v1 na expansão; apenas tópicos novos são indexados."
        ),
    ),
    "wikipedia_benchmark_v3": CorpusVersionDefinition(
        version_id="wikipedia_benchmark_v3",
        tier="refined",
        topics=WIKI_TOPICS_V2_ALL,
        chunk_size=500,
        chunk_overlap=150,
        parent_version="wikipedia_benchmark_v2",
        added_topics=(),
        motivation=(
            "Reindexação com overlap maior para reduzir fragmentação de conceitos "
            "entre chunks adjacentes."
        ),
        expected_impact=(
            "Chunks mais contextuais; possível redução de ruído na recuperação. "
            "Coexiste com v1/v2 no banco — benchmarks devem declarar a versão alvo."
        ),
        chunking_notes=(
            "chunk_size=500, overlap=150 (+50 vs. v1/v2). Reindexa todos os tópicos de v2 "
            "com nova marca de versão; não apaga versões anteriores."
        ),
    ),
}


def get_corpus_definition(version_id: str) -> CorpusVersionDefinition:
    if version_id not in CORPUS_VERSIONS:
        known = ", ".join(sorted(CORPUS_VERSIONS))
        raise ValueError(f"corpus_version desconhecida: {version_id!r}. Conhecidas: {known}")
    return CORPUS_VERSIONS[version_id]


def resolve_corpus_version(corpus_version: str | None) -> str:
    """Aceita alias legado `wikipedia_benchmark` → v1."""
    if corpus_version is None or corpus_version == LEGACY_CORPUS_LABEL:
        return "wikipedia_benchmark_v1"
    return corpus_version


def effective_retrieval_versions(version_id: str) -> tuple[str, ...]:
    """
    Versões de documentos visíveis na busca para um benchmark.

    v1 → só v1; v2 → v1+v2 (cumulativo); v3 → v1+v2+v3.
    """
    resolved = resolve_corpus_version(version_id)
    order = ("wikipedia_benchmark_v1", "wikipedia_benchmark_v2", "wikipedia_benchmark_v3")
    if resolved not in order:
        return (resolved,)
    idx = order.index(resolved)
    return order[: idx + 1]


def topics_to_index_for_version(version_id: str) -> tuple[str, ...]:
    """Tópicos que o pipeline de indexação deve tentar baixar nesta execução."""
    defn = get_corpus_definition(resolve_corpus_version(version_id))
    if defn.tier == "expanded" and defn.added_topics:
        return defn.added_topics
    return defn.topics


# Compatibilidade com código que importa WIKI_TOPICS
WIKI_TOPICS = WIKI_TOPICS_V1
