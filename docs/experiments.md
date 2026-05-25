# Experimentos e análise de resultados

Guia operacional para executar, exportar e transformar resultados em material do TCC (tabelas e gráficos).

## Pré-condições

- [ ] `docker compose up -d` (PostgreSQL + pgvector na porta 5433)  
- [ ] `.env` na raiz configurado (`DATABASE_URL`, `OPENAI_API_KEY`)  
- [ ] Tabelas criadas (`python create_tables.py`)  
- [ ] Base indexada com filtro de tecnologia (`python indexar_dados.py`)  
- [ ] Dependências instaladas (`make install` na raiz `tcc-project/`)

## Passo 0 — Ambiente (resumo)

```bash
cd tcc-project
docker compose up -d
cp .env.example .env
# editar .env
make install
python create_tables.py
```

## Passo 1 — Indexação

```bash
python indexar_dados.py
```

Ou via API Python (customizar tópicos):

```python
from app.infrastructure.db.connection import SessionLocal
from app.dados.squad_pt_indexer import index_squad_pt_contexts

with SessionLocal() as session:
    report = index_squad_pt_contexts(
        session,
        limit=50,
        chunk_size=300,
        chunk_overlap=50,
        clear_documents=True,
        tech_only=True,
    )
    print(report)
```

O benchmark (`run_benchmark_experiment`) usa `get_questions(..., tech_only=True)` por padrão — mesmo subconjunto temático.

Registrar no TCC: `rows_scanned`, `skipped_irrelevant`, `unique_contexts`, `chunks_total`, `TECH_TOPICS` em `squad_pt_filter.py`.

## Passo 2 — Benchmark completo

```python
import logging
from app.infrastructure.db.connection import SessionLocal
from app.application.use_cases.execute_rag import RAGScenario
from app.evaluation import run_benchmark_experiment

logging.basicConfig(level=logging.INFO)

with SessionLocal() as session:
    out = run_benchmark_experiment(
        session,
        limit=50,           # aumentar conforme orçamento API
        top_k=5,            # rag_optimized / rag_rerank (final)
        rerank_top_k=10,    # rag_rerank
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

with SessionLocal() as session:
    report = run_benchmark(
        session,
        limit=20,
        scenarios=(RAGScenario.RAG_RERANK,),
        top_k=3,
        rerank_top_k=10,
    )
```

## Passo 3 — Artefatos gerados

Diretório: `tcc-project/results/` (gitignored).

| Arquivo | Conteúdo |
|---------|----------|
| `benchmark_*.json` | `summaries` + `results` (cada pergunta) |
| `benchmark_*.csv` | Uma linha por (cenário, pergunta): EM, F1, latência, tokens, chunks |

### Colunas CSV (para gráficos)

- `scenario`
- `exact_match`, `f1`
- `latency_seconds`
- `tokens_used`
- `chunks_retrieved`
- `question`, `expected_answer`, `model_answer`

## Passo 4 — Análise sugerida

### Tabela resumo (copiar de `summaries` no JSON)

| Cenário | EM médio | F1 médio | Latência média (s) | Tokens médios | Chunks médios |
|---------|----------|----------|--------------------|---------------|---------------|
| llm | | | | | |
| rag_basic | | | | | |
| rag_optimized | | | | | |
| rag_rerank | | | | | |

### Gráficos recomendados para slides

1. **Barras agrupadas** — EM e F1 por cenário  
2. **Barras** — latência média por cenário  
3. **Barras** — tokens médios (custo)  
4. (Opcional) **Dispersão** — F1 vs latência por cenário  

Ferramentas: Excel, Google Sheets, Python (`pandas` + `matplotlib`), Power BI.

### Exemplo rápido com pandas

```python
import pandas as pd

df = pd.read_csv("results/benchmark_20250101_120000.csv")
summary = df.groupby("scenario").agg(
    em=("exact_match", "mean"),
    f1=("f1", "mean"),
    latency=("latency_seconds", "mean"),
    tokens=("tokens_used", lambda s: pd.to_numeric(s, errors="coerce").mean()),
    chunks=("chunks_retrieved", "mean"),
)
print(summary)
```

## Passo 5 — Teste manual via API (demonstração na banca)

```bash
make run
```

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"Onde nasceu Machado de Assis?","scenario":"rag_rerank","top_k":3,"rerank_top_k":10}'
```

Mostrar no Swagger: `http://127.0.0.1:8000/docs`

## Registro em `experiment_runs`

Cada chamada a `execute_rag` (incluindo via benchmark) grava:

- pergunta, cenário, parâmetros JSON  
- chunks recuperados, scores, prompt, resposta  
- latência, tokens  

Útil para **auditoria** e exemplos qualitativos no TCC (um caso de acerto e um de erro por cenário).

## Controle de variáveis (checklist para metodologia)

Documente explicitamente em cada rodada:

- [ ] `limit` de perguntas do SQuAD-pt (benchmark)  
- [ ] `limit` de contexts únicos na indexação  
- [ ] `tech_only=True` e `TECH_TOPICS` (`squad_pt_filter.py`)  
- [ ] `chunk_size` / `chunk_overlap`  
- [ ] `top_k`, `rerank_top_k`, `score_threshold`  
- [ ] `OPENAI_MODEL` e data da execução  
- [ ] Versão do código (commit git)

## Comparativo esperado (hipóteses — preencher com seus dados)

| Comparação | O que observar |
|------------|----------------|
| llm vs rag_basic | Ganho de EM/F1 com contexto |
| rag_basic vs rag_optimized | Efeito do prompt restritivo e k |
| rag_optimized vs rag_rerank | Ganho do rerank vs custo de latência |

## Troubleshooting

| Problema | Causa provável |
|----------|----------------|
| EM/F1 ≈ 0 em todos | Base não indexada ou pergunta fora do corpus indexado |
| Retrieval retorna pop culture | Reindexar com `tech_only=True`; rodar `python indexar_dados.py` |
| Erro 502 na API | OpenAI key / quota |
| Dimensão embedding | `VECTOR_DIMENSIONS` ≠ saída do modelo |
| Benchmark muito lento | `limit` alto + rerank + API OpenAI sequencial |
| OOM no rerank | `rerank_top_k` muito alto — reduzir |
