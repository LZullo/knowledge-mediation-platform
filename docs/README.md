# Documentação técnica — TCC (RAG + Wikipédia técnica PT)

Documentação pensada para **escrita do TCC**, **apresentação à banca**, **reprodução do experimento** e **defesa das escolhas arquiteturais**.

## Índice

| Documento | Uso principal |
|-----------|----------------|
| [architecture.md](architecture.md) | Capítulo de arquitetura / diagrama de componentes |
| [methodology.md](methodology.md) | Metodologia experimental e pipeline de dados |
| [experiments.md](experiments.md) | Protocolo de benchmark e análise de resultados |
| [corpus_evolution.md](corpus_evolution.md) | Versionamento e expansão do corpus |
| [preliminary_results_test_1.md](preliminary_results_test_1.md) | Resultados preliminares — Teste 1 (v1) |
| [preliminary_results_test_2.md](preliminary_results_test_2.md) | Resultados preliminares — Teste 2 (v2) |
| [discussion_preliminary_findings.md](discussion_preliminary_findings.md) | Discussão interpretativa Testes 1 e 2 |
| [decisions.md](decisions.md) | Registro de decisões (ADR) para defesa |
| [limitations.md](limitations.md) | Limitações honestas + trabalhos futuros |
| [diagrams/](diagrams/) | Diagramas Mermaid (slides e texto) |

Guia rápido na raiz do repositório: [../README.md](../README.md).

## Visão em uma página

```
Wikipédia (tópicos controlados) → extract texto → chunk + embedding → pgvector
Pergunta (benchmark manual JSON) → /ask ou benchmark → retrieve → prompt → LLM (Ollama phi3 ou OpenAI) → métricas EM/F1
```

**Cenários comparados:** `llm` | `rag_basic` | `rag_optimized` | `rag_rerank`

## Fluxo experimental v1 → v2 e rastreabilidade

O TCC adota evolução **incremental** do corpus e dos benchmarks, sem apagar evidências anteriores.

| Etapa | Corpus | Benchmark (`run_id`) | Documentação |
|-------|--------|----------------------|--------------|
| Teste 1 | `wikipedia_benchmark_v1` (rótulo legado: `wikipedia_benchmark`) | `20260525_160434` | [preliminary_results_test_1.md](preliminary_results_test_1.md) |
| Expansão incremental | `wikipedia_benchmark_v2` (+35 chunks; índice cumulativo 446) | — | [corpus_evolution.md](corpus_evolution.md) |
| Teste 2 | `wikipedia_benchmark_v2` | `20260526_020326` | [preliminary_results_test_2.md](preliminary_results_test_2.md) |
| Discussão consolidada | — | Comparação v1 vs v2 | [discussion_preliminary_findings.md](discussion_preliminary_findings.md) |

**Evolução incremental do corpus:** a v2 acrescenta tópicos de recuperação de informação e ferramentas RAG sobre a v1, com deduplicação e indexação incremental (`python indexar_corpus.py --version wikipedia_benchmark_v2`). Relatórios: `results/corpus_report_wikipedia_benchmark_v1.json` e `v2.json`.

**Preservação dos benchmarks históricos:** ficheiros em `results/benchmark_*.json` e `.csv` **não devem ser sobrescritos** nem ter métricas recalculadas retroativamente. Metadados de nomenclatura (ex.: `corpus_version` no Teste 1) podem ser padronizados apenas quando documentados como equivalência, sem alterar EM/F1/latências/respostas.

**Importância da rastreabilidade:** cada execução exporta `run_id`, `corpus_version`, modelos de embedding/rerank/LLM e agregados por cenário — condição necessária para comparar Teste 1 e Teste 2 na dissertação e para replicar o protocolo (ver [experiments.md](experiments.md), secção comparação v1 vs v2).

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
- `LLM_PROVIDER=ollama` (padrão do projeto) ou `openai`
- `OLLAMA_MODEL=phi3` e `OLLAMA_BASE_URL=http://localhost:11434` (geração local)
- `OPENAI_API_KEY=...` (somente se `LLM_PROVIDER=openai`)
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

**Retrieval** (local, sem LLM):

```bash
python test_retrieval.py
python validar_retrieval.py
```

**Ollama** (geração local; padrão `phi3` via `OLLAMA_MODEL`):

```bash
ollama pull phi3
curl http://localhost:11434/api/tags

python test_ollama.py
python test_rag_ollama.py
python run_benchmark_ollama.py
```

**Consulta RAG** (`POST /ask` — usa o provedor de `LLM_PROVIDER`):

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
- **Ollama** rodando localmente (padrão: modelo `phi3`) **ou** chave **OpenAI** se `LLM_PROVIDER=openai`
- Conexão à internet para a MediaWiki API (`pt.wikipedia.org`)

## Indexação — parâmetros principais

| Parâmetro | Padrão | Efeito |
|-----------|--------|--------|
| `topics` | `WIKI_TOPICS` | Lista controlada de páginas da Wikipédia |
| `clear_documents` | `False` | Apaga `documents` antes de indexar |
| `chunk_size` / `chunk_overlap` | `500` / `100` | Granularidade dos chunks |

Corpus e benchmark (v2 oficial): `app/dados/wikipedia_loader.py`, `app/dados/benchmark_questions_v2_final.json`.

## Estrutura do repositório

```
tcc-project/
├── app/                    # Código da aplicação
│   ├── api/                # FastAPI (rotas, schemas)
│   ├── application/        # Casos de uso, pipeline RAG, strategies, providers (LLM)
│   ├── core/               # Configuração (Settings)
│   ├── dados/              # Wikipédia: loader, chunking, indexação, benchmark JSON
│   ├── evaluation/         # Métricas EM/F1, benchmark, export
│   ├── experiments/        # Lotes internos → experiment_runs
│   ├── infrastructure/     # DB, embeddings, pgvector, cliente OpenAI, rerank
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
| `rag_basic` | pgvector | contexto + instrução padrão | configurável (padrão 3) |
| `rag_optimized` | pgvector | contexto restritivo | configurável (padrão 5) |
| `rag_rerank` | pgvector expandido + CrossEncoder | contexto restritivo | final configurável (padrão 3), `rerank_top_k` padrão 10 |

## Provedor de LLM (Ollama vs OpenAI)

| Variável | Padrão | Função |
|----------|--------|--------|
| `LLM_PROVIDER` | `ollama` | `ollama` ou `openai` |
| `OLLAMA_MODEL` | `phi3` | Modelo no Ollama (`ollama pull phi3`) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Endpoint do servidor Ollama |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | Usado só com `LLM_PROVIDER=openai` |

Seleção em código: `app/application/providers/factory.py` (`get_llm_provider`, `get_generation_strategy`).

| Strategy | Classe | Provedor |
|----------|--------|----------|
| Geração OpenAI | `OpenAIGenerationStrategy` | `openai_client.generate_from_prompt` |
| Geração Ollama | `OllamaGenerationStrategy` | `OllamaLLMProvider` + `langchain_ollama.ChatOllama` |

Dependência: `langchain-ollama` em `requirements.txt`.
