"""
Pipeline RAG genérico: recuperação + montagem de contexto/prompt + LLM.
Comportamentos variáveis via Strategy (retrieval, prompt, generation).
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.application.strategies.generation import GenerationStrategy, OpenAIGenerationStrategy
from app.application.strategies.prompt import DefaultPromptStrategy, PromptStrategy
from app.application.strategies.retrieval import PgVectorRetrievalStrategy, RetrievalStrategy
from app.infrastructure.llm import LLMGenerationResult
from app.infrastructure.vectorstore import SimilarDocument


@dataclass(frozen=True)
class RAGPipelineResult:
    """Saída do pipeline: resposta do modelo e metadados alinhados aos chunks."""

    answer: str
    retrieved_chunks: list[str]
    similarity_scores: list[float]
    """Scores no intervalo ~[0, 1]; maior = mais similar (derivado da distância cosseno)."""
    prompt: str
    tokens_used: int | None
    model: str


def cosine_distance_to_similarity(cosine_distance: float) -> float:
    """
    Converte distância cosseno do pgvector (`<=>`) em um score de similaridade.
    Para vetores L2-normalizados, o operador fica em [0, 2]; mapeamos para [1, 0] e limitamos a [0, 1].
    """
    score = 1.0 - (cosine_distance / 2.0)
    if score < 0.0:
        return 0.0
    if score > 1.0:
        return 1.0
    return score


def run_rag_pipeline(
    session: Session,
    *,
    question: str,
    top_k: int,
    retrieval: RetrievalStrategy | None = None,
    prompt: PromptStrategy | None = None,
    generation: GenerationStrategy | None = None,
) -> RAGPipelineResult:
    """
    Executa o fluxo: recuperação → contexto → prompt → geração.

    Passe instâncias customizadas de `RetrievalStrategy`, `PromptStrategy` ou `GenerationStrategy`
    para experimentar sem alterar este módulo.
    """
    if not question.strip():
        raise ValueError("question não pode ser vazia")
    if top_k < 1:
        raise ValueError("top_k deve ser >= 1")

    retrieval_st: RetrievalStrategy = retrieval or PgVectorRetrievalStrategy()
    prompt_st: PromptStrategy = prompt or DefaultPromptStrategy()
    generation_st: GenerationStrategy = generation or OpenAIGenerationStrategy()

    documents = retrieval_st.retrieve(session, question, top_k)

    retrieved_chunks = [d.content for d in documents]
    similarity_scores = [cosine_distance_to_similarity(d.cosine_distance) for d in documents]

    context_text = prompt_st.build_context(question, documents)
    prompt_text = prompt_st.build_prompt(question, context_text)

    llm_out: LLMGenerationResult = generation_st.generate(prompt_text)

    return RAGPipelineResult(
        answer=llm_out.text,
        retrieved_chunks=retrieved_chunks,
        similarity_scores=similarity_scores,
        prompt=prompt_text,
        tokens_used=llm_out.tokens_used,
        model=llm_out.model,
    )
