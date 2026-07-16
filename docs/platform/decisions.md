# Registro de decisões arquiteturais (ADR)

Formato por decisão: **contexto → decisão → alternativas → vantagens → limitações**.

Use este documento na **defesa oral** para demonstrar escolha consciente, não acidental.

---

## ADR-01 — PostgreSQL + pgvector como vector store

**Contexto:** necessidade de persistir chunks, embeddings e consultas por similaridade no mesmo ambiente local, com controle total dos dados.

**Decisão:** usar **PostgreSQL** com extensão **pgvector** e SQLAlchemy (`PgVectorStore`).

**Alternativas consideradas:**

| Alternativa | Por que não neste projeto |
|-------------|---------------------------|
| Pinecone / Weaviate / Qdrant (SaaS) | Custo, dependência externa, menos alinhado a “stack única” didática |
| Chroma/FAISS em memória | Persistência e concorrência mais frágeis para API + benchmark |
| Elasticsearch híbrido | Complexidade operacional desproporcional ao escopo |

**Vantagens:** um único banco relacional; SQL + vetores; reproduzível em máquina local; integração natural com `experiment_runs`.

**Limitações:** escalar horizontalmente é mais trabalhoso que SaaS especializado; busca híbrida BM25+vetor exige extensão futura.

---

## ADR-02 — Wikipédia técnica (PT) + benchmark manual JSON

**Contexto:** comparar cenários RAG em português com corpus técnico controlado e respostas de referência para EM/F1.

**Decisão:**

- **Indexação:** páginas listadas em `WIKI_TOPICS` (`wikipedia_loader.py`) via MediaWiki API; pipeline `index_wikipedia_corpus` (`wikipedia_indexer.py`).
- **Benchmark:** perguntas/respostas gold em JSON + `benchmark_loader.py`, com **conjunto congelado** para garantir comparabilidade e reprodutibilidade.
- Script operacional: `python scripts/indexing/indexar_dados.py` (chunk 500 / overlap 100 por padrão).

**Alternativas:**

| Alternativa | Trade-off |
|-------------|-----------|
| SQuAD-pt (Hugging Face) | Mais perguntas, menos controle de domínio e de alinhamento página↔pergunta |
| Corpus institucional fechado | Mais realista, menos padronização de métricas |
| Apenas LLM sem gold | Impossível EM/F1 rigoroso |

**Vantagens:** domínio técnico explícito; sem dependência de `datasets`; rastreio por `source` (título, URL, chunk); reprodutível com lista fixa de tópicos.

**Limitações:** N pequeno no JSON atual; qualidade da Wikipédia; possível desalinhamento pergunta↔chunk após chunking (ver [limitations.md](limitations.md)).

**Notas de metodologia (versão consolidada da plataforma):**

- v1 foi tratada como **preliminar exploratória**.
- A tentativa inicial da v2 foi **inválida** (falha antes de exportar JSON/CSV).
- A v2 oficial/final usa `corpus_version=wikipedia_benchmark_v2` e o conjunto congelado `app/dados/benchmark_questions_v2_final.json` (5 perguntas), configurado explicitamente via `questions_path`.

---

## ADR-03 — FastAPI como camada HTTP

**Contexto:** expor `/ask` para demonstração e integração futura.

**Decisão:** **FastAPI** + Uvicorn.

**Alternativas:** Flask (menos tipagem nativa), Django REST (pesado para protótipo).

**Vantagens:** validação Pydantic, OpenAPI, async-ready, adoção em produção.

**Limitações:** experimento batch principal não depende da API — FastAPI é interface, não núcleo científico.

---

## ADR-04 — Strategy Pattern no pipeline RAG

**Contexto:** comparar llm / RAG básico / otimizado / rerank sem duplicar pipeline.

**Decisão:** `run_rag_pipeline` fixo; variar `RetrievalStrategy`, `PromptStrategy`, `GenerationStrategy`; seleção em `execute_rag`.

**Alternativas:** if/else monolítico; microserviços por cenário.

**Vantagens:** extensão de cenários isolada; código testável; padrão de projeto explícito.

**Limitações:** protocolo `retrieve(session, question, top_k)` não expõe todos os parâmetros (rerank configurado na instância da strategy).

---

## ADR-05 — Embeddings locais (sentence-transformers)

**Contexto:** indexar e buscar sem custo por token de embedding API.

**Decisão:** `all-MiniLM-L6-v2` (384D, normalizado).

**Alternativas:** OpenAI `text-embedding-3-*`, modelos multilíngues maiores.

**Vantagens:** gratuito em execução local; latência previsível; dimensão fixa documentada.

**Limitações:** qualidade em português inferior a modelos maiores/multilíngues; mesmo modelo para index e query (obrigatório).

---

## ADR-06 — CrossEncoder local para reranking

**Contexto:** cenário `rag_rerank` comparável a “retrieval de dois estágios”.

**Decisão:** `cross-encoder/ms-marco-MiniLM-L-6-v2` via sentence-transformers.

**Alternativas:** rerank OpenAI; Cohere rerank; LLM como reranker.

**Vantagens:** sem custo de API no rerank; reprodutível; padrão em pipelines de busca.

**Limitações:** modelo treinado principalmente em EN; latência CPU/GPU adicional; domínio técnico PT da Wikipédia pode divergir do treino do cross-encoder.

---

## ADR-07 — Chunking por caracteres

**Contexto:** dividir contexts longos para caber no contexto do LLM e melhorar granularidade vetorial.

**Decisão:** janelas de **300 caracteres**, **overlap 50** (`chunk_text`).

**Alternativas:** chunk por tokens (tiktoken); por sentença; semantic chunking.

**Vantagens:** implementação simples, determinística, rápida de explicar.

**Limitações:** pode cortar frases; não otimiza coerência semântica; `chunk_size` na API ainda não reindexa em tempo real.

---

## ADR-08 — PostgreSQL único (dados + vetores + logs)

**Contexto:** reduzir complexidade operacional da plataforma.

**Decisão:** tabelas `documents` e `experiment_runs` no mesmo PostgreSQL.

**Vantagens:** backup único; transações; familiaridade acadêmica com SQL.

**Limitações:** picos de carga em benchmark + indexação competem no mesmo servidor.

---

## ADR-09 — Não implementar busca híbrida (BM25 + vetor) na v1

**Contexto:** melhorar recall em termos raros (nomes próprios, datas).

**Decisão:** apenas busca **densa** (pgvector) na versão atual.

**Alternativas:** PostgreSQL full-text + fusão RRF; Elasticsearch.

**Vantagens:** escopo controlado; foco na comparação llm vs RAG vs rerank.

**Limitações:** falhas de retrieval por lexical mismatch — trabalho futuro explícito.

---

## ADR-10 — Provedor de LLM plugável (Ollama padrão, OpenAI opcional)

**Contexto:** gerar respostas sem depender de API paga; permitir comparar cenários RAG localmente.

**Decisão:**

- Variável `LLM_PROVIDER` (`ollama` | `openai`), padrão **`ollama`**.
- **Ollama:** `OllamaLLMProvider` + `langchain-ollama` (`ChatOllama`), modelo padrão **`phi3`**, URL `http://localhost:11434`.
- **OpenAI:** `OpenAILLMProvider` / `OpenAIGenerationStrategy` (cliente existente).
- Factory: `get_llm_provider()` e `get_generation_strategy()` em `app/application/providers/factory.py`.
- Embeddings e rerank permanecem **locais** (sem LangChain).

**Alternativas:** só OpenAI; HTTP direto à API Ollama sem LangChain.

**Vantagens:** benchmark e `/ask` reproduzíveis sem `OPENAI_API_KEY`; troca de modelo via `.env`; mesma interface `GenerationStrategy`.

**Limitações:** phi3 local pode ser mais lento e menos fluente que GPT; `tokens_used` é `None` no Ollama; checagem de saúde via `GET /api/tags` antes da geração.

---

## ADR-11 — Benchmark via `execute_rag` (não HTTP)

**Contexto:** resultados acadêmicos devem ser reproduzíveis.

**Decisão:** módulo `app/evaluation/` chama caso de uso diretamente; export JSON/CSV.

**Alternativas:** benchmark apenas via HTTP `/ask`.

**Vantagens:** remove variância de rede; mais fácil repetir na mesma máquina.

**Limitações:** runner HTTP mantido só para testes integrados opcionais.

---

## ADR-12 — Campo `source` como única metadata estruturada

**Contexto:** modelo `Document` minimalista (4 colunas).

**Decisão:** proveniência em string `source` (ex. `wikipedia|topic=PostgreSQL|title=...|url=...|chunk=0`).

**Alternativas:** JSONB `metadata`, tabela relacional de páginas.

**Vantagens:** sem migração complexa; suficiente para rastreio em prompts.

**Limitações:** filtros por metadata na retrieval ainda não implementados (roadmap).
