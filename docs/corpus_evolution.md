# Evolução controlada do corpus experimental

## Contexto metodológico

O benchmark preliminar (Teste 1, `run_id=20260525_160434`) foi executado sobre um corpus **limitado** de artigos técnicos da Wikipédia em português. Os resultados indicaram ganhos com RAG e reranking, mas também **lacunas de cobertura** — em especial na pergunta sobre **pgvector**, para a qual o índice não continha contexto adequado.

Para fortalecer a **validade experimental** sem perder comparabilidade histórica, o projeto passou a tratar o corpus como artefato **versionado**, com rastreio em banco, relatórios JSON e documentação automática.

## Por que expandir o corpus

1. **Cobertura documental:** conceitos centrais do pipeline (embeddings, busca vetorial, pgvector, APIs) precisam existir como chunks indexados para o RAG operar como desenhado.
2. **Hipótese testável:** o desempenho em tarefas factuais depende da interseção entre pergunta, qualidade do retrieval e **presença do tema no corpus** — não apenas da sofisticação do reranker ou do LLM.
3. **Comparabilidade:** novos benchmarks referenciam explicitamente `corpus_version`, permitindo contrastar v1 (Teste 1) com v2/v3 sem sobrescrever silenciosamente o índice anterior.

## Versões e tiers

| Versão | Tier | Papel |
|--------|------|--------|
| `wikipedia_benchmark_v1` | inicial | Reproduz o escopo do Teste 1 (9 tópicos, chunk 500/100) |
| `wikipedia_benchmark_v2` | expandido | Acrescenta tópicos RAG/vetores/stack; indexação **incremental** |
| `wikipedia_benchmark_v3` | refinado | Corpus Wikipédia **curado** (validação prévia de títulos) + documentação complementar controlada; overlap=150 secundário |

O rótulo legado `wikipedia_benchmark` nos JSON antigos equivale a **`wikipedia_benchmark_v1`**.

## Deduplicação

Foram introduzidos três mecanismos complementares:

| Mecanismo | Objetivo |
|-----------|----------|
| **SHA-256** do conteúdo normalizado | Impedir reinserção de chunk idêntico |
| **Bloqueio por `source_topic`** | Impedir reindexar a mesma página Wikipédia (modo incremental v2) |
| **Similaridade textual > 95%** | Evitar chunks quase duplicados (`rapidfuzz` ou `difflib`) |

**Motivação acadêmica:** a deduplicação reduz redundância semântica no índice e mitiga **viés de recuperação** (vários chunks quase iguais dominando o `top_k`), sem apagar versões anteriores do corpus.

Na v3 refinada, a similaridade é avaliada **no escopo da mesma versão**, para permitir rechunking com overlap maior sem bloquear por similaridade com chunks da v2.

## Chunking

| Versão | chunk_size | overlap | Nota |
|--------|------------|---------|------|
| v1, v2 | 500 | 100 | Alinhado à indexação original do Teste 1 |
| v3 | 500 | 150 | Overlap secundário; foco principal em curadoria e cobertura real |

Alterações de chunking **não reescrevem** benchmarks passados: cada versão mantém seus documentos em `documents.corpus_version`.

## Rastreabilidade no benchmark

Cada execução exporta:

- `corpus_version`
- `corpus_document_count` / `corpus_topics_indexed`
- `embedding_model`, `rerank_model`, `llm_model`

A recuperação usa versões **cumulativas** conforme a versão do benchmark (ex.: v2 consulta documentos v1 + v2).

## Relação cobertura × desempenho RAG

Observação útil para o TCC:

> *A expansão incremental do corpus permite avaliar empiricamente a influência da cobertura documental sobre o desempenho do pipeline RAG, mantendo o protocolo de métricas (EM/F1) e os cenários de inferência comparáveis entre versões.*

> *A deduplicação foi introduzida para reduzir redundância semântica e evitar viés de recuperação, sem conflitar com a preservação histórica das versões v1 e v2.*

## Fluxo operacional recomendado

```bash
# 1. Migrar schema + marcar legado como v1
python create_tables.py

# 2. Indexar v1 (se necessário; sem --clear por padrão)
python indexar_dados.py

# 3. Expandir corpus (somente tópicos novos)
python indexar_corpus.py --version wikipedia_benchmark_v2

# 4. Benchmark preliminar na v2
python run_benchmark_preliminary.py --corpus-version wikipedia_benchmark_v2

# 5. Validar títulos Wikipédia PT (v3)
python validate_wiki_topics_v3.py

# 6. Corpus refinado (v3)
python indexar_corpus.py --version wikipedia_benchmark_v3 --no-incremental

# 7. Benchmark Teste 3
python run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v3
```

## Validação prévia de títulos (v3)

Antes da indexação v3, cada título MediaWiki é verificado contra a API da Wikipédia PT:

- `topic_exists` — página encontrada ou resolvida via redirect
- `redirect_exists` — título solicitado redireciona para outro artigo
- `fallback_title` — título alternativo quando o principal falha
- `selected_title` — título efetivamente usado na coleta

Relatório gerado em `results/wiki_topic_validation_wikipedia_benchmark_v3.json`.

**Motivação:** a v2 solicitou 12 tópicos e indexou apenas 2 — muitos títulos eram inexistentes, redirects não resolvidos ou extracts insuficientes. A validação prévia evita planejar cobertura que nunca entra no índice.

## Inclusão controlada de documentação complementar

### Limitações da Wikipédia PT

A Wikipédia em português **não possui** artigo dedicado estável para diversos conceitos de software especializado (ex.: **pgvector**). No Teste 1 e Teste 2, a pergunta sobre pgvector tornou-se um **resultado metodológico**: o pipeline RAG não compensa ausência de evidência documental, e o baseline `llm` pode alucinar.

### Motivação da inclusão manual

Para o Teste 3, foi adotado um **corpus complementar mínimo** em `docs/custom_corpus/`:

- Documentos **curtos**, técnicos e objetivos
- `source_url` explícita (repositório ou documentação oficial)
- Rastreio no índice via `source_topic=custom:<id>` e `corpus_version=wikipedia_benchmark_v3`
- **Sem** mascarar a limitação: a dissertação deve distinguir Wikipédia PT de fonte complementar

Exemplo atual: `docs/custom_corpus/pgvector.md` (fonte: repositório oficial pgvector).

### Impacto esperado

- Permitir avaliar RAG na pergunta histórica sobre pgvector **sem inventar** artigo na Wikipédia
- Manter honestidade: ganhos de F1 nessa pergunta refletem **inclusão documental controlada**, não melhoria do modelo
- Não generalizar para “o RAG resolve pgvector” fora do escopo do corpus experimental

## Evolução experimental do corpus

| Fase | Versão | O que mudou | O que **não** mudou |
|------|--------|-------------|---------------------|
| Teste 1 | v1 | Corpus inicial Wikipédia (9 tópicos) | — |
| Teste 2 | v2 | Expansão incremental planejada | Embeddings, retrieval, rerank, phi3 |
| Teste 3 | v3 | Curadoria + validação + complementar + benchmark 18 perguntas + controle phi3 | Arquitetura RAG, modelos de embedding/rerank |

## Limitações epistemológicas

1. **Melhorar benchmark ≠ melhorar RAG:** gabaritos mais representativos e mais perguntas aumentam validade métrica; não provam modelo superior isoladamente.
2. **Cobertura documental:** desempenho em tarefas factuais depende da interseção pergunta–índice (evidenciado em pgvector nos Testes 1–2).
3. **Wikipédia PT:** viés de idioma, atualização e ausência de tópicos de nicho.
4. **phi3 local:** verbosidade e latência; EM literal permanece severo mesmo com `num_predict` e instrução concisa.
5. **EM/F1 token-level:** favorece respostas curtas; comparar F1 entre Teste 1/2 e Teste 3 no subconjunto `core_5` exige cautela se os **gabaritos** mudaram (ver Teste 3).

### Comparabilidade de métricas (Teste 3)

| Subconjunto | Perguntas | Comparável com Teste 1/2? |
|-------------|-----------|---------------------------|
| `core_5` | Mesmo texto de pergunta | Texto da pergunta sim; **F1 só comparável com gabarito idêntico** — Teste 3 refinou respostas esperadas |
| `extended` | 13 novas | Não — amplia amostra e estabilidade, sem histórico |

**Regra:** não interpretar aumento de F1 médio global do Teste 3 como ganho puro do pipeline sem separar efeito de gabarito, cobertura e controle de geração.

## Riscos e vieses remanescentes

- Tópicos sem artigo equivalente na Wikipédia PT podem ser **ignorados** na coleta (ex.: Pgvector).
- Modelos de embedding/rerank **anglófonos** podem sub-representar termos em português.
- Corpus cumulativo (v2 sobre v1) aumenta ruído se houver **desatualização** entre artigos.
- Expansão temática pode **inflar F1** em perguntas antes falhas — interpretar como efeito de cobertura, não só de modelo.

## Resultados Preliminares da Expansão do Corpus

Esta seção consolida evidências empíricas da transição **Teste 1 → Teste 2**, com base nos artefatos `benchmark_20260525_160434.json` (v1) e `benchmark_20260526_020326.json` (v2). Os ficheiros históricos **não foram alterados**.

### Crescimento do corpus

| Indicador | v1 (`wikipedia_benchmark_v1`) | Acréscimo v2 (rodada incremental) | Total visível no Teste 2 |
|-----------|------------------------------|-----------------------------------|--------------------------|
| Documentos/chunks | 411 | +35 | 446 |
| Tópicos com chunks (relatório de indexação) | 9 | 2 novos (`Recuperação_de_informação`, `LangChain`) | 11 listados no benchmark v2 |
| Tópicos solicitados na expansão e ignorados | — | 10 | — |

O crescimento é **incremental e cumulativo**: a recuperação na versão v2 consulta documentos marcados como v1 e v2, preservando o conteúdo do Teste 1 no índice.

### Aumento de cobertura temática

A expansão planejou tópicos de embeddings, busca vetorial, APIs e componentes do pipeline RAG. Na prática, a rodada documentada em `corpus_report_wikipedia_benchmark_v2.json` indexou **dois** tópicos adicionais. Tópicos como *pgvector* ou *banco de dados vetorial* não passaram a constar como páginas dedicadas no índice — limitação da disponibilidade na Wikipédia PT e do modo incremental (páginas já indexadas são ignoradas).

### Relação entre cobertura e retrieval

- **Machine learning:** F1 de `rag_basic` subiu de **0,154** (Teste 1) para **0,286** (Teste 2), com `chunks_retrieved` = 5 e latência de retrieval elevada na pergunta (≈ 59 s), sugerindo índice maior e contexto mais amplo.
- **pgvector:** F1 de `rag_basic` **caiu** de 0,133 para 0,069; as respostas continuam a negar contexto adequado. A expansão **não** supriu a lacuna central identificada no Teste 1.
- **PostgreSQL:** F1 de `rag_rerank` manteve-se em **0,296** nos dois testes — cenário já bem coberto na v1.

A hipótese de que *desempenho RAG ∝ cobertura documental* mantém-se válida; a expansão v2 testou-a de forma **parcial**, não universal.

### Melhorias observadas no benchmark (Teste 2)

| Métrica | Teste 1 | Teste 2 | Leitura |
|---------|---------|---------|---------|
| F1 médio `rag_basic` | 0,1116 | **0,1188** | Melhoria modesta (+0,0072) |
| F1 médio `rag_rerank` | **0,1317** | 0,1216 | Queda agregada; outlier REST no Teste 2 |
| F1 médio `llm` | 0,0301 | 0,0301 | Invariante (sem retrieval) |
| EM (todos os cenários) | 0 | 0 | Estável |

Documentação analítica completa: [preliminary_results_test_2.md](preliminary_results_test_2.md) e [discussion_preliminary_findings.md](discussion_preliminary_findings.md).

## Resultados do Teste 3 (v3 refinado)

**`run_id`:** `20260526_171347` | Índice consultado: 601 chunks (v1+v2+v3) | Rodada v3: 155 chunks | 18 perguntas.

Métricas, figuras (`results/plots/`), validação qualitativa e discussão: **[final_experimental_analysis.md](final_experimental_analysis.md)** §4–9 (fonte canônica).

**Equivalência Teste 1:** `corpus = "wikipedia_benchmark"` ≡ `wikipedia_benchmark_v1` — artefatos preservados sem reprocessamento.

## Artefatos

- Registro de versões: `app/dados/corpus_registry.py`
- Documentação viva: `docs/corpus_versions.md` (gerada após indexação)
- Relatórios: `results/corpus_report_<version>.json`
- Resultados de benchmark: `results/benchmark_<run_id>.json` (**não sobrescrever** Testes 1, 2 nem 3)
- Análise final: `docs/final_experimental_analysis.md`
