# Metodologia operacional da plataforma

Documenta o **pipeline de dados**, os **cenários de inferência** e as **métricas** implementadas no software.

> Protocolo científico do artigo e campanhas oficiais: `knowledge-mediation-study`.  
> Histórico acadêmico: `research-archive` (privado).

## 1. Corpus e perguntas de avaliação

### Base documental

- **Fonte padrão:** MediaWiki API (`pt.wikipedia.org`).
- **Lista controlada:** `WIKI_TOPICS` em `app/dados/wikipedia_loader.py`.
- Fluxo: texto → chunking → embeddings → tabela `documents`.

### Fixtures de perguntas

| Ficheiro | Uso típico |
|----------|------------|
| `app/dados/benchmark_questions_v2_final.json` | Conjunto menor (5 perguntas) |
| `app/dados/benchmark_questions_v3.json` | Conjunto ampliado (`core_5` + `extended`) |

Pares `question` / `answer` (gold) **não** são enviados ao modelo na consulta.

### Controlo de domínio

- Apenas títulos em `WIKI_TOPICS` são descarregados e indexados.
- Páginas com conteúdo abaixo de `_MIN_CONTENT_CHARS` são ignoradas.
- Novos tópicos: editar `WIKI_TOPICS` e reindexar.

Corpus complementar documentado: `docs/methodology/custom_corpus/` (ex.: `pgvector.md`).

## 2. Versionamento de corpus

A plataforma trata o corpus como artefato **versionado** (`documents.corpus_version`):

| Versão | Tier | Papel |
|--------|------|--------|
| `wikipedia_benchmark_v1` | inicial | Escopo base (9 tópicos) |
| `wikipedia_benchmark_v2` | expandido | Expansão incremental |
| `wikipedia_benchmark_v3` | refinado | Curadoria + validação de títulos + complementar |

Inventário gerado pelo pipeline: [`../corpus_versions.md`](../corpus_versions.md).

Deduplicação: SHA-256 do conteúdo, bloqueio por `source_topic` (modo incremental) e similaridade textual alta.

## 3. Cenários de inferência

Expostos via Strategy Pattern em `execute_rag`:

| Cenário | Descrição |
|---------|-----------|
| `llm` | Geração sem retrieval |
| `rag_basic` | Retrieval vetorial + geração |
| `rag_optimized` | RAG com prompt mais restritivo |
| `rag_rerank` | Retrieval + CrossEncoder + geração |

Parâmetros típicos: `top_k`, `rerank_top_k`, `score_threshold` (rerank).

## 4. Métricas

Implementadas em `app/evaluation/metrics.py` (normalização estilo SQuAD):

- **Exact Match (EM)** — igualdade após normalização
- **F1 token-level** — overlap de tokens
- Latência (total e, quando disponível, retrieval/geração/rerank)
- Tokens / chunks recuperados (quando disponíveis)

Export: `app/evaluation/export.py` → `results/` (scratch local gitignored).

## 5. Execução

Ver o guia operacional: [experiments.md](experiments.md).

## 6. Fronteira de responsabilidade

| Repositório | Conteúdo |
|-------------|----------|
| **Esta plataforma** | Software, infra, docs técnicas, scripts, testes |
| **knowledge-mediation-study** | Benchmark oficial, protocolo, campanha, estatística, paper |
| **research-archive** | TCC, banca, rascunhos, artefatos históricos |
