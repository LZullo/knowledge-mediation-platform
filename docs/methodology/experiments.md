# Experimentos operacionais

Guia para **executar** benchmarks da plataforma e exportar artefatos locais.

> Resultados científicos, campanhas oficiais e análise do artigo vivem em `knowledge-mediation-study`.  
> Histórico acadêmico (TCC, banca, estudos preliminares) vive em `research-archive` (privado).

## Pré-condições

- [ ] `docker compose up -d` (PostgreSQL + pgvector na porta 5433)
- [ ] `.env` na raiz configurado (`DATABASE_URL`, `LLM_PROVIDER`, `OLLAMA_*` ou `OPENAI_API_KEY`)
- [ ] Ollama rodando e modelo instalado (`ollama pull phi3`) se `LLM_PROVIDER=ollama`
- [ ] Tabelas criadas (`python scripts/indexing/create_tables.py`)
- [ ] Corpus indexado (`python scripts/indexing/indexar_dados.py` ou `indexar_corpus.py`)
- [ ] Dependências instaladas (`make install` ou `pip install -r requirements.txt`)

## Ambiente (resumo)

```bash
cd knowledge-mediation-platform
docker compose up -d
cp .env.example .env
# editar .env
make install
python scripts/indexing/create_tables.py
```

## Indexação

```bash
python scripts/indexing/indexar_dados.py
# ou versão explícita:
python scripts/indexing/indexar_corpus.py --version wikipedia_benchmark_v3 --no-incremental
```

Ficheiros de perguntas de exemplo (fixtures da plataforma):

- `app/dados/benchmark_questions_v2_final.json`
- `app/dados/benchmark_questions_v3.json`

## Benchmark completo

**Com Ollama:**

```bash
# .env: LLM_PROVIDER=ollama, OLLAMA_MODEL=phi3, LLM_TEMPERATURE=0
python scripts/benchmark/run_benchmark_ollama.py \
  --corpus-version wikipedia_benchmark_v3 \
  --questions-path app/dados/benchmark_questions_v3.json
```

**Via Python** (respeita `LLM_PROVIDER`):

```python
import logging
from app.infrastructure.db.connection import SessionLocal
from app.evaluation import run_benchmark_experiment

logging.basicConfig(level=logging.INFO)

with SessionLocal() as session:
    out = run_benchmark_experiment(
        session,
        corpus_version="wikipedia_benchmark_v3",
        limit=None,
        questions_path="app/dados/benchmark_questions_v3.json",
        top_k=5,
        rerank_top_k=10,
        commit_each=True,
    )

for s in out.report.summaries:
    print(s)
```

Cenários padrão: `llm`, `rag_basic`, `rag_optimized`, `rag_rerank`.

### Benchmark parcial (um cenário)

```python
from app.evaluation.benchmark_runner import run_benchmark
from app.application.use_cases.execute_rag import RAGScenario
from app.infrastructure.db.connection import SessionLocal

with SessionLocal() as session:
    report = run_benchmark(
        session,
        limit=20,
        scenarios=(RAGScenario.RAG_RERANK,),
        top_k=3,
        rerank_top_k=10,
    )
```

## Artefatos gerados (área local)

Diretório: `results/` na raiz da plataforma (**gitignored**; scratch local regenerável).

| Arquivo | Conteúdo |
|---------|----------|
| `benchmark_*.json` | `summaries` + `results` (cada pergunta) |
| `benchmark_*.csv` | Uma linha por (cenário, pergunta): EM, F1, latência, tokens, chunks |

### Colunas CSV úteis

- `scenario`, `exact_match`, `f1`, `latency_seconds`
- `tokens_used`, `chunks_retrieved`
- `question`, `expected_answer`, `model_answer`

### Agregação rápida

```python
import pandas as pd

df = pd.read_csv("results/benchmark_<run_id>.csv")
print(df.groupby("scenario")[["exact_match", "f1", "latency_seconds"]].mean())
```

## Teste manual via API

```bash
make run
```

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"O que é pgvector?","scenario":"rag_rerank","top_k":3,"rerank_top_k":10}'
```

Swagger: `http://127.0.0.1:8000/docs`

## Registro em `experiment_runs`

Cada chamada a `execute_rag` (incluindo via benchmark) grava pergunta, cenário, parâmetros, chunks, prompt, resposta, latência e tokens — útil para auditoria operacional.

## Checklist de reprodutibilidade operacional

Documente em cada rodada local:

- [ ] `limit` de perguntas
- [ ] Tópicos (`WIKI_TOPICS`) e `corpus_version`
- [ ] `chunk_size` / `chunk_overlap`
- [ ] `top_k`, `rerank_top_k`
- [ ] `LLM_PROVIDER` e modelo
- [ ] Commit git da plataforma

## Subconjuntos do JSON v3

O ficheiro `app/dados/benchmark_questions_v3.json` usa o campo `subset`:

| Subset | Papel |
|--------|--------|
| `core_5` | Conjunto menor de perguntas de referência |
| `extended` | Perguntas adicionais para cobertura temática |

## Troubleshooting

| Problema | Causa provável |
|----------|----------------|
| EM/F1 ≈ 0 em todos | Base não indexada ou pergunta fora do corpus |
| Retrieval irrelevante | Reindexar; conferir `corpus_version` |
| Erro 502 na API | Ollama parado ou `OPENAI_API_KEY` inválida |
| Ollama não responde | Conferir `OLLAMA_BASE_URL` |
| Dimensão embedding | `VECTOR_DIMENSIONS` ≠ saída do modelo |
| Benchmark lento | Muitas perguntas + rerank + modelo local |
| OOM no rerank | Reduzir `rerank_top_k` |
