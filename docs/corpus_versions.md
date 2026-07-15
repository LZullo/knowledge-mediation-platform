# Versões do corpus experimental

Documento gerado/atualizado automaticamente pelo pipeline de indexação. Preserva rastreabilidade entre versões de corpus (`wikipedia_benchmark_v1` = rótulo legado `wikipedia_benchmark`).

## wikipedia_benchmark_v1

**Tier:** `initial`  
**Chunking:** `chunk_size=500`, `overlap=100`  

### Tópicos solicitados

- `Aprendizado_de_máquina`
- `Inteligência_artificial`
- `Rede_neural_artificial`
- `PostgreSQL`
- `Docker_(software)`
- `Interface_de_programação_de_aplicações`
- `REST`
- `Banco_de_dados`
- `Algoritmo`

### Estatísticas indexadas (banco)

- **Documentos/chunks:** 411
- **Tópicos com chunks:** 9
- **Tamanho médio do chunk (caracteres):** 494.9

### Motivação

Corpus inicial controlado para o benchmark de exemplo da plataforma, com tópicos técnicos amplos da Wikipédia em português.

### Impacto esperado

Baseline de cobertura documental; evidenciou ganhos de RAG e lacunas (ex.: pgvector ausente no índice).

### Observações de chunking

chunk_size=500, overlap=100 — alinhado à indexação da versão inicial.

## wikipedia_benchmark_v2

**Tier:** `expanded`  
**Versão anterior:** `wikipedia_benchmark_v1`  
**Chunking:** `chunk_size=500`, `overlap=100`  

### Tópicos solicitados

- `Aprendizado_de_máquina`
- `Inteligência_artificial`
- `Rede_neural_artificial`
- `PostgreSQL`
- `Docker_(software)`
- `Interface_de_programação_de_aplicações`
- `REST`
- `Banco_de_dados`
- `Algoritmo`
- `Embedding`
- `Sentence-BERT`
- `Banco_de_dados_vetorial`
- `Busca_semântica`
- `Recuperação_de_informação`
- `Similaridade_do_cosseno`
- `Transformer_(modelo_de_linguagem)`
- `LangChain`
- `FastAPI`
- `Serviço_web`
- `Geração_de_texto`

### Tópicos adicionados (em relação à versão anterior)

- `Embedding`
- `Sentence-BERT`
- `Banco_de_dados_vetorial`
- `Busca_semântica`
- `Recuperação_de_informação`
- `Similaridade_do_cosseno`
- `Transformer_(modelo_de_linguagem)`
- `LangChain`
- `FastAPI`
- `Serviço_web`
- `Geração_de_texto`

### Estatísticas indexadas (banco)

- **Documentos/chunks:** 35
- **Tópicos com chunks:** 2
- **Tamanho médio do chunk (caracteres):** 480.6

### Motivação

Expansão incremental com tópicos de embeddings e busca vetorial, APIs e ferramentas do pipeline RAG, sem remover documentos da v1.

### Impacto esperado

Melhorar cobertura em perguntas sobre embeddings e retrieval; permitir comparar benchmarks v1 vs. v2 com filtro de versão.

### Observações de chunking

Mesmos parâmetros de chunk da v1 na expansão; apenas tópicos novos são indexados.

## wikipedia_benchmark_v3

**Tier:** `refined`  
**Versão anterior:** `wikipedia_benchmark_v2`  
**Chunking:** `chunk_size=500`, `overlap=150`  

### Tópicos solicitados

- `Aprendizado_de_máquina`
- `PostgreSQL`
- `REST`
- `Docker_(software)`
- `Embedding`
- `Banco_de_dados_vetorial`
- `Busca_semântica`
- `Recuperação_de_informação`
- `Similaridade_do_cosseno`
- `Transformer_(modelo_de_linguagem)`
- `LangChain`
- `Processamento_de_linguagem_natural`
- `Modelo_de_linguagem`
- `Rede_neural_artificial`
- `Interface_de_programação_de_aplicações`

### Tópicos adicionados (em relação à versão anterior)

- `Aprendizado_de_máquina`
- `PostgreSQL`
- `REST`
- `Docker_(software)`
- `Embedding`
- `Banco_de_dados_vetorial`
- `Busca_semântica`
- `Recuperação_de_informação`
- `Similaridade_do_cosseno`
- `Transformer_(modelo_de_linguagem)`
- `LangChain`
- `Processamento_de_linguagem_natural`
- `Modelo_de_linguagem`
- `Rede_neural_artificial`
- `Interface_de_programação_de_aplicações`

### Corpus complementar (documentação curada)

- `docs/custom_corpus/pgvector.md`

### Estatísticas indexadas (banco)

- **Documentos/chunks:** 155
- **Tópicos com chunks:** 6
- **Tamanho médio do chunk (caracteres):** 493.7

### Motivação

Refinamento experimental: corpus Wikipédia curado com validação prévia de títulos, documentação complementar controlada para lacunas da Wikipédia PT (ex.: pgvector), benchmark ampliado e controle de verbosidade do gerador — sem alterar embeddings, retrieval ou rerank.

### Impacto esperado

Aumentar cobertura documental real; permitir subconjuntos `core_5` e `extended`; manter rastreabilidade v1→v2→v3.

### Observações de chunking

chunk_size=500, overlap=150 (secundário). Principal evolução: curadoria, validação de títulos e corpus complementar documentado.

---

## Tabela comparativa — versões do corpus

| Versão | Tier | Chunks (rodada isolada) | Chunks cumulativos típicos | Tópicos indexados (rodada) |
|--------|------|-------------------------|----------------------------|----------------------------|
| `wikipedia_benchmark_v1` | inicial | 411 | 411 | 9 |
| `wikipedia_benchmark_v2` | expandido | +35 | 446 | +2 |
| `wikipedia_benchmark_v3` | refinado | 155 | 601 | 6 + custom:pgvector |

**Nota:** o rótulo legado `wikipedia_benchmark` equivale a `wikipedia_benchmark_v1`.

> Métricas experimentais e runs científicos **não** fazem parte desta documentação da plataforma. Ver `knowledge-mediation-study` (artigo) e `research-archive` (histórico).

---

_Atualize executando `python scripts/indexing/indexar_corpus.py --version <id>` ou `python -m app.dados.corpus_documentation` após indexação._