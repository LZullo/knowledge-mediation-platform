# Índice mestre da documentação experimental

Mapa de navegação acadêmica do TCC — **arquitetura, metodologia, benchmarks e resultados** do pipeline RAG (PostgreSQL + pgvector + Ollama/phi3). Use este documento como ponto de partida para leitura, escrita da dissertação e rastreabilidade entre testes.

**Documento principal recomendado para o capítulo experimental:** [final_experimental_analysis.md](final_experimental_analysis.md)  
**Métricas e figuras canônicas:** secção 4 e `results/plots/` (não duplicar tabelas noutros `.md`)

**Índice operacional da pasta `docs/`:** [README.md](README.md) (reprodução local, Docker, scripts)

---

## Ordem recomendada de leitura

| Ordem | Documento | Papel na leitura |
|-------|-----------|------------------|
| 1 | [README.md](README.md) | Visão geral, pré-requisitos, fluxo local |
| 2 | [architecture.md](architecture.md) | Componentes, camadas, cenários RAG |
| 3 | [methodology.md](methodology.md) | Corpus, pipeline, métricas, protocolo |
| 4 | [corpus_evolution.md](corpus_evolution.md) | Versionamento v1→v2→v3, deduplicação |
| 5 | [experiments.md](experiments.md) | Execução de benchmarks, tabelas, troubleshooting |
| 6 | [final_experimental_analysis.md](final_experimental_analysis.md) | **Consolidação final** — resultados, qualitativa, discussão, conclusão |
| — | [preliminary_report_esalq.md](preliminary_report_esalq.md) | **Entrega ESALQ** — relatório preliminar em formato acadêmico |
| 7 | [limitations.md](limitations.md) | Limitações e trabalhos futuros |
| 8 | [decisions.md](decisions.md) | Registro de decisões arquiteturais (defesa) |

**Leitura complementar (histórico ou apoio):**

| Documento | Quando ler |
|-----------|------------|
| [preliminary_results_test_1.md](preliminary_results_test_1.md) | Detalhe do Teste 1 (v1) |
| [preliminary_results_test_2.md](preliminary_results_test_2.md) | Detalhe do Teste 2 (v2) |
| [preliminary_results_test_3.md](preliminary_results_test_3.md) | Resumo executivo do Teste 3 |
| [discussion_preliminary_findings.md](discussion_preliminary_findings.md) | Discussão Testes 1 e 2 (pré-consolidação) |
| [corpus_versions.md](corpus_versions.md) | Estatísticas por versão do corpus |
| [custom_corpus/pgvector.md](custom_corpus/pgvector.md) | Fonte complementar documentada (pgvector) |
| [diagrams/](diagrams/) | Figuras Mermaid para slides e texto |

---

## Estrutura recomendada para o TCC

Ordem lógica sugerida para o texto da dissertação, com mapeamento aos artefatos do repositório.

| Capítulo / seção do TCC | Conteúdo | Documento(s) principal(is) |
|-------------------------|----------|------------------------------|
| 1. Introdução | Problema, objetivos, contribuições | Texto da dissertação; visão em [README.md](README.md) |
| 2. Fundamentação teórica | RAG, embeddings, recuperação, avaliação QA | Literatura externa; métricas em [methodology.md](methodology.md) §5 |
| 3. Arquitetura proposta | Camadas, Strategy Pattern, tecnologias | [architecture.md](architecture.md), [diagrams/architecture.mmd](diagrams/architecture.mmd) |
| 4. Pipeline RAG | Ingestão, retrieval, rerank, geração | [architecture.md](architecture.md), [methodology.md](methodology.md) §2–4 |
| 5. Corpus experimental | Wikipédia PT, versionamento, complementar | [corpus_evolution.md](corpus_evolution.md), [corpus_versions.md](corpus_versions.md) |
| 6. Benchmark e metodologia | Cenários, perguntas, protocolo, métricas | [methodology.md](methodology.md), [experiments.md](experiments.md) |
| 7. Resultados experimentais | Tabelas, evolução v1–v3, casos | [final_experimental_analysis.md](final_experimental_analysis.md), `results/benchmark_*.csv` |
| 8. Discussão | Interpretação, tradeoffs, cobertura × desempenho | [final_experimental_analysis.md](final_experimental_analysis.md) §7 |
| 9. Limitações | Ameaças à validade, generalização | [limitations.md](limitations.md), [final_experimental_analysis.md](final_experimental_analysis.md) §8 |
| 10. Conclusão | Síntese, viabilidade, continuidade | [final_experimental_analysis.md](final_experimental_analysis.md) §9 |
| Relatório preliminar ESALQ | Resumo, intro, métodos, resultados, considerações | [preliminary_report_esalq.md](preliminary_report_esalq.md) |

---

## Evolução experimental

Três rodadas de benchmark preservadas integralmente. A recuperação na v2 e v3 consulta o índice **cumulativo** (versões anteriores permanecem no banco).

### Teste 1 — baseline inicial

- **Objetivo:** validar o pipeline RAG e estabelecer linha de base comparativa.
- **Corpus:** `wikipedia_benchmark_v1` (rótulo legado nos artefatos: `wikipedia_benchmark`).
- **Benchmark:** 5 perguntas; cenários `llm`, `rag_basic`, `rag_rerank`.
- **`run_id`:** `20260525_160434`
- **Status:** histórico — preservar sem reprocessamento.

### Teste 2 — expansão incremental

- **Objetivo:** ampliar cobertura temática (embeddings, RI, LangChain) com indexação incremental sobre v1.
- **Corpus:** `wikipedia_benchmark_v2` (índice cumulativo ≈ 446 chunks na rodada documentada).
- **Benchmark:** 5 perguntas (mesmo conjunto base do Teste 1).
- **`run_id`:** `20260526_020326`
- **Status:** histórico — validação intermediária; discussão em [discussion_preliminary_findings.md](discussion_preliminary_findings.md).

### Teste 3 — consolidação final

- **Objetivo:** refinamento metodológico (curadoria, validação de títulos, corpus complementar pgvector, benchmark ampliado, controle de geração).
- **Corpus:** `wikipedia_benchmark_v3` (rodada v3: 155 chunks; índice consultado no benchmark: 601 chunks v1+v2+v3).
- **Benchmark:** 18 perguntas (`core_5` + `extended`); validação qualitativa do retrieval; reranking.
- **`run_id`:** `20260526_171347`
- **Status:** **referência principal** para resultados e discussão final.

### Tabela resumo dos testes

| Teste | Objetivo | Corpus | Perguntas | `run_id` | Documentação | Status |
|-------|----------|--------|-----------|----------|--------------|--------|
| 1 | Baseline inicial | `wikipedia_benchmark_v1` | 5 | `20260525_160434` | [preliminary_results_test_1.md](preliminary_results_test_1.md) | Histórico |
| 2 | Expansão incremental | `wikipedia_benchmark_v2` | 5 | `20260526_020326` | [preliminary_results_test_2.md](preliminary_results_test_2.md) | Histórico |
| 3 | Consolidação final | `wikipedia_benchmark_v3` | 18 | `20260526_171347` | [final_experimental_analysis.md](final_experimental_analysis.md) | **Final** |

**Equivalência legada:** em `results/benchmark_20260525_160434.*`, o campo `corpus = "wikipedia_benchmark"` ≡ `corpus_version = "wikipedia_benchmark_v1"`.

---

## Mapa de documentos (`docs/`)

| Arquivo | Finalidade | Tipo | Uso no TCC |
|---------|------------|------|------------|
| [documentation_index.md](documentation_index.md) | Índice mestre e navegação | Índice | Ponto de partida |
| [final_experimental_analysis.md](final_experimental_analysis.md) | Consolidação experimental final | **Principal** | Cap. resultados, discussão, conclusão experimental |
| [preliminary_report_esalq.md](preliminary_report_esalq.md) | Relatório preliminar (formato ESALQ) | **Entrega** | Submissão orientador / MBA |
| [methodology.md](methodology.md) | Metodologia, métricas, protocolo | **Principal** | Cap. metodologia |
| [architecture.md](architecture.md) | Arquitetura e componentes | **Principal** | Cap. arquitetura |
| [experiments.md](experiments.md) | Execução, tabelas, validação qualitativa | **Principal** | Cap. experimentos (operacional) |
| [corpus_evolution.md](corpus_evolution.md) | Evolução v1→v2→v3, deduplicação | Apoio | Cap. corpus / dados |
| [corpus_versions.md](corpus_versions.md) | Estatísticas por versão | Apoio | Tabelas de cobertura |
| [limitations.md](limitations.md) | Limitações e futuro | Apoio | Cap. limitações |
| [decisions.md](decisions.md) | ADRs e justificativas | Apoio | Defesa / apêndice |
| [discussion_preliminary_findings.md](discussion_preliminary_findings.md) | Discussão Testes 1–2 | Histórico | Contexto; ver análise final |
| [preliminary_results_test_1.md](preliminary_results_test_1.md) | Resultados Teste 1 | Histórico | Detalhe v1 |
| [preliminary_results_test_2.md](preliminary_results_test_2.md) | Resultados Teste 2 | Histórico | Detalhe v2 |
| [preliminary_results_test_3.md](preliminary_results_test_3.md) | Atalhos Teste 3 (sem métricas duplicadas) | Apoio | Links → análise final |
| [README.md](README.md) | Guia técnico e reprodução | Operacional | Apêndice / replicação |
| [custom_corpus/pgvector.md](custom_corpus/pgvector.md) | Texto fonte complementar | Fonte | Metodologia corpus curado |
| [diagrams/*.mmd](diagrams/) | Diagramas Mermaid | Figuras | Slides e capítulo |

---

## Histórico vs consolidação final

| Categoria | O que inclui | Regra de uso |
|-----------|--------------|--------------|
| **Consolidação final** | [final_experimental_analysis.md](final_experimental_analysis.md), benchmark `20260526_171347`, validação `retrieval_validation_wikipedia_benchmark_v3.txt` | **Referência principal** para capítulo experimental |
| **Histórico (preservar)** | Testes 1 e 2 (`20260525_160434`, `20260526_020326`), preliminares 1–2, discussão preliminar | Comparabilidade longitudinal; **não** sobrescrever métricas |
| **Apoio operacional** | [README.md](README.md), [experiments.md](experiments.md) (troubleshooting) | Reprodução e banca |
| **Fonte de dados** | `app/dados/benchmark_questions_v3.json`, `corpus_registry.py` | Citação metodológica; não substituir análise narrativa |

**Não reprocessar** artefatos em `results/benchmark_*.json` / `.csv` dos Testes 1 e 2.

---

## Artefatos experimentais (`results/`)

Diretório de saída das execuções (geralmente gitignored). Convenção atual: ficheiros na **raiz** de `results/` com prefixos descritivos. Subpastas abaixo são **recomendação** para organização futura de gráficos — **sem mover** ficheiros históricos existentes.

### Inventário atual (raiz `results/`)

| Arquivo | Conteúdo | Teste / versão |
|---------|----------|----------------|
| `benchmark_20260525_160434.json` | Métricas completas + respostas | Teste 1 (v1) |
| `benchmark_20260525_160434.csv` | Tabela por cenário × pergunta | Teste 1 |
| `benchmark_20260526_020326.json` | Métricas completas + respostas | Teste 2 (v2) |
| `benchmark_20260526_020326.csv` | Tabela quantitativa | Teste 2 |
| `benchmark_20260526_171347.json` | Métricas completas + respostas | **Teste 3 (final)** |
| `benchmark_20260526_171347.csv` | Tabela quantitativa | **Teste 3** |
| `corpus_report_wikipedia_benchmark_v1.json` | Estatísticas de indexação v1 | Corpus v1 |
| `corpus_report_wikipedia_benchmark_v2.json` | Estatísticas de indexação v2 | Corpus v2 |
| `corpus_report_wikipedia_benchmark_v3.json` | Estatísticas de indexação v3 | Corpus v3 |
| `wiki_topic_validation_wikipedia_benchmark_v3.json` | Validação de títulos MediaWiki | Pré-Teste 3 |
| `retrieval_validation_wikipedia_benchmark_v3.txt` | Inspeção qualitativa top-k | Teste 3 |

### Tabela por tipo de artefato

| Padrão / pasta | Conteúdo | Uso no TCC |
|----------------|----------|------------|
| `results/benchmark_<run_id>.json` | Summaries, resultados por pergunta, metadados de corpus/modelos | Fonte primária; auditoria |
| `results/benchmark_<run_id>.csv` | EM, F1, latência, chunks, respostas | **Tabelas e gráficos** |
| `results/corpus_report_*.json` | Chunks, tópicos, deduplicação | Metodologia corpus |
| `results/wiki_topic_validation_*.json` | Títulos válidos / redirects | Metodologia v3 |
| `results/retrieval_validation_*.txt` | Chunks recuperados (qualitativa) | Discussão retrieval |
| `results/plots/*.png` | 4 gráficos finais (F1, latência, evolução, tradeoff) | Figuras da dissertação |
| `experiment_runs` (PostgreSQL) | Logs por execução via API/benchmark | Exemplos qualitativos na banca |

### Relação `run_id` → documentação

| `run_id` | JSON / CSV | Documento narrativo |
|----------|------------|---------------------|
| `20260525_160434` | `benchmark_20260525_160434.*` | [preliminary_results_test_1.md](preliminary_results_test_1.md) |
| `20260526_020326` | `benchmark_20260526_020326.*` | [preliminary_results_test_2.md](preliminary_results_test_2.md) |
| `20260526_171347` | `benchmark_20260526_171347.*` | [final_experimental_analysis.md](final_experimental_analysis.md) |

---

## Evidências experimentais (figuras, tabelas, gráficos)

### Onde obter dados para tabelas

- **Agregados por cenário:** campo `summaries` em `results/benchmark_<run_id>.json`
- **Detalhe por pergunta:** `results/benchmark_<run_id>.csv` ou secção `results` no JSON
- **Tabelas canônicas:** [final_experimental_analysis.md](final_experimental_analysis.md) §4 (incl. tabela mestre §4.6)
- **Operação / Testes 1–2:** [experiments.md](experiments.md)

### Gráficos finais (`results/plots/`)

| Arquivo | Descrição |
|---------|-----------|
| `f1_by_scenario.png` | F1 médio por cenário × v1/v2/v3 |
| `latency_by_scenario.png` | Latência média por cenário × v1/v2/v3 |
| `evolution_f1_v1_v2_v3.png` | Evolução de F1 por cenário |
| `tradeoff_f1_latency_rerank.png` | Tradeoff F1 × latência (`rag_rerank`) |

Regenerar: `python scripts/plot_benchmark_evolution.py --runs results/benchmark_20260525_160434.json results/benchmark_20260526_020326.json results/benchmark_20260526_171347.json --labels v1 v2 v3`  
Detalhes: [final_experimental_analysis.md](final_experimental_analysis.md) §4.5.

### Convenção de nomenclatura para figuras do TCC

| Elemento | Convenção sugerida | Exemplo |
|----------|-------------------|---------|
| Figura | `Figura N – <descrição> (run_id <id>)` | Figura 3 – F1 médio por cenário (run_id 20260526_171347) |
| Tabela | `Tabela N – <métrica>, Teste <1\|2\|3>` | Tabela 2 – Comparação v1/v2/v3, F1 rag_basic |
| Arquivo PNG | `fig_<tema>_<run_id_curto>.png` | `fig_f1_scenarios_171347.png` |

Sempre citar no texto: **versão do corpus**, **número de perguntas** e **`run_id`** quando reportar métricas.

### Dados de benchmark (app)

| Recurso | Localização |
|---------|-------------|
| Perguntas Teste 3 (18) | `app/dados/benchmark_questions_v3.json` |
| Perguntas Testes 1–2 (5) | `app/dados/benchmark_questions_v2_final.json` |
| Registro de versões de corpus | `app/dados/corpus_registry.py` |

---

## Estrutura sugerida para organização futura (opcional)

Organização **lógica** para novos artefatos — **não** implica mover ficheiros já gerados:

```text
results/
├── test_1_v1/          # cópias ou atalhos documentais (opcional)
├── test_2_v2/
├── test_3_v3/
├── plots/
└── retrieval_validation/
```

A rastreabilidade oficial permanece pelos nomes `benchmark_<run_id>.*` na raiz de `results/`.

---

## Estado atual do projeto

| Dimensão | Situação |
|----------|----------|
| Arquitetura | Estabilizada (API, pipeline RAG, strategies, pgvector) |
| Pipeline experimental | Finalizado (Testes 1–3 executados e documentados) |
| Benchmark | Consolidado no Teste 3 (`20260526_171347`) |
| Figuras | Geradas em `results/plots/` (4 PNG) |
| Corpus | Versionado v1/v2/v3; complementar pgvector indexado |
| Foco atual | Redação do capítulo experimental a partir de [final_experimental_analysis.md](final_experimental_analysis.md) |

---

## Links rápidos

- **Relatório preliminar ESALQ:** [preliminary_report_esalq.md](preliminary_report_esalq.md)
- **Capítulo experimental (técnico):** [final_experimental_analysis.md](final_experimental_analysis.md)
- **Reproduzir experimento:** [README.md](README.md) → [experiments.md](experiments.md)
- **Defender decisões técnicas:** [decisions.md](decisions.md) + [architecture.md](architecture.md)
- **Honestidade metodológica:** [limitations.md](limitations.md)

---

_Última consolidação documental alinhada ao benchmark final `20260526_171347`. Preservar artefatos históricos; atualizar este índice ao adicionar novas rodadas experimentais._
