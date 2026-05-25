# Documentação técnica — TCC (RAG + Wikipédia técnica PT)

Documentação pensada para **escrita do TCC**, **apresentação à banca**, **reprodução do experimento** e **defesa das escolhas arquiteturais**.

## Índice

| Documento | Uso principal |
|-----------|----------------|
| [architecture.md](architecture.md) | Capítulo de arquitetura / diagrama de componentes |
| [methodology.md](methodology.md) | Metodologia experimental e pipeline de dados |
| [experiments.md](experiments.md) | Protocolo de benchmark e análise de resultados |
| [decisions.md](decisions.md) | Registro de decisões (ADR) para defesa |
| [limitations.md](limitations.md) | Limitações honestas + trabalhos futuros |
| [diagrams/](diagrams/) | Diagramas Mermaid (slides e texto) |

Guia rápido na raiz do repositório: [../README.md](../README.md).

## Visão em uma página

```
Wikipédia (tópicos controlados) → extract texto → chunk + embedding → pgvector
Pergunta (benchmark manual JSON) → /ask ou benchmark → retrieve → prompt → OpenAI → métricas EM/F1
```

**Cenários comparados:** `llm` | `rag_basic` | `rag_optimized` | `rag_rerank`

## Passo a passo — reproduzir localmente

Executar na raiz **`tcc-project/`**.

### 1. PostgreSQL + pgvector (Docker)

```bash
docker compose up -d
docker compose ps
```

- Imagem: `pgvector/pgvector:pg16`
- Porta host: **5433** → container `5432`
- Banco: `mba` | usuário/senha: `postgres` / `postgres`

### 2. Python, dependências e `.env`

```bash
python -m venv venv
# Windows:  .\venv\Scripts\Activate.ps1
# Linux:    source venv/bin/activate

make install
# alternativa: pip install -r requirements.txt

cp .env.example .env
```

Ajustar em `.env`:

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5433/mba`
- `OPENAI_API_KEY=...`
- `VECTOR_DIMENSIONS=384` (MiniLM)

### 3. Criar tabelas

```bash
python create_tables.py
```

### 4. Indexar corpus Wikipédia (tópicos técnicos controlados)

Script pronto na raiz:

```bash
python indexar_dados.py
```

Lista de páginas em `app/dados/wikipedia_loader.py` (`WIKI_TOPICS`). Chunk padrão: 500 caracteres, overlap 100.

```bash
python inspecionar_wikipedia.py
```

Equivalente em Python:

```python
from app.infrastructure.db.connection import SessionLocal
from app.dados.wikipedia_indexer import index_wikipedia_corpus

with SessionLocal() as session:
    report = index_wikipedia_corpus(
        session=session,
        clear_documents=True,
        chunk_size=500,
        chunk_overlap=100,
    )
    print(report)
```

Campos do relatório (`WikipediaIndexingReport`):

| Campo | Significado |
|-------|-------------|
| `topics_requested` | Tópicos solicitados em `WIKI_TOPICS` |
| `pages_fetched` | Páginas baixadas com sucesso |
| `topics_skipped` | Tópicos ignorados (vazio, inexistente ou curto) |
| `chunks_total` | Chunks gravados em `documents` |

### 5. Subir a API

```bash
make run
```

- Swagger: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

### 6. Testes rápidos

**Retrieval** (local, sem OpenAI):

```bash
python test_retrieval.py
```

**Consulta RAG** (`POST /ask`):

```json
{
  "question": "O que é machine learning?",
  "scenario": "rag_rerank",
  "top_k": 3,
  "rerank_top_k": 10
}
```

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"O que é Python?","scenario":"rag_rerank","top_k":3,"rerank_top_k":10}'
```

### 7. Benchmark (recomendado para o TCC)

Usa `execute_rag` **diretamente** (reproduzível, sem HTTP):

```python
import logging
from app.infrastructure.db.connection import SessionLocal
from app.evaluation import run_benchmark_experiment

logging.basicConfig(level=logging.INFO)

with SessionLocal() as session:
    out = run_benchmark_experiment(session)

print(out.report.summaries)
print(out.json_path, out.csv_path)
```

Saídas em `tcc-project/results/`:

- `benchmark_YYYYMMDD_HHMMSS.json` — relatório completo
- `benchmark_YYYYMMDD_HHMMSS.csv` — tabela para gráficos

## Pré-requisitos

- Python 3.11+
- Docker (PostgreSQL + pgvector)
- Chave **OpenAI** (geração de respostas)
- Conexão à internet para a MediaWiki API (`pt.wikipedia.org`)

## Indexação — parâmetros principais

| Parâmetro | Padrão | Efeito |
|-----------|--------|--------|
| `topics` | `WIKI_TOPICS` | Lista controlada de páginas da Wikipédia |
| `clear_documents` | `False` | Apaga `documents` antes de indexar |
| `chunk_size` / `chunk_overlap` | `500` / `100` | Granularidade dos chunks |

Corpus e benchmark: `app/dados/wikipedia_loader.py`, `app/dados/benchmark_questions.json`.

## Estrutura do repositório

```
tcc-project/
├── app/                    # Código da aplicação
│   ├── api/                # FastAPI (rotas, schemas)
│   ├── application/        # Casos de uso, pipeline RAG, strategies
│   ├── core/               # Configuração (Settings)
│   ├── dados/              # Wikipédia: loader, chunking, indexação, benchmark JSON
│   ├── evaluation/         # Métricas EM/F1, benchmark, export
│   ├── experiments/        # Lotes internos → experiment_runs
│   ├── infrastructure/     # DB, embeddings, pgvector, OpenAI, rerank
│   └── utils/              # chunking, limpeza de texto
├── docs/                   # Esta documentação
├── results/                # Saídas de benchmark (gitignored)
├── docker-compose.yml
├── Makefile
├── indexar_dados.py
├── create_tables.py
└── .env.example
```

## Diagramas

Renderize os `.mmd` no [Mermaid Live Editor](https://mermaid.live) ou no VS Code (extensão Mermaid). Arquivos:

- `diagrams/architecture.mmd` — componentes e camadas
- `diagrams/ask_sequence.mmd` — sequência do `/ask`
- `diagrams/benchmark_sequence.mmd` — pipeline de avaliação
- `diagrams/deployment.mmd` — deploy lógico

## Ordem sugerida para o experimento do TCC

1. `docker compose up -d` e `.env` configurado  
2. `python create_tables.py`  
3. `python indexar_dados.py` (corpus tech)  
4. `make run` (demonstração) ou `run_benchmark_experiment` (métricas)  
5. Analisar CSV/JSON em `results/`  
6. Consultar [decisions.md](decisions.md) e [limitations.md](limitations.md) na discussão  

## Referência rápida de cenários

| `scenario` | Retrieval | Prompt | top_k |
|------------|-----------|--------|-------|
| `llm` | nenhum | pergunta direta | — |
| `rag_basic` | pgvector | contexto + instrução padrão | 3 (fixo) |
| `rag_optimized` | pgvector | contexto restritivo | configurável (padrão 5) |
| `rag_rerank` | pgvector expandido + CrossEncoder | contexto restritivo | final configurável (padrão 3), `rerank_top_k` padrão 10 |
