"""
Teste do pipeline RAG completo com Ollama local.

Fluxo: pergunta → pgvector → chunks → prompt → Ollama → resposta.

Padrão: LLM_PROVIDER=ollama e OLLAMA_MODEL=phi3 (via .env ou config).
"""

import logging

from app.application.use_cases.execute_rag import ExecuteRAGInput, RAGScenario, execute_rag
from app.infrastructure.db.connection import SessionLocal

logging.basicConfig(level=logging.INFO)

QUESTION = "O que é PostgreSQL?"
SCENARIO = RAGScenario.RAG_BASIC

if __name__ == "__main__":
    with SessionLocal() as session:
        result = execute_rag(
            session,
            ExecuteRAGInput(question=QUESTION, scenario=SCENARIO),
        )
        session.commit()

    print("\n--- RESPOSTA ---")
    print(result.answer)
    print(f"\nModelo: {result.model}")
    print(f"Chunks recuperados: {len(result.retrieved_chunks)}")
    print(f"Tamanho do prompt: {len(result.prompt)} caracteres")
