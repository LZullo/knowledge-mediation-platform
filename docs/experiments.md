# Experimentos e análise de resultados

Guia operacional para **executar** benchmarks e exportar artefatos. **Métricas finais, figuras e discussão:** [final_experimental_analysis.md](final_experimental_analysis.md) (fonte canônica). Navegação: [documentation_index.md](documentation_index.md).

## Pré-condições

- [ ] `docker compose up -d` (PostgreSQL + pgvector na porta 5433)  
- [ ] `.env` na raiz configurado (`DATABASE_URL`, `LLM_PROVIDER`, `OLLAMA_*` ou `OPENAI_API_KEY`)  
- [ ] Ollama rodando e modelo instalado (`ollama pull phi3`) se `LLM_PROVIDER=ollama`  
- [ ] Tabelas criadas (`python create_tables.py`)  
- [ ] Corpus indexado (`python indexar_dados.py`)  
- [ ] Dependências instaladas (`make install` ou `pip install -r requirements.txt`)

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

Perguntas do benchmark final (v2): `app/dados/benchmark_questions_v2_final.json` (carregadas por `benchmark_loader.py` e passadas explicitamente via `questions_path`).

Registrar no TCC: tópicos em `WIKI_TOPICS`, `chunk_size`/`chunk_overlap`, campos de `WikipediaIndexingReport`.

## Passo 2 — Benchmark completo

**Com Ollama (sem OpenAI)** — script pronto:

```bash
# .env: LLM_PROVIDER=ollama, OLLAMA_MODEL=phi3, LLM_TEMPERATURE=0
python run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v2 --questions-path app/dados/benchmark_questions_v2_final.json
```

**Via Python** (mesmo motor; respeita `LLM_PROVIDER`):

```python
import logging
from app.infrastructure.db.connection import SessionLocal
from app.application.use_cases.execute_rag import RAGScenario
from app.evaluation import run_benchmark_experiment

logging.basicConfig(level=logging.INFO)

with SessionLocal() as session:
    out = run_benchmark_experiment(
        session,
        corpus_version="wikipedia_benchmark_v2",
        limit=None,         # todas as perguntas do JSON
        questions_path="app/dados/benchmark_questions_v2_final.json",
        top_k=5,            # rag_basic / rag_optimized / rag_rerank (top_k final)
        rerank_top_k=10,    # rag_rerank
        commit_each=True,
    )

for s in out.report.summaries:
    print(s)
```

Cenários padrão: `llm`, `rag_basic`, `rag_optimized`, `rag_rerank`. A geração usa `get_generation_strategy()` (`OpenAIGenerationStrategy` ou `OllamaGenerationStrategy`).

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

- [ ] `limit` de perguntas do benchmark JSON  
- [ ] Tópicos Wikipédia indexados (`WIKI_TOPICS`)  
- [ ] `chunk_size` / `chunk_overlap` na indexação  
- [ ] `top_k`, `rerank_top_k`, `score_threshold`  
- [ ] `LLM_PROVIDER`, `OLLAMA_MODEL` ou `OPENAI_MODEL` e data da execução  
- [ ] Versão do código (commit git)

## Hipóteses vs resultados observados

| Comparação | Hipótese | Resultado (benchmark final v3) |
|------------|----------|--------------------------------|
| `llm` vs `rag_basic` | RAG eleva F1 com contexto adequado | F1 0,189 → **0,239** (18 perg.) — ver [final_experimental_analysis.md](final_experimental_analysis.md) §4 |
| `rag_basic` vs `rag_rerank` | Rerank melhora precisão do top-k | F1 médio **inferior** com maior latência neste corpus — §4.1 |
| Evolução v1→v3 | Cobertura documental afeta RAG | Tendência de ganho; v3 não comparável 1:1 (N perguntas e gabaritos) — §4.3, §4.6 |

---

## Teste 1 histórico (legacy) — rastreabilidade

| Atributo | Valor |
|----------|-------|
| `run_id` | `20260525_160434` |
| Artefatos | `results/benchmark_20260525_160434.json`, `.csv` |
| Campo legado | `corpus = "wikipedia_benchmark"` |
| Equivalência | `corpus_version = "wikipedia_benchmark_v1"` |

Os ficheiros históricos foram **preservados sem alteração estrutural** das métricas; não houve reprocessamento retroativo. A preservação de resultados experimentais anteriores sustenta rastreabilidade e validade comparativa longitudinal — prática recomendada quando o protocolo evolui (versionamento de corpus, refinamento de gabaritos) sem invalidar a série documentada.

Documentação: [preliminary_results_test_1.md](preliminary_results_test_1.md), [final_experimental_analysis.md](final_experimental_analysis.md) (secção 3).

---

## Comparação Teste 1 (v1) vs Teste 2 (v2) — resultados registrados

Artefatos oficiais (preservar sem reescrita):

| Teste | `run_id` | Corpus | JSON |
|-------|----------|--------|------|
| Teste 1 | `20260525_160434` | `wikipedia_benchmark_v1` (rótulo legado: `wikipedia_benchmark`) | `results/benchmark_20260525_160434.json` |
| Teste 2 | `20260526_020326` | `wikipedia_benchmark_v2` | `results/benchmark_20260526_020326.json` |
| Teste 3 (final) | `20260526_171347` | `wikipedia_benchmark_v3` | `results/benchmark_20260526_171347.json` |

### Tabela comparativa — F1 e latência médias

| Cenário | v1 F1 | v2 F1 | Δ F1 | v1 lat. (s) | v2 lat. (s) | Δ lat. (s) |
|---------|-------|-------|------|-------------|-------------|------------|
| `llm` | 0,0301 | 0,0301 | 0,0000 | 120,21 | 152,43 | +32,22 |
| `rag_basic` | 0,1116 | 0,1188 | +0,0072 | 74,66 | 170,70 | +96,04 |
| `rag_rerank` | 0,1317 | 0,1216 | −0,0100 | 133,16 | 435,74 | +302,58 |

EM médio = **0** em todos os cenários e em ambos os testes.

Análise detalhada: [preliminary_results_test_2.md](preliminary_results_test_2.md).

### Observações sobre latência

1. **Teste 2** apresentou latências médias superiores em todos os cenários RAG e em `llm`, em ambiente Ollama/phi3 com índice maior (446 documentos).
2. **Outlier crítico (Teste 2, `rag_rerank`, pergunta REST):** `latency_seconds` ≈ **1272 s**, com repetição textual na resposta e F1 ≈ **0,004**. Este ponto distorce a média de `rag_rerank` no Teste 2; reportar mediana ou média sem outlier em análises futuras.
3. **Decomposição:** em `rag_rerank` v2, `mean_generation_latency_seconds` ≈ **415,5 s** vs. **123,3 s** no Teste 1 — o custo de geração (incluindo patologia de repetição) supera o de retrieval (`mean_retrieval_latency_seconds` ≈ 14,4 s).

### Análise de retrieval

| Indicador | Teste 1 | Teste 2 |
|-----------|---------|---------|
| `mean_chunks_retrieved` (`rag_basic`) | 3,0 | 5,0 |
| `mean_chunks_retrieved` (`rag_rerank`) | 5,0 | 5,0 |
| Corpus no benchmark | v1 (411 docs no relatório v1) | v2 cumulativo (446 docs) |

- Ganho de F1 em *machine learning* com `rag_basic` (0,154 → 0,286) co-ocorre com **cinco** chunks recuperados e maior tempo de busca vetorial.
- **pgvector:** ausência de artigo dedicado no índice; F1 de `rag_basic` **reduziu** (0,133 → 0,069) — a expansão não corrigiu a lacuna.
- **PostgreSQL:** F1 de `rag_rerank` estável em **0,296** — retrieval já adequado na v1.

### Discussão sobre reranking

| Aspecto | Teste 1 | Teste 2 |
|---------|---------|---------|
| F1 médio `rag_rerank` vs `rag_basic` | Rerank **superior** (+18% relativo no F1 médio) | Rerank **inferior** no agregado (−2,5% relativo vs. `rag_basic`) |
| Melhor caso (PostgreSQL) | F1 = 0,296 | F1 = 0,296 |
| Pior degradação | Docker: rerank < basic | REST: F1 ≈ 0,004 (falha generativa) |

**Conclusão operacional:** o reranking permanece útil quando candidatos relevantes existem no pool expandido, mas no Teste 2 o benefício médio foi ofuscado por (i) instabilidade do phi3 em respostas longas e (ii) cobertura ainda insuficiente em tópicos-alvo (pgvector). Não reinterpretar a queda do F1 médio de `rag_rerank` como falha do CrossEncoder sem examinar a pergunta REST.

### Documentação relacionada

- [preliminary_results_test_1.md](preliminary_results_test_1.md)
- [preliminary_results_test_2.md](preliminary_results_test_2.md)
- [discussion_preliminary_findings.md](discussion_preliminary_findings.md)
- [corpus_evolution.md](corpus_evolution.md)

---

## Teste 3 — corpus refinado (v3)

**`run_id`:** `20260526_171347` | **Métricas e figuras:** [final_experimental_analysis.md](final_experimental_analysis.md) §4–4.6

### Passo 1 — Validar títulos Wikipédia

```bash
python validate_wiki_topics_v3.py
```

Saída: `results/wiki_topic_validation_wikipedia_benchmark_v3.json`

### Passo 2 — Indexar v3

```bash
python indexar_corpus.py --version wikipedia_benchmark_v3 --no-incremental
```

Saída: `results/corpus_report_wikipedia_benchmark_v3.json` (inclui `custom_corpus_indexed`)

### Passo 3 — Benchmark

```bash
python run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v3
```

Perguntas: `app/dados/benchmark_questions_v3.json` (18 itens; campos `id`, `subset`)

Export ampliado no CSV: `prompt_chars`, `response_chars`, `rerank_latency_seconds`, `subset`, `question_id`

### Passo 4 — Gráficos finais

```bash
python scripts/plot_benchmark_evolution.py ^
  --runs results/benchmark_20260525_160434.json results/benchmark_20260526_020326.json results/benchmark_20260526_171347.json ^
  --labels v1 v2 v3
```

Saída em `results/plots/`: `f1_by_scenario.png`, `latency_by_scenario.png`, `evolution_f1_v1_v2_v3.png`, `tradeoff_f1_latency_rerank.png` (descrição em [final_experimental_analysis.md](final_experimental_analysis.md) §4.5).

### Comparabilidade (importante)

| Comparação | Permitido? |
|------------|------------|
| Teste 3 `core_5` vs Teste 1/2 (mesma pergunta) | Qualitativo sim; **F1 direto não**, se gabarito mudou |
| Teste 3 global (18 perg.) vs Teste 1/2 (5 perg.) | Não sem ponderação |
| Evolução corpus v1→v2→v3 | Sim via `corpus_version` e relatórios JSON |

Documentação: [preliminary_results_test_3.md](preliminary_results_test_3.md), [final_experimental_analysis.md](final_experimental_analysis.md)

### Passo 5 — Validação qualitativa do retrieval

```bash
python validar_retrieval.py
```

Saída: `results/retrieval_validation_wikipedia_benchmark_v3.txt`

---

## Subconjuntos do Benchmark

No Teste 3 (v3), o benchmark foi ampliado preservando um subconjunto histórico para manter comparabilidade e, simultaneamente, introduzir um conjunto complementar voltado à análise experimental.

O arquivo `app/dados/benchmark_questions_v3.json` separa as perguntas por `subset` em:

- `core_5`:
  - conjunto histórico com as **5 perguntas** preservadas dos testes v1 e v2;
  - utilizado como base de comparabilidade quantitativa controlada.

- `extended`:
  - subset complementar introduzido na v3 com **13 perguntas adicionais**;
  - inclui perguntas relacionadas a embeddings, recuperação da informação, bancos vetoriais, busca semântica e sistemas RAG;
  - utilizado principalmente para avaliação qualitativa e para ampliação temática com maior diversidade de cenários.

### Observação metodológica

Alterações no benchmark podem afetar a comparabilidade direta de métricas:

- quando perguntas mudam ou são refinadas;
- quando gabaritos passam por ajustes;
- quando a cobertura temática e a distribuição de dificuldades se alteram.

Por essa razão, comparações quantitativas devem privilegiar o subset `core_5` (quando o objetivo é rastrear efeitos ao longo do histórico), enquanto resultados envolvendo `extended` devem ser interpretados como robustez experimental e ampliação metodológica, evitando inferências diretas entre populações diferentes de perguntas.

| Subset   | Objetivo                                  |
| -------- | ----------------------------------------- |
| core_5   | comparabilidade histórica                 |
| extended | robustez qualitativa e ampliação temática |

---

## Análise interpretativa (Teste 3)

Validação qualitativa do retrieval, casos observados (LangChain, bancos vetoriais, pgvector, embeddings), discussão, limitações e conclusão experimental estão consolidados em **[final_experimental_analysis.md](final_experimental_analysis.md)** (§5–9). Este ficheiro cobre apenas execução e comparação histórica Testes 1–2.

---

## Troubleshooting

| Problema | Causa provável |
|----------|----------------|
| EM/F1 ≈ 0 em todos | Base não indexada ou pergunta fora do corpus indexado |
| Retrieval retorna pop culture | Reindexar com `tech_only=True`; rodar `python indexar_dados.py` |
| Erro 502 na API | Ollama parado (`ollama serve`) ou `OPENAI_API_KEY` inválida |
| Ollama não responde | Conferir `OLLAMA_BASE_URL`; `curl http://localhost:11434/api/tags` |
| Dimensão embedding | `VECTOR_DIMENSIONS` ≠ saída do modelo |
| Benchmark muito lento | Muitas perguntas + rerank + phi3 local (CPU/GPU) |
| OOM no rerank | `rerank_top_k` muito alto — reduzir |
