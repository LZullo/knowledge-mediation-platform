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
| `wikipedia_benchmark_v3` | refinado | Mesmos tópicos de v2 com **overlap=150**; reindexação sem apagar v1/v2 |

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
| v3 | 500 | 150 | Menor fragmentação entre janelas adjacentes |

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

# 5. (Opcional) Corpus refinado
python indexar_corpus.py --version wikipedia_benchmark_v3 --no-incremental
```

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

## Artefatos

- Registro de versões: `app/dados/corpus_registry.py`
- Documentação viva: `docs/corpus_versions.md` (gerada após indexação)
- Relatórios: `results/corpus_report_<version>.json`
- Resultados de benchmark: `results/benchmark_<run_id>.json` (**não sobrescrever** Teste 1 nem Teste 2)
