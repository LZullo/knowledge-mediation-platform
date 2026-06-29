# Análise experimental final — pipeline RAG (benchmark v3)

> Navegação: [documentation_index.md](documentation_index.md) | Relatório preliminar ESALQ: [preliminary_report_esalq.md](preliminary_report_esalq.md)

Documento consolidado para o capítulo experimental do TCC (MBA em Engenharia de Software). Integra metodologia, evolução do corpus (v1 → v2 → v3), resultados quantitativos do benchmark final, validação qualitativa do retrieval, discussão interpretativa, limitações e conclusão — **sem substituir** artefatos históricos em `results/` nem documentação preliminar dos Testes 1 e 2.

**Benchmark final (Teste 3):** `run_id` = `20260526_171347`  
**Artefatos:** `results/benchmark_20260526_171347.json`, `results/benchmark_20260526_171347.csv`  
**Validação de retrieval:** `results/retrieval_validation_wikipedia_benchmark_v3.txt`  
**Relatório de corpus v3:** `results/corpus_report_wikipedia_benchmark_v3.json`

Documentação complementar: [methodology.md](methodology.md) (protocolo), [experiments.md](experiments.md) (reprodução e Testes 1–2), [documentation_index.md](documentation_index.md) (navegação).

> **Fonte canônica de métricas:** as tabelas desta secção 4 prevalecem sobre resumos em outros ficheiros. Figuras consolidadas: secção 4.5 e `results/plots/`.

---

## 1. Metodologia experimental (síntese)

O experimento compara três cenários de inferência sobre o mesmo conjunto de perguntas:

| Cenário | Retrieval | Reranking | Papel |
|---------|-----------|-----------|-------|
| `llm` | — | — | Baseline paramétrico (phi3 via Ollama) |
| `rag_basic` | pgvector (top-k=5) | — | RAG mínimo viável |
| `rag_rerank` | pgvector (pool expandido) + CrossEncoder | Sim | Two-stage retrieval |

**Modelos fixos na rodada final:** embedding `sentence-transformers/all-MiniLM-L6-v2`; rerank `cross-encoder/ms-marco-MiniLM-L-6-v2`; LLM `phi3` (`LLM_TEMPERATURE=0`). **Métricas:** Exact Match (EM) e F1 token-level (normalização estilo SQuAD); latência end-to-end e decomposição retrieval/geração/rerank quando aplicável.

**Benchmark v3:** `app/dados/benchmark_questions_v3.json` — 18 perguntas em subconjuntos `core_5` (5 perguntas históricas) e `extended` (13 perguntas novas). O retrieval na v3 consulta documentos cumulativos das versões `wikipedia_benchmark_v1`, `v2` e `v3`.

---

## 2. Evolução do corpus (v1 → v2 → v3)

### 2.1 Objetivos e diferenças por versão

| Versão | Tier | Objetivo principal | Diferença em relação à anterior |
|--------|------|-------------------|--------------------------------|
| `wikipedia_benchmark_v1` | inicial | Estabelecer baseline documental e validar o pipeline (Teste 1) | 9 tópicos Wikipédia PT; chunk 500/100; 411 chunks |
| `wikipedia_benchmark_v2` | expandido | Ampliar cobertura temática (embeddings, RI, LangChain) de forma incremental | +35 chunks na rodada documentada; indexação incremental sobre v1; 2/12 tópicos novos efetivamente indexados |
| `wikipedia_benchmark_v3` | refinado | Curadoria, validação de títulos, deduplicação e corpus complementar | Reindexação controlada; overlap 150; validação prévia MediaWiki; `docs/custom_corpus/pgvector.md`; 155 chunks na rodada v3 |

**Equivalência legada (Teste 1):** nos artefatos `benchmark_20260525_160434.*`, o campo `corpus = "wikipedia_benchmark"` equivale semanticamente a `corpus_version = "wikipedia_benchmark_v1"`. Metadados foram padronizados sem reprocessamento retroativo de métricas.

### 2.2 Refinamentos metodológicos (v3)

- **Validação de tópicos:** `validate_wiki_topics_v3.py` → `results/wiki_topic_validation_wikipedia_benchmark_v3.json` (existência, redirect, título efetivo).
- **Deduplicação:** hash SHA-256, bloqueio por `source_topic` e similaridade textual (>95%) no escopo da versão.
- **Corpus complementar:** documentação curada para lacunas da Wikipédia PT (pgvector), com `source_topic=custom:pgvector`.
- **Impacto esperado na recuperação semântica:** maior probabilidade de top-k com trechos alinhados à pergunta; redução de lacunas factuais; possível redundância entre chunks v1 e v3 do mesmo artigo.

### 2.3 Cobertura no benchmark final

No `run_id` `20260526_171347`, o índice consultado acumula **601 documentos/chunks** (`corpus_document_count` / `corpus_chunk_count`), refletindo v1+v2+v3. A rodada de indexação v3 isolada registrou 155 chunks em `corpus_report_wikipedia_benchmark_v3.json`.

---

## 3. Rastreabilidade do Teste 1 (legacy)

| Atributo | Valor |
|----------|-------|
| `run_id` | `20260525_160434` |
| Rótulo histórico | `corpus = "wikipedia_benchmark"` |
| Versão padronizada | `wikipedia_benchmark_v1` |
| Perguntas | 5 |
| Artefatos | `results/benchmark_20260525_160434.json`, `.csv` |

**Nota metodológica:** os ficheiros históricos foram preservados sem alteração estrutural das métricas (EM, F1, latências, respostas). Não houve reprocessamento retroativo. O objetivo foi manter **comparabilidade experimental** e **validade comparativa longitudinal** — prática recomendada em estudos empíricos iterativos, na qual reinterpretar resultados antigos com métricas novas invalidaria a série temporal documentada.

---

## 4. Resultados quantitativos — benchmark v3 final

**Configuração:** `corpus_version = wikipedia_benchmark_v3`; 18 perguntas; cenários `llm`, `rag_basic`, `rag_rerank`; `top_k_config = 5`.

### 4.1 Métricas médias globais (18 perguntas)

| Cenário | EM médio | F1 médio | Latência média (s) | Chunks médios | Observação |
|---------|----------|----------|-------------------|---------------|------------|
| `llm` | 0,000 | **0,189** | ≈ 35 | 0 | Baseline sem contexto |
| `rag_basic` | 0,000 | **0,239** | ≈ 117 | 5,0 | Melhor F1 médio |
| `rag_rerank` | 0,000 | **0,202** | ≈ 124 | 5,0 | +≈1,6 s rerank médio; F1 abaixo de `rag_basic` |

**Leitura cautelosa:** o retrieval (`rag_basic`) elevou o F1 médio em relação ao `llm` (+0,050 absoluto, ≈+26% relativo). O reranking acrescentou latência (`mean_rerank_latency_seconds` ≈ 1,59 s) **sem** elevar o F1 médio neste corpus e conjunto de perguntas — efeito dependente do tamanho do índice, da qualidade do pool inicial e do ruído no top-k expandido, não indicativo de inadequação universal do reranking.

### 4.2 Desagregação por subconjunto

| Subconjunto | Cenário | F1 médio | Latência média (s) |
|-------------|---------|----------|-------------------|
| `core_5` (n=5) | `llm` | 0,282 | ≈ 70 |
| `core_5` | `rag_basic` | **0,332** | ≈ 113 |
| `core_5` | `rag_rerank` | 0,294 | ≈ 117 |
| `extended` (n=13) | `llm` | 0,153 | ≈ 22 |
| `extended` | `rag_basic` | **0,204** | ≈ 119 |
| `extended` | `rag_rerank` | 0,166 | ≈ 127 |

O subconjunto `extended` concentra perguntas de maior dificuldade documental (embeddings, bancos vetoriais, LangChain). **Não** comparar F1 de `core_5` na v3 diretamente com Testes 1/2 sem verificar identidade dos gabaritos (refinados na v3).

### 4.3 Comparação longitudinal v1 / v2 / v3 (F1 médio `rag_basic`)

| Versão | `run_id` | Perguntas | F1 `llm` | F1 `rag_basic` | F1 `rag_rerank` |
|--------|----------|-----------|----------|----------------|-----------------|
| v1 (Teste 1) | `20260525_160434` | 5 | 0,030 | 0,112 | 0,132 |
| v2 (Teste 2) | `20260526_020326` | 5 | 0,030 | 0,119 | 0,122 |
| v3 (Teste 3) | `20260526_171347` | 18 | 0,189 | 0,239 | 0,202 |

A v3 altera simultaneamente corpus, gabaritos, controle de geração (`num_predict`, instrução concisa) e tamanho amostral — a tabela longitudinal ilustra **tendência**, não prova causal isolada de cada fator.

### 4.4 Cobertura temática indexada (v3)

Tópicos com chunks no relatório do benchmark: Aprendizado de máquina, Inteligência artificial, Rede neural artificial, PostgreSQL, Docker, API, REST, Banco de dados, Algoritmo, Recuperação de informação, LangChain, **custom:pgvector**.

### 4.5 Figuras consolidadas (`results/plots/`)

Geradas por `scripts/plot_benchmark_evolution.py` a partir dos JSON dos Testes 1–3 (rótulos v1, v2, v3). **Nota:** v3 usa 18 perguntas; v1 e v2 usam 5 — o gráfico de evolução ilustra tendência, não comparabilidade direta de amostra.

| Figura (arquivo) | Conteúdo | Uso sugerido no TCC |
|------------------|----------|---------------------|
| `f1_by_scenario.png` | F1 médio por cenário (`llm`, `rag_basic`, `rag_rerank`) × versão | Resultados — comparação entre cenários |
| `latency_by_scenario.png` | Latência média por cenário × versão | Discussão custo computacional |
| `evolution_f1_v1_v2_v3.png` | Linhas de F1 por cenário ao longo de v1→v2→v3 | Evolução experimental |
| `tradeoff_f1_latency_rerank.png` | Dispersão F1 × latência (`rag_rerank` apenas) | Tradeoff qualidade × tempo |

Comando de regeneração (a partir da raiz `tcc-project/`):

```bash
python scripts/plot_benchmark_evolution.py \
  --runs results/benchmark_20260525_160434.json \
        results/benchmark_20260526_020326.json \
        results/benchmark_20260526_171347.json \
  --labels v1 v2 v3
```

### 4.6 Tabela mestre — três testes (médias por cenário)

Valores de F1 e latência extraídos dos `summaries` de cada `run_id`. EM = 0 em todas as células.

| Teste | `run_id` | N perg. | Cenário | F1 médio | Latência média (s) |
|-------|----------|---------|---------|----------|-------------------|
| 1 (v1) | `20260525_160434` | 5 | `llm` | 0,030 | 120,2 |
| 1 | | | `rag_basic` | 0,112 | 74,7 |
| 1 | | | `rag_rerank` | 0,132 | 133,2 |
| 2 (v2) | `20260526_020326` | 5 | `llm` | 0,030 | 152,4 |
| 2 | | | `rag_basic` | 0,119 | 170,7 |
| 2 | | | `rag_rerank` | 0,122 | 435,7 |
| 3 (v3) | `20260526_171347` | 18 | `llm` | 0,189 | 35,0 |
| 3 | | | `rag_basic` | 0,239 | 117,0 |
| 3 | | | `rag_rerank` | 0,202 | 123,9 |

Detalhe por pergunta: `results/benchmark_<run_id>.csv`.

---

## 5. Validação qualitativa do retrieval

Procedimento: `validar_retrieval.py` sobre `wikipedia_benchmark_v3`, inspeção manual do top-k=5. Saída: `results/retrieval_validation_wikipedia_benchmark_v3.txt`.

### 5.1 Procedimento

- Verificação de relevância semântica do top-1 e dos demais chunks.
- Análise de **diversidade** (títulos/URLs distintos) e **repetição** (trechos sobrepostos do mesmo artigo).
- Registro do **mix de `corpus_version`** na saída (v1, v2, v3).

### 5.2 Observações principais

| Observação | Evidência qualitativa |
|------------|----------------------|
| Chunks repetidos em várias perguntas | Ex.: machine learning — múltiplos trechos de *Aprendizado de máquina* (v1 e v3); PostgreSQL — baixa diversidade |
| Reutilização frequente de chunks v1 | Mix v1 dominante em IA, Docker, REST; v3 complementa em RI e pgvector |
| v3 complementa cobertura semântica | Recuperação de informação: top-k majoritariamente v2/v3; busca semântica: chunks v3 de RI |
| Diversidade média do top-k | Predominantemente **média**; exceções de baixa diversidade (PostgreSQL) |
| Corpus customizado necessário para pgvector | Top-1 irrelevante (Rede neural artificial); chunk `custom:pgvector` aparece em posição 3 |
| Lacunas Wikipédia PT | Tópicos planejados sem artigo estável (10 ignorados na indexação v3) |

### 5.3 Por que complementar EM/F1

EM/F1 medem aderência lexical da **resposta gerada** ao gabarito; não isolam se o retrieval entregou evidência adequada. A inspeção manual do top-k explica falhas de geração versus falhas de recuperação e justifica decisões de curadoria (corpus complementar, deduplicação).

---

## 6. Casos observados durante o benchmark

### 6.1 LangChain

- **`llm`:** resposta de que LangChain “não existe” — limitação de conhecimento paramétrico do phi3.
- **`rag_basic`:** resposta correta como framework open source para aplicações com LLMs (F1 elevado relativamente ao baseline).
- **Implicação:** evidencia dependência do retrieval contextual para tópicos recentes ou de nicho.

### 6.2 Bancos vetoriais

- **`llm`:** confusão entre “bancos **vetoriais**” e “bancos **virtuais**” (instituições financeiras digitais).
- **`rag_basic`:** desvio semântico para PostgreSQL/TimescaleDB e dados geoespaciais — ambiguidade lexical e retrieval imperfeito.
- **Implicação:** ambiguidade morfológica em português afeta embedding e geração.

### 6.3 pgvector

- **`llm`:** definição parcialmente alinhada, porém imprecisa (“módulo” genérico).
- **`rag_basic`:** resposta alinhada ao corpus complementar (extensão PostgreSQL, busca por similaridade, uso em RAG).
- **Implicação:** mesmo com top-1 irrelevante na validação qualitativa, o contexto agregado no prompt melhorou a resposta — ganho dependente da inclusão documental controlada.

### 6.4 Embeddings

- Respostas **parcialmente corretas** porém vagas ou ancoradas em subseções periféricas de *Aprendizado de máquina* (aprendizado por dicionário esparso).
- **Implicação:** limitação conceitual do modelo e do alinhamento chunk-pergunta, não apenas ausência de RAG.

---

## 7. Discussão dos resultados

1. **Retrieval contribuiu semanticamente:** `rag_basic` superou `llm` no F1 médio global e em ambos os subconjuntos, coerente com a hipótese de que contexto documental ancora a geração.
2. **RAG melhorou sobre LLM puro no agregado v3**, com ressalva de que gabaritos refinados e controle de verbosidade também influenciam F1.
3. **Reranking elevou latência** (≈ +7 s médios vs. `rag_basic`, além de ≈1,6 s de rerank explícito) **sem** ganho médio de F1 nesta configuração — tradeoff qualidade × custo desfavorável **neste** experimento, não conclusão geral sobre rerankers.
4. **Corpus incremental** ampliou cobertura temática (RI, pgvector customizado, rechunk v3), mas manteve redundância entre versões, afetando diversidade do top-k.
5. **Qualidade do retrieval influencia a geração** diretamente (pgvector, LangChain, bancos vetoriais).
6. **Limitações do phi3** permanecem em respostas abstratas, prolixas ou alucinadas quando o contexto é insuficiente ou ambíguo.

**Tradeoffs centrais:** qualidade (F1) × latência; cobertura documental × ruído no índice cumulativo; estágio de retrieval × capacidade do gerador local.

---

## 8. Ameaças à validade e limitações

| Limitação | Impacto na interpretação |
|-----------|-------------------------|
| EM ≈ 0 em todas as rodadas | Natureza generativa do phi3 e gabaritos concisos; EM não discrimina adequação semântica |
| F1 token-level | Insensível a paráfrases; sensível a prolixidade e tokens extras |
| Wikipédia PT | Cobertura incompleta para software especializado |
| Índice cumulativo v1+v2+v3 | Dificulta atribuir ganhos exclusivamente à curadoria v3 |
| Chunks repetidos entre versões | Reduz diversidade informacional do top-k |
| Corpus pequeno (601 chunks vs. sistemas comerciais) | Generalização limitada |
| Hardware local | Latência não transferível entre máquinas |
| Avaliação qualitativa manual | Subjetividade parcial; não substitui métricas automáticas em escala |
| Modelos EN no retrieval/rerank | Possível sub-representação lexical em português |
| 18 perguntas | Amostra reduzida; `extended` domina médias globais |

---

## 9. Conclusão experimental

O pipeline RAG foi **implementado e avaliado com sucesso** no escopo do TCC: ingestão versionada, embeddings em pgvector, recuperação densa, reranking opcional e geração local via Ollama/phi3. Os resultados do `run_id` `20260526_171347` indicam que:

- o **retrieval melhorou a qualidade média das respostas** (F1) em relação ao baseline `llm`, de forma consistente com a literatura RAG, porém com magnitudes modestas e EM nulo;
- o **reranking apresentou tradeoff custo/benefício desfavorável na média** deste corpus e configuração, sem invalidar seu uso em índices maiores ou com maior ruído no pool inicial;
- o **versionamento do corpus** permitiu evolução controlada e rastreável (v1 → v2 → v3) sem apagar evidências dos Testes 1 e 2;
- a **validação qualitativa do retrieval** complementou EM/F1, explicando repetição de chunks, mix de versões e lacunas documentais;
- a combinação **PostgreSQL + pgvector + corpus complementar curado** demonstra **viabilidade técnica** de RAG local para domínio técnico em português, **sem** caracterizar desempenho “excelente” ou generalizável a outros domínios, modelos ou escalas de corpus.

Trabalhos futuros sugeridos: métricas semânticas em português, avaliação humana em rubrica, ablação de rerank com índice maior, busca híbrida e redução de redundância inter-versões no índice.

---

## 10. Referência rápida de artefatos

| Artefato | Descrição |
|----------|-----------|
| `results/benchmark_20260525_160434.*` | Teste 1 (v1, legado) |
| `results/benchmark_20260526_020326.*` | Teste 2 (v2) |
| `results/benchmark_20260526_171347.*` | Teste 3 final (v3) |
| `results/retrieval_validation_wikipedia_benchmark_v3.txt` | Inspeção qualitativa top-k |
| `results/corpus_report_wikipedia_benchmark_v3.json` | Estatísticas da indexação v3 |
| `results/plots/*.png` | Figuras consolidadas (secção 4.5) |
| `app/dados/benchmark_questions_v3.json` | 18 perguntas (`core_5` + `extended`) |

_Preliminares históricos preservados:_ [preliminary_results_test_1.md](preliminary_results_test_1.md), [preliminary_results_test_2.md](preliminary_results_test_2.md), [preliminary_results_test_3.md](preliminary_results_test_3.md).
