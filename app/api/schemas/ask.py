"""Contratos HTTP para /ask."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.application.services.rag_pipeline import RAGPipelineResult
from app.application.use_cases.execute_rag import ExecuteRAGInput, RAGScenario


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Pergunta do usuário")
    scenario: RAGScenario
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=200,
        description="Quantidade de documentos (principalmente em rag_optimized); opcional.",
    )
    chunk_size: int = Field(
        default=300,
        ge=1,
        le=100_000,
        description="Tamanho alvo de chunk (uso futuro na indexação).",
    )
    rerank_top_k: int | None = Field(
        default=None,
        ge=1,
        le=200,
        description="Candidatos pgvector antes do rerank (cenário rag_rerank).",
    )
    score_threshold: float | None = Field(
        default=None,
        description="Score mínimo do cross-encoder (cenário rag_rerank).",
    )

    def to_execute_input(self) -> ExecuteRAGInput:
        return ExecuteRAGInput(
            question=self.question.strip(),
            scenario=self.scenario,
            top_k=self.top_k,
            chunk_size=self.chunk_size,
            rerank_top_k=self.rerank_top_k,
            score_threshold=self.score_threshold,
        )


class AskResponse(BaseModel):
    answer: str
    retrieved_chunks: list[str]
    similarity_scores: list[float]
    prompt: str
    tokens_used: int | None
    model: str

    @classmethod
    def from_pipeline(cls, result: RAGPipelineResult) -> AskResponse:
        return cls(
            answer=result.answer,
            retrieved_chunks=result.retrieved_chunks,
            similarity_scores=result.similarity_scores,
            prompt=result.prompt,
            tokens_used=result.tokens_used,
            model=result.model,
        )
