# Exemplo rápido — API `/ask`

Com a API no ar (`make run` ou uvicorn na porta 8000):

```bash
curl -s http://127.0.0.1:8000/health

curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"O que é RAG?\", \"scenario\": \"rag_basic\", \"top_k\": 5}"
```

Documentação interativa: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Cenários típicos: `llm`, `rag_basic`, `rag_optimized`, `rag_rerank`.
