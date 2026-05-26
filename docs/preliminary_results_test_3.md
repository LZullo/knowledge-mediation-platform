# Resultados preliminares — Teste 3 (corpus refinado v3)

**Status:** protocolo e artefatos implementados; preencher `run_id` após executar o benchmark.  
**Corpus:** `wikipedia_benchmark_v3` (tier `refined`)  
**Benchmark:** `app/dados/benchmark_questions_v3.json` (18 perguntas: `core_5` + `extended`)  
**Comparativos históricos (não alterar):** Teste 1 `20260525_160434`, Teste 2 `20260526_020326`

---

## 1. Objetivo do Teste 3

Fortalecer **validade experimental** sem reinventar a arquitetura RAG:

- Curadoria real do corpus Wikipédia PT (validação prévia de títulos)
- Corpus complementar controlado para lacunas documentais (pgvector)
- Benchmark ampliado com subconjuntos rastreáveis
- Gabaritos objetivos semanticamente mais completos (sem inflar artificialmente)
- Controle de verbosidade do phi3 (`num_predict`, `repeat_penalty`, instrução 1–3 frases)

**Explicitamente fora de escopo:** novos embeddings, retrieval, rerank, fine-tuning, agentes.

---

## 2. Protocolo

| Parâmetro | Valor |
|-----------|--------|
| Cenários | `llm`, `rag_basic`, `rag_rerank` |
| Perguntas | 18 (`core_5` + `extended`) |
| Temperatura LLM | 0 |
| `num_predict` (Ollama) | 256 (configurável em `.env`) |
| `repeat_penalty` | 1.15 |
| Retrieval cumulativo | v1 + v2 + v3 |
| Export | `prompt_chars`, `response_chars`, `rerank_latency_seconds`, `subset`, `corpus_version` |

### Execução

```bash
python validate_wiki_topics_v3.py
python indexar_corpus.py --version wikipedia_benchmark_v3 --no-incremental
python run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v3
```

Artefatos esperados (novo `run_id`, **sem sobrescrever** Testes 1–2):

- `results/benchmark_<run_id>.json`
- `results/benchmark_<run_id>.csv`
- `results/corpus_report_wikipedia_benchmark_v3.json`
- `results/wiki_topic_validation_wikipedia_benchmark_v3.json`

Gráficos (após o benchmark):

```bash
python scripts/plot_benchmark_evolution.py ^
  --runs results/benchmark_20260525_160434.json results/benchmark_20260526_020326.json results/benchmark_<run_id>.json ^
  --labels v1 v2 v3
```

---

## 3. Tabela comparativa (preencher após execução)

| Versão | Corpus | Perguntas | Mean F1 (`rag_basic`) | Mean F1 (`rag_rerank`) | Mean latência (`rag_rerank`) |
|--------|--------|-----------|------------------------|-------------------------|------------------------------|
| v1 (Teste 1) | `wikipedia_benchmark_v1` | 5 | 0,1116 | 0,1317 | ver JSON `20260525_160434` |
| v2 (Teste 2) | `wikipedia_benchmark_v2` | 5 | 0,1188 | 0,1216 | ver JSON `20260526_020326` |
| v3 (Teste 3) | `wikipedia_benchmark_v3` | 18 | _preencher_ | _preencher_ | _preencher_ |

**Subconjunto `core_5` (Teste 3):** calcular médias filtrando `subset=core_5` no CSV — útil para narrativa de evolução, mas **não** comparar F1 diretamente com Teste 1/2 se os gabaritos de `core_5` foram refinados.

---

## 4. O que mudou em relação à v2

| Fator | v2 | v3 |
|-------|----|----|
| Validação de títulos | Não | Sim (`wiki_topic_validation_*.json`) |
| Tópicos indexados | 2/12 na rodada incremental | Curadoria + títulos válidos |
| pgvector | Sem cobertura | `docs/custom_corpus/pgvector.md` (complementar) |
| Benchmark | 5 perguntas | 18 (`core_5` + `extended`) |
| Gabaritos | Ultra-curtos | Objetivos, 1 frase completa |
| phi3 | Sem limite de tokens | `num_predict` + anti-repetição |

---

## 5. Análise qualitativa (roteiro)

Após o benchmark, documentar exemplos para:

| Tema | Cenários a contrastar | Hipótese |
|------|----------------------|----------|
| PostgreSQL | `llm` vs `rag_basic` vs `rag_rerank` | RAG ancora em corpus v1 |
| pgvector | idem | Complementar habilita resposta factual |
| Embeddings / busca semântica | perguntas `extended` | Cobertura v3 + retrieval |
| REST / Docker | `core_5` | Comparabilidade histórica de pergunta |

Incluir trechos de resposta e `chunks_retrieved` / `prompt_chars` do CSV exportado.

---

## 6. Rerank: custo vs benefício (Teste 3)

Discutir com base em `rerank_latency_seconds` e F1 por cenário:

- Ganho marginal de F1 em `rag_rerank` vs `rag_basic`
- Custo de latência (rerank + geração)
- Dependência de candidatos relevantes no pool pgvector

---

## 7. Limitações epistemológicas (honestas)

1. **Gabaritos refinados** podem elevar F1 sem melhorar o modelo.
2. **Corpus complementar** é decisão metodológica explícita — não é “descoberta” na Wikipédia.
3. **18 perguntas** alteram médias globais em relação aos Testes 1–2 (5 perguntas).
4. **EM** provavelmente permanece próximo de zero com phi3.
5. **Retrieval cumulativo** confunde efeito “versão v3” com massa total do índice.

---

## 8. Preservação histórica

Os ficheiros abaixo **não devem ser modificados**:

- `results/benchmark_20260525_160434.json` / `.csv`
- `results/benchmark_20260526_020326.json` / `.csv`
- `docs/preliminary_results_test_1.md`
- `docs/preliminary_results_test_2.md`

---

_Atualizar esta seção com métricas reais assim que `run_id` do Teste 3 estiver disponível. Não estimar valores._
