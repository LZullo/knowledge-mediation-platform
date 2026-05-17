"""Estratégia de montagem de contexto e prompt."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from app.infrastructure.vectorstore import SimilarDocument


@runtime_checkable
class PromptStrategy(Protocol):
    """Define como transformar documentos recuperados no texto enviado ao LLM."""

    def build_context(self, question: str, documents: list[SimilarDocument]) -> str:
        """Monta o bloco de contexto a partir dos trechos recuperados."""
        ...

    def build_prompt(self, question: str, context: str) -> str:
        """Monta o prompt final (instruções + contexto + pergunta)."""
        ...


class DefaultPromptStrategy:
    """Formatação neutra: fonte + conteúdo, depois instrução mínima ao modelo."""

    def build_context(self, question: str, documents: list[SimilarDocument]) -> str:
        _ = question
        if not documents:
            return ""
        parts: list[str] = []
        for doc in documents:
            parts.append(f"[{doc.source}]\n{doc.content}")
        return "\n\n---\n\n".join(parts)

    def build_prompt(self, question: str, context: str) -> str:
        return (
            "Use apenas o contexto abaixo para responder. Se não houver informação suficiente, diga que não sabe.\n\n"
            f"Contexto:\n{context}\n\n"
            f"Pergunta:\n{question}"
        )


class DirectQuestionPromptStrategy:
    """Apenas a pergunta do usuário, sem contexto (modo LLM direto)."""

    def build_context(self, question: str, documents: list[SimilarDocument]) -> str:
        _ = question, documents
        return ""

    def build_prompt(self, question: str, context: str) -> str:
        _ = context
        return question.strip()


class RestrictiveRagPromptStrategy:
    """
    Mesmo contexto que o padrão, com instrução restritiva ao responder só com base no contexto.
    """

    _formatter = DefaultPromptStrategy()

    def build_context(self, question: str, documents: list[SimilarDocument]) -> str:
        return self._formatter.build_context(question, documents)

    def build_prompt(self, question: str, context: str) -> str:
        return (
            "Responda apenas com base no contexto fornecido. "
            "Se não houver informação suficiente no contexto, diga explicitamente que não pode responder.\n\n"
            f"Contexto:\n{context}\n\n"
            f"Pergunta:\n{question}"
        )
