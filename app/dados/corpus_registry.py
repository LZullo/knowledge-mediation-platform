"""
Registro versionado de corpora experimentais (Wikipédia técnica PT + complementar).

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

WIKI_TOPICS_V2_ALL: tuple[str, ...] = tuple(
    dict.fromkeys(WIKI_TOPICS_V1 + WIKI_TOPICS_V2_ADDITIONS)
)

# v3: títulos solicitados → fallback opcional (validação prévia via wiki_topic_validation).
WIKI_TOPICS_V3_CANDIDATES: dict[str, str | None] = {
    "Aprendizado_de_máquina": None,
    "PostgreSQL": None,
    "REST": None,
    "Docker_(software)": None,
    "Embedding": "Representação_distribuída",
    "Banco_de_dados_vetorial": None,
    "Busca_semântica": None,
    "Recuperação_de_informação": None,
    "Similaridade_do_cosseno": None,
    "Transformer_(modelo_de_linguagem)": "Modelo_transformer",
    "LangChain": None,
    "Processamento_de_linguagem_natural": None,
    "Modelo_de_linguagem": None,
    "Rede_neural_artificial": None,
    "Interface_de_programação_de_aplicações": None,
}

# Lista plana única (sem duplicar Docker)
WIKI_TOPICS_V3_REQUESTED: tuple[str, ...] = tuple(
    dict.fromkeys(
        (
            "Aprendizado_de_máquina",
            "PostgreSQL",
            "REST",
            "Docker_(software)",
            "Embedding",
            "Banco_de_dados_vetorial",
            "Busca_semântica",
            "Recuperação_de_informação",
            "Similaridade_do_cosseno",
            "Transformer_(modelo_de_linguagem)",
            "LangChain",
            "Processamento_de_linguagem_natural",
            "Modelo_de_linguagem",
            "Rede_neural_artificial",
            "Interface_de_programação_de_aplicações",
        )
    )
)

# Documentos complementares (fora da Wikipédia PT) — ver docs/custom_corpus/
CUSTOM_CORPUS_V3: tuple[str, ...] = ("pgvector",)


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
    wiki_topic_fallbacks: dict[str, str | None]
    custom_corpus_topics: tuple[str, ...]
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
        wiki_topic_fallbacks={},
        custom_corpus_topics=(),
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
        wiki_topic_fallbacks={},
        custom_corpus_topics=(),
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
        topics=WIKI_TOPICS_V3_REQUESTED,
        chunk_size=500,
        chunk_overlap=150,
        parent_version="wikipedia_benchmark_v2",
        added_topics=WIKI_TOPICS_V3_REQUESTED,
        wiki_topic_fallbacks={
            k: v
            for k, v in WIKI_TOPICS_V3_CANDIDATES.items()
            if k in WIKI_TOPICS_V3_REQUESTED
        },
        custom_corpus_topics=CUSTOM_CORPUS_V3,
        motivation=(
            "Refinamento experimental: corpus Wikipédia curado com validação prévia de "
            "títulos, documentação complementar controlada para lacunas da Wikipédia PT "
            "(ex.: pgvector), benchmark ampliado e controle de verbosidade do gerador — "
            "sem alterar embeddings, retrieval ou rerank."
        ),
        expected_impact=(
            "Aumentar cobertura documental real; permitir Teste 3 com subconjuntos "
            "core_5 e extended; manter rastreabilidade v1→v2→v3."
        ),
        chunking_notes=(
            "chunk_size=500, overlap=150 (secundário). Principal evolução: curadoria, "
            "validação de títulos e corpus complementar documentado."
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
    """Tópicos Wikipédia que o pipeline de indexação deve tentar baixar nesta execução."""
    defn = get_corpus_definition(resolve_corpus_version(version_id))
    if defn.tier == "expanded" and defn.added_topics:
        return defn.added_topics
    return defn.topics


def wiki_fallbacks_for_version(version_id: str) -> dict[str, str | None]:
    defn = get_corpus_definition(resolve_corpus_version(version_id))
    return dict(defn.wiki_topic_fallbacks)


def custom_corpus_for_version(version_id: str) -> tuple[str, ...]:
    defn = get_corpus_definition(resolve_corpus_version(version_id))
    return defn.custom_corpus_topics


# Compatibilidade com código que importa WIKI_TOPICS
WIKI_TOPICS = WIKI_TOPICS_V1
