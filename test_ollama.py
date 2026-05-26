"""
Teste rápido do provedor Ollama (sem retrieval).

Requer: Ollama rodando, modelo em OLLAMA_MODEL (padrão: phi3).
"""

import logging

from app.application.providers.ollama_provider import OllamaLLMProvider

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    llm = OllamaLLMProvider()
    response = llm.generate("O que é PostgreSQL?")
    print(response)
