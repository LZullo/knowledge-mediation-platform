# Registro de decisões arquiteturais (ADR)

Formato por decisão: **contexto → decisão → alternativas → vantagens → limitações**.

Use este documento na **defesa oral** para demonstrar escolha consciente, não acidental.

---

## ADR-01 — PostgreSQL + pgvector como vector store

**Contexto:** necessidade de persistir chunks, embeddings e consultas por similaridade no mesmo ambiente do TCC, com controle total dos dados.

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

## ADR-02 — SQuAD-pt como corpus e benchmark

**Contexto:** comparar cenários RAG em português com perguntas e respostas de referência.

**Decisão:** dataset **`nunorc/squad_v1_pt`** — contexts indexados; Q&A para métricas EM/F1. Indexação com filtro opcional **`topics`** para corpus de tecnologia (ver `squad_pt_indexer.py`).

**Alternativas:**

| Alternativa | Trade-off |
|-------------|-----------|
| Corpus próprio (ex. São Manuel) | Mais alinhado ao domínio, menos padronização de métricas |
| EN SQuAD traduzido | Menos representativo de linguagem natural PT |
| Apenas LLM sem gold | Impossível EM/F1 rigoroso |

**Vantagens:** métricas comparáveis à literatura; reprodutibilidade; Hugging Face `datasets`.

**Limitações:** domínio Wikipedia/geral; possível desalinhamento pergunta↔chunk após chunking; viés do dataset (ver [limitations.md](limitations.md)).

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

**Vantagens:** extensão de cenários isolada; código testável; narrativa clara para banca (padrão de projeto).

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

**Limitações:** modelo treinado principalmente em EN; latência CPU/GPU adicional; não é o mesmo domínio do SQuAD-pt.

---

## ADR-07 — Chunking por caracteres

**Contexto:** dividir contexts longos para caber no contexto do LLM e melhorar granularidade vetorial.

**Decisão:** janelas de **300 caracteres**, **overlap 50** (`chunk_text`).

**Alternativas:** chunk por tokens (tiktoken); por sentença; semantic chunking.

**Vantagens:** implementação simples, determinística, rápida de explicar.

**Limitações:** pode cortar frases; não otimiza coerência semântica; `chunk_size` na API ainda não reindexa em tempo real.

---

## ADR-08 — PostgreSQL único (dados + vetores + logs)

**Contexto:** reduzir complexidade operacional do TCC.

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

## ADR-10 — OpenAI para geração (não para embeddings/rerank)

**Contexto:** qualidade de resposta em linguagem natural para defesa do protótipo.

**Decisão:** **OpenAI Chat Completions** para geração; embeddings e rerank locais.

**Vantagens:** melhor fluência que modelos open pequenos; integração simples.

**Limitações:** dependência de API, custo, variabilidade entre versões do modelo — documentar `OPENAI_MODEL` e data do experimento.

---

## ADR-11 — Benchmark via `execute_rag` (não HTTP)

**Contexto:** resultados acadêmicos devem ser reproduzíveis.

**Decisão:** módulo `app/evaluation/` chama caso de uso diretamente; export JSON/CSV.

**Alternativas:** apenas `squad_pt_runner` HTTP.

**Vantagens:** remove variância de rede; mais fácil repetir na mesma máquina.

**Limitações:** runner HTTP mantido só para testes integrados opcionais.

---

## ADR-12 — Campo `source` como única metadata estruturada

**Contexto:** modelo `Document` minimalista (4 colunas).

**Decisão:** proveniência em string `source` (ex. `squad-pt/train#12#chunk-0`).

**Alternativas:** JSONB `metadata`, tabela de títulos SQuAD.

**Vantagens:** sem migração complexa; suficiente para rastreio em prompts.

**Limitações:** filtros por metadata na retrieval ainda não implementados (roadmap).
