# Evolução controlada do corpus (plataforma)

Guia **operacional** de versionamento e indexação.

> Análises e resultados históricos: `research-archive`.  
> Inventário técnico gerado pelo pipeline: [`../corpus_versions.md`](../corpus_versions.md).

## Versões e tiers

| Versão | Tier | Papel |
|--------|------|--------|
| `wikipedia_benchmark_v1` | inicial | Escopo base (9 tópicos, chunk 500/100) |
| `wikipedia_benchmark_v2` | expandido | Tópicos adicionais; indexação incremental |
| `wikipedia_benchmark_v3` | refinado | Validação prévia de títulos + complementar; overlap=150 |

O rótulo legado `wikipedia_benchmark` equivale a **`wikipedia_benchmark_v1`**.

## Deduplicação

| Mecanismo | Objetivo |
|-----------|----------|
| SHA-256 do conteúdo normalizado | Evitar chunk idêntico |
| Bloqueio por `source_topic` | Evitar reindexar a mesma página (incremental) |
| Similaridade textual alta | Evitar quase-duplicados |

Na v3, a similaridade é avaliada **no escopo da mesma versão**.

## Chunking

| Versão | chunk_size | overlap |
|--------|------------|---------|
| v1, v2 | 500 | 100 |
| v3 | 500 | 150 |

Alterações de chunking **não reescrevem** documentos de outras versões: cada uma mantém `documents.corpus_version` próprio.

## Rastreabilidade no benchmark

Cada execução pode exportar: `corpus_version`, contagens de documentos/tópicos, modelos de embedding/rerank/LLM.

A recuperação pode consultar versões **cumulativas** conforme a versão pedida (ex.: v2 → v1+v2).

## Fluxo operacional

```bash
python scripts/indexing/create_tables.py
python scripts/indexing/indexar_dados.py
python scripts/indexing/indexar_corpus.py --version wikipedia_benchmark_v2
python scripts/indexing/validate_wiki_topics_v3.py
python scripts/indexing/indexar_corpus.py --version wikipedia_benchmark_v3 --no-incremental
python scripts/benchmark/run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v3
```

## Validação prévia de títulos (v3)

`validate_wiki_topics_v3.py` verifica títulos MediaWiki (existência, redirect, fallback) antes da indexação e pode escrever relatório em `results/` (scratch local).

## Documentação complementar

Para lacunas da Wikipédia PT, a plataforma aceita documentos curtos em `docs/methodology/custom_corpus/` (ex.: `pgvector.md`), indexados com `source_topic=custom:<id>`.

## Artefatos de software

- Registo de versões: `app/dados/corpus_registry.py`
- Documentação viva: `docs/corpus_versions.md`
- Relatórios locais: `results/corpus_report_<version>.json` (gitignored)
