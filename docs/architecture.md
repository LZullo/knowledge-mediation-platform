# Arquitetura do sistema

Este documento descreve **como o sistema está organizado**, **por que as camadas existem** e **como o fluxo ponta a ponta funciona**, com foco na defesa do TCC.

## Objetivo do sistema

Construir um **assistente de perguntas e respostas** em português que compare:

1. Resposta apenas com LLM (**sem contexto recuperado**)
2. RAG com recuperação vetorial simples
3. RAG com prompt mais restritivo e `top_k` configurável
4. RAG com **reranking** semântico após recuperação expandida

A base documental experimental usa **páginas técnicas da Wikipédia em português** (`WIKI_TOPICS`) indexadas em PostgreSQL com **pgvector**. O benchmark usa **perguntas manuais** em `benchmark_questions_v2_final.json` (conjunto congelado da versão oficial).

## Princípio central: Strategy Pattern sem pipeline duplicado

O fluxo RAG é **único** (`run_rag_pipeline`). O que muda entre cenários são **implementações plugáveis**:

| Abstração | Responsabilidade | Implementações atuais |
|-----------|------------------|------------------------|
| `RetrievalStrategy` | Obter trechos relevantes | `NoRetrieval`, `PgVector`, `RerankPgVector` |
| `PromptStrategy` | Montar contexto e prompt | `Direct`, `Default`, `Restrictive` |
| `GenerationStrategy` | Chamar o LLM | `OpenAIGenerationStrategy`, `OllamaGenerationStrategy` |

O provedor concreto é escolhido por `LLM_PROVIDER` (`app/application/providers/factory.py`). O caso de uso `execute_rag` **seleciona** retrieval e prompt conforme `RAGScenario`, injeta a strategy de geração via factory e registra a execução em `experiment_runs`.

```text
/ask → execute_rag → run_rag_pipeline(retrieval, prompt, generation)
```

Diagrama de componentes: [diagrams/architecture.mmd](diagrams/architecture.mmd).

## Camadas e responsabilidades

### 1. API (`app/api/`)

- **FastAPI** expõe `GET /health` e `POST /ask`.
- **Pydantic** valida entrada (`AskRequest`) e serializa saída (`AskResponse`).
- Não contém regra de negócio RAG; delega a `execute_rag`.

**Por quê FastAPI:** tipagem, OpenAPI automático (`/docs`), baixo boilerplate — adequado a protótipo experimental com API clara para demonstração na banca.

### 2. Casos de uso (`app/application/use_cases/`)

- **`execute_rag`**: orquestra cenário, chama pipeline, persiste métricas operacionais (latência, tokens, chunks).
- Define `RAGScenario` e parâmetros (`top_k`, `rerank_top_k`, `score_threshold`).

### 3. Serviços de aplicação (`app/application/services/`)

| Módulo | Papel |
|--------|--------|
| `rag_pipeline.py` | Fluxo genérico retrieve → prompt → generate |
| `vector_context.py` | `index_document(s)` e bridge para embeddings + `PgVectorStore` |
| `indexing_pipeline.py` | Ingestão offline de `.txt` (legado/auxiliar) |

### 4. Strategies e providers (`app/application/`)

- **Retrieval** (`strategies/retrieval/pgvector.py`, `rerank_pgvector_strategy.py`)
- **Prompt** (`strategies/prompt.py`)
- **Generation** (`strategies/generation.py`) — adapta o contrato `generate(prompt) -> LLMGenerationResult`
- **Providers** (`providers/ollama_provider.py`, `openai_provider.py`, `factory.py`) — Ollama via `langchain_ollama.ChatOllama`; OpenAI via `infrastructure/llm/openai_client.py`

### 5. Infraestrutura (`app/infrastructure/`)

| Componente | Função |
|------------|--------|
| `embeddings/embedding_model.py` | `sentence-transformers/all-MiniLM-L6-v2`, vetores 384D normalizados |
| `vectorstore/pgvector_store.py` | INSERT e busca por distância cosseno |
| `reranking/cross_encoder_reranker.py` | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| `llm/openai_client.py` | Chat completions OpenAI |
| `db/` | SQLAlchemy, modelos `Document`, `ExperimentRun` |

### 6. Dados e avaliação

- **`app/dados/`**: loader/indexação Wikipédia, chunking, `benchmark_loader`, JSON de perguntas.
- **`app/evaluation/`**: EM/F1, benchmark reproduzível, export JSON/CSV.

## Fluxo ponta a ponta: consulta (`/ask`)

1. Cliente envia `question` + `scenario` (+ parâmetros opcionais).
2. `execute_rag` escolhe strategies e `top_k` efetivo.
3. `run_rag_pipeline`:
   - **Retrieval:** embedding da pergunta → pgvector (`ORDER BY cosine_distance LIMIT k`).
   - **Rerank (se `rag_rerank`):** recupera `rerank_top_k` candidatos → CrossEncoder → mantém `top_k` finais.
   - **Prompt:** concatena `[source]\ncontent` com separador `---`.
   - **Generation:** `get_generation_strategy()` → Ollama (`phi3`) ou OpenAI; retorna texto e tokens (se disponível).
4. Scores de similaridade na resposta convertem distância cosseno em valor ~[0,1] (`cosine_distance_to_similarity`).
5. Registro em `experiment_runs` para auditoria.

Sequência detalhada: [diagrams/ask_sequence.mmd](diagrams/ask_sequence.mmd).

## Fluxo ponta a ponta: indexação

1. **`WIKI_TOPICS`:** lista fixa de títulos MediaWiki em `wikipedia_loader.py`.
2. **Coleta:** `fetch_wikipedia_corpus` — API `pt.wikipedia.org`; páginas curtas ou falhas entram em `topics_skipped`.
3. **Chunking:** `chunk_wikipedia_page` — `clean_text` → `chunk_text` (padrão 500 / overlap 100).
4. **`index_documents`:** `embed_texts` em lote → `PgVectorStore.insert_document` para cada chunk.
5. Campo **`source`:** `wikipedia|topic=...|title=...|url=...|chunk=N` — única metadata estruturada hoje.

Script operacional na raiz: `python indexar_dados.py` (`index_wikipedia_corpus`, opcional `clear_documents=True`).

A função genérica `index_documents` também suporta outros pares `(content, source)` (ex. ingestão `.txt` legada).

## PgVectorStore

- Tabela `documents`: `id`, `content`, `embedding`, `source`.
- Busca: `embedding <=> query_embedding` ordenado por distância crescente.
- **Não** implementa rerank, filtros complexos nem BM25 — isso fica nas strategies ou em evoluções futuras.

## Embeddings vs reranking

| Etapa | Modelo | Onde roda |
|-------|--------|-----------|
| Embedding (index + query) | MiniLM L6 v2 (384D) | Local (sentence-transformers) |
| Reranking | MS MARCO MiniLM CrossEncoder | Local |
| Geração | Ollama `phi3` (padrão) ou OpenAI | Local ou API externa |

Separação intencional: **embeddings e rerank sempre locais**; geração configurável (`LLM_PROVIDER`) sem alterar o pipeline RAG.

## Pipeline de avaliação (`app/evaluation/`)

- **`benchmark_runner`:** loop cenários × perguntas do JSON via `execute_rag`.
- **`metrics`:** EM e F1 com normalização estilo SQuAD (+ artigos em português).
- **`export`:** JSON completo + CSV para gráficos do TCC.

Independente da API HTTP — essencial para **reprodutibilidade acadêmica**.

## Desacoplamento e extensão

Para adicionar um novo cenário experimental:

1. Novo valor em `RAGScenario`.
2. Branch em `_select_strategies` escolhendo strategies existentes ou novas.
3. (Opcional) incluir cenário em `DEFAULT_SCENARIOS` do benchmark.

**Não é necessário** alterar `run_rag_pipeline` nem `PgVectorStore` para rerank ou novos prompts — apenas novas classes Strategy.

## Tecnologias (resumo para o TCC)

| Tecnologia | Papel no projeto |
|------------|------------------|
| FastAPI + Uvicorn | API REST |
| SQLAlchemy 2 | ORM e sessões |
| PostgreSQL + pgvector | Persistência e busca vetorial |
| sentence-transformers | Embeddings + CrossEncoder |
| Ollama + langchain-ollama | Geração local (padrão: phi3) |
| OpenAI API | Geração opcional (`LLM_PROVIDER=openai`) |
| MediaWiki API | Corpus Wikipédia PT |
| Pydantic Settings | Configuração por ambiente |

Deploy lógico: [diagrams/deployment.mmd](diagrams/deployment.mmd).
