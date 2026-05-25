# Metodologia experimental

Este capítulo documenta **o pipeline de dados**, **os cenários comparados** e **as métricas** — material direto para a seção de Metodologia do TCC e para slides de apresentação.

## 1. Corpus e benchmark

### Base documental: SQuAD-pt

- Dataset: `nunorc/squad_v1_pt` (Hugging Face).
- **Contexts** → indexados em `documents` (base do RAG).
- **Questions + answers** → usados apenas na **avaliação** (gold standard), não enviados ao modelo na consulta.

**Justificativa:** alinha pergunta e resposta esperada em português, permite métricas padrão (EM/F1) e comparação com literatura QA.

### Filtro de domínio (tecnologia)

O SQuAD-pt cobre títulos variados (entretenimento, esportes, biografias, etc.). Para o TCC, **indexação e benchmark** compartilham o mesmo filtro em `app/dados/squad_pt_filter.py`:

- `is_tech_related(text)` — `TECH_TOPICS` com **regex e word boundaries** (`\b`), sem substring solta.
- `is_tech_squad_item(item)` — aplica apenas em **`context` + `question`** (sem `title`).
- Indexação: `collect_tech_unique_contexts` (contexts únicos).
- Benchmark: `collect_tech_questions` / `get_questions(tech_only=True)` (perguntas do mesmo subconjunto).

Documentos e perguntas irrelevantes são descartados **antes** de embedding ou `execute_rag`.

**Limitação metodológica:** filtro lexical (regex); termos ambíguos em PT/EN podem persistir (ex.: “programação” em sentido não técnico). Evolução: filtro semântico ou classificador de tópico.

### Deduplicação na indexação

Vários registros compartilham o mesmo `context`. Antes do chunking, contexts repetidos são removidos (ordem preservada) para evitar embeddings redundantes e viés de frequência.

O parâmetro **`limit`** define o máximo de **contexts únicos** a indexar (após filtro e deduplicação), percorrendo o split até atingir esse número ou esgotar o dataset.

## 2. Pipeline de ingestão e indexação

```text
context bruto → clean_text → chunk_text → embed_texts → INSERT documents
```

| Etapa | Implementação | Parâmetros padrão |
|-------|---------------|-------------------|
| Limpeza | `utils/text_processing.clean_text` | Unicode NFKC, normalização de espaços |
| Chunking | `chunk_text` | `chunk_size=300`, `overlap=50` (caracteres) |
| Embedding | `all-MiniLM-L6-v2` | 384 dimensões, L2-normalizado |
| Persistência | `index_documents` → `PgVectorStore` | `source=squad-pt/{split}#{idx}#chunk-{n}` |

**Trade-off do chunking por caracteres:** simples e determinístico; não respeita limites de frase/token — discutir na seção de limitações.

## 3. Pipeline de consulta (RAG)

```text
pergunta → [retrieval] → montagem de contexto → prompt → LLM → resposta
```

### 3.1 Retrieval vetorial

1. Embedding da pergunta (mesmo modelo da indexação).
2. Busca top-k por distância cosseno no pgvector.
3. Conversão distância → score de similaridade para resposta API e logs.

### 3.2 Reranking (`rag_rerank`)

1. Recuperar `rerank_top_k` candidatos (padrão 10).
2. Pontuar pares (pergunta, chunk) com CrossEncoder local.
3. Ordenar por score decrescente.
4. Aplicar `score_threshold` opcional.
5. Retornar `top_k` finais ao pipeline de prompt.

Comparável na literatura a **two-stage retrieval** (recall amplo + precisão).

### 3.3 Geração

- Modelo configurável via `OPENAI_MODEL`.
- Prompt inclui instrução de usar apenas o contexto (varia entre cenários).

## 4. Cenários experimentais

Cada cenário isola uma variável de desenho para comparação controlada.

| Cenário | Hipótese de comparação | Retrieval | Prompt | top_k final |
|---------|------------------------|-----------|--------|-------------|
| `llm` | Baseline sem conhecimento externo | — | pergunta direta | — |
| `rag_basic` | RAG mínimo viável | pgvector | padrão | 3 (fixo) |
| `rag_optimized` | RAG + instrução restritiva + k ajustável | pgvector | restritivo | padrão 5 (API) |
| `rag_rerank` | RAG + reranking semântico | pgvector + CrossEncoder | restritivo | padrão 3 |

**Nota metodológica:** `rag_optimized` e `rag_rerank` diferem em **mecanismo de retrieval** e parâmetros padrão de k — ao reportar resultados, documente `top_k` e `rerank_top_k` usados em cada rodada.

### Parâmetros configuráveis

| Parâmetro | Onde | Efeito |
|-----------|------|--------|
| `top_k` | API / benchmark | Chunks finais no contexto (`rag_optimized`, `rag_rerank`) |
| `rerank_top_k` | API / benchmark | Candidatos antes do rerank |
| `score_threshold` | API / `.env` | Descarta chunks com score CrossEncoder baixo |
| `chunk_size` / overlap | Indexação | Granularidade dos trechos na base |
| `tech_only` | Indexação / benchmark | Ativa filtro `is_tech_squad_item` (padrão `True`) |
| `limit` | Indexação | Máximo de contexts únicos indexados |
| `limit` | Benchmark | Quantidade de perguntas SQuAD-pt avaliadas |

## 5. Métricas de avaliação

Implementadas em `app/evaluation/metrics.py`, padrão **SQuAD**:

### Normalização

- minúsculas;
- remoção de pontuação;
- remoção de artigos (EN + PT: *o, a, os, as, um, uma*, etc.);
- colapso de espaços.

### Exact Match (EM)

Proporção de respostas cuja string normalizada é **idêntica** ao gold.  
Rígida; penaliza paráfrases corretas.

### F1 token-level

F1 sobre tokens após normalização; mais tolerante a variações lexicais.  
Usada também como métrica principal em muitos trabalhos QA.

### Métricas operacionais (por execução)

| Métrica | Fonte | Uso no TCC |
|---------|-------|------------|
| Latência (s) | `time.perf_counter` no benchmark | Custo tempo / UX |
| Tokens | `usage` OpenAI quando disponível | Custo financeiro |
| Chunks recuperados | `len(retrieved_chunks)` | Tamanho do contexto |
| Similaridade vetorial | resposta `/ask` | Qualidade retrieval (auxiliar) |

Agregação no benchmark: **média por cenário** sobre N perguntas.

## 6. Protocolo de benchmark reproduzível

1. Indexar contexts (`index_squad_pt_contexts`).
2. Executar `run_benchmark_experiment(session, limit=N)`.
3. Exportar `results/benchmark_*.json` e `.csv`.
4. Gerar gráficos: EM vs cenário, F1 vs cenário, latência vs cenário, tokens vs cenário.

**Não usar HTTP** no experimento principal — evita variância de rede e facilita replicação.

Sequência: [diagrams/benchmark_sequence.mmd](diagrams/benchmark_sequence.mmd).

Detalhes operacionais: [experiments.md](experiments.md).

## 7. O que reportar na dissertação

Sugestão de subseções:

1. **Desenho experimental** — cenários, N perguntas, seed/amostra, hardware.
2. **Configuração** — modelos, k, chunking, versões de dependências.
3. **Métricas** — EM, F1, latência, tokens (média ± desvio se repetir runs).
4. **Resultados** — tabelas/gráficos a partir do CSV.
5. **Discussão** — trade-offs (ver [decisions.md](decisions.md), [limitations.md](limitations.md)).

## 8. Hipóteses qualitativas (para discussão na banca)

- `llm` deve ter EM/F1 baixos em perguntas factuais do corpus, salvo conhecimento paramétrico do modelo.
- `rag_basic` deve superar `llm` quando o chunk correto estiver no top_k.
- `rag_optimized` pode reduzir alucinação com prompt restritivo (qualitativo + F1).
- `rag_rerank` pode melhorar F1 quando o embedding bi-encoder ranqueia mal o chunk certo, à custa de latência.

Validação empírica: seus CSVs exportados.
