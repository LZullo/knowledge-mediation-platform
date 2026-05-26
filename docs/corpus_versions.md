# Versões do corpus experimental

Documento gerado/atualizado automaticamente pelo pipeline de indexação. A seção **Evolução Experimental** é mantida de forma estável para rastreabilidade metodológica do TCC; as seções por versão refletem estatísticas atuais do banco.

## Evolução Experimental

### Teste 1 — corpus inicial (`wikipedia_benchmark_v1`)

O benchmark preliminar **Teste 1** (`run_id=20260525_160434`) foi executado **antes** da introdução do versionamento formal do corpus no banco e nos artefatos de exportação. Nos registros históricos, o corpus aparece como `wikipedia_benchmark`; esse identificador corresponde ao corpus posteriormente padronizado como `wikipedia_benchmark_v1` (tier `initial`, nove tópicos técnicos da Wikipédia PT, chunking 500/100). Os resultados do Teste 1 foram **preservados integralmente** (métricas EM/F1, latências, respostas e `run_id`); apenas a nomenclatura de rastreio foi padronizada na documentação e nos metadados dos artefatos.

O benchmark permanece **metodologicamente válido**: protocolo (três cenários, cinco perguntas, temperatura 0, mesmos modelos) e interpretação dos agregados não dependem do rótulo legado, mas da equivalência documentada entre `wikipedia_benchmark` e `wikipedia_benchmark_v1`.

### Teste 2 — corpus expandido (`wikipedia_benchmark_v2`)

O **Teste 2** utiliza o tier `expanded`: indexação **incremental** sobre a v1, acrescentando tópicos de embeddings, busca vetorial, pgvector, APIs e componentes do pipeline RAG. A motivação metodológica decorre da **cobertura insuficiente** observada no Teste 1 — em particular na pergunta sobre **pgvector**, para a qual o índice inicial não continha contexto adequado, limitando o ganho do RAG independentemente do reranking.

### Teste 3 — corpus refinado (`wikipedia_benchmark_v3`)

A versão **v3** (tier `refined`) reindexa os tópicos da v2 com overlap ampliado (150 caracteres), visando reduzir fragmentação entre chunks adjacentes, **sem** remover versões anteriores. Permite ablação de chunking mantendo comparabilidade entre Teste 1, Teste 2 e Teste 3 via `corpus_version` explícita em cada execução.

### Versionamento, deduplicação e cobertura documental

A partir da expansão planejada, o projeto adotou:

- **Versionamento** por `corpus_version` no banco e nos relatórios de benchmark;
- **Deduplicação** (hash de conteúdo, bloqueio por `source_topic`, similaridade textual) para mitigar redundância semântica no índice;
- **Retrieval cumulativo** (ex.: v2 consulta documentos v1 + v2).

A relação entre **cobertura documental** e **desempenho RAG** foi evidenciada no Teste 1: pipelines mais sofisticados não substituem a presença do tema no corpus. A expansão v2 testa empiricamente essa hipótese, mantendo EM/F1 e cenários comparáveis.

---

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

Corpus inicial controlado para o benchmark preliminar (Teste 1), com tópicos técnicos amplos da Wikipédia em português.

### Impacto esperado

Baseline de cobertura documental; evidenciou ganhos de RAG e lacunas (ex.: pgvector ausente no índice).

### Observações de chunking

chunk_size=500, overlap=100 — alinhado à indexação usada antes do Teste 1.

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

### Estatísticas indexadas (banco)

- **Documentos/chunks:** 0
- **Tópicos com chunks:** 0
- **Tamanho médio do chunk (caracteres):** 0.0

### Motivação

Reindexação com overlap maior para reduzir fragmentação de conceitos entre chunks adjacentes.

### Impacto esperado

Chunks mais contextuais; possível redução de ruído na recuperação. Coexiste com v1/v2 no banco — benchmarks devem declarar a versão alvo.

### Observações de chunking

chunk_size=500, overlap=150 (+50 vs. v1/v2). Reindexa todos os tópicos de v2 com nova marca de versão; não apaga versões anteriores.

---

_Atualize executando `python indexar_corpus.py --version <id>` ou `python -m app.dados.corpus_documentation` após indexação._