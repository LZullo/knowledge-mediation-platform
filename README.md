# TCC — RAG comparativo com corpus técnico da Wikipédia (PT)



Protótipo experimental de **Retrieval-Augmented Generation (RAG)** em português: indexação de páginas técnicas da Wikipédia, API FastAPI e benchmark com métricas EM/F1 sobre perguntas manuais.



Documentação completa: [docs/README.md](docs/README.md).



## Pré-requisitos



- **Docker** (PostgreSQL + pgvector)

- **Python 3.11+**

- **Make** (opcional; alternativas em bash abaixo)

- **Ollama** com modelo **phi3** (`ollama pull phi3`) — padrão do projeto (`LLM_PROVIDER=ollama`)

- **OpenAI** ([platform.openai.com](https://platform.openai.com/api-keys)) — somente se `LLM_PROVIDER=openai`

- Internet para baixar páginas da Wikipédia (MediaWiki API)



## Passo a passo — subir e testar



**Subir o banco**



```bash

docker compose up -d

```



**Verificar**



```bash

docker compose ps

```



**Limpar/reindexar os dados**



```bash

python indexar_dados.py

```



`clear_documents=True` apaga embeddings antigos e reindexa do zero.



**Subir a API**



```bash

python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

```



**Rodar o benchmark**



```bash

python -c "import logging; from app.infrastructure.db.connection import SessionLocal; from app.evaluation import run_benchmark_experiment; logging.basicConfig(level=logging.INFO); session = SessionLocal(); out = run_benchmark_experiment(session); session.close(); print(out.report.summaries); print(out.json_path, out.csv_path)"

```



Todos os comandos abaixo assumem o diretório **`tcc-project/`** (raiz deste repositório).



### 1. Subir o banco (Docker)



```bash

docker compose up -d

```



PostgreSQL com pgvector na porta **5433** (usuário/senha/banco: `postgres` / `postgres` / `mba`).



### 2. Ambiente Python e variáveis



```bash

python -m venv venv

```



Ativar o venv:



- **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`

- **Linux/macOS:** `source venv/bin/activate`



Instalar dependências:



```bash

make install

```



Configurar credenciais:



```bash

cp .env.example .env

```



### 3. Criar tabelas



```bash

python create_tables.py

```



### 4. Indexar corpus (Wikipédia técnica controlada)



O script `indexar_dados.py` baixa apenas os tópicos definidos em `WIKI_TOPICS` (`app/dados/wikipedia_loader.py`), aplica chunking e grava embeddings no pgvector.



```bash

python indexar_dados.py

```



Personalizar tópicos ou parâmetros de chunk:



```python

from app.infrastructure.db.connection import SessionLocal

from app.dados.wikipedia_indexer import index_wikipedia_corpus

from app.dados.wikipedia_loader import WIKI_TOPICS



with SessionLocal() as session:

    report = index_wikipedia_corpus(

        session=session,

        topics=WIKI_TOPICS,

        clear_documents=True,

        chunk_size=500,

        chunk_overlap=100,

    )

    print(report)

```



Inspecionar páginas baixadas:



```bash

python inspecionar_wikipedia.py

```



### 5. Subir a API



```bash

make run

```



- Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)



### 6. Testar manualmente



**Retrieval local** (sem LLM):



```bash

python test_retrieval.py

python validar_retrieval.py

```



**Ollama** (geração + RAG; `.env` com `LLM_PROVIDER=ollama`):



```bash

ollama pull phi3

python test_ollama.py

python test_rag_ollama.py

python run_benchmark_ollama.py

```



**Pergunta via API** (usa `LLM_PROVIDER` do `.env`):



```bash

curl -X POST http://127.0.0.1:8000/ask ^

  -H "Content-Type: application/json" ^

  -d "{\"question\":\"O que é machine learning?\",\"scenario\":\"rag_rerank\",\"top_k\":3,\"rerank_top_k\":10}"

```



Cenários: `llm` | `rag_basic` | `rag_optimized` | `rag_rerank`.



### 7. Benchmark experimental (TCC)



Benchmark oficial/final do TCC (v2):

- `corpus_version`: `wikipedia_benchmark_v2`
- perguntas congeladas: `app/dados/benchmark_questions_v2_final.json` (5 perguntas)
- cenários: `llm`, `rag_basic`, `rag_rerank`



```bash

python run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v2 --questions-path app/dados/benchmark_questions_v2_final.json

```



Saídas em `results/` (`benchmark_*.json` e `benchmark_*.csv`).



## Comandos úteis



| Ação | Comando |

|------|---------|

| Subir Postgres | `docker compose up -d` |

| Criar tabelas | `python create_tables.py` |

| Indexar Wikipédia | `python indexar_dados.py` |

| Inspecionar corpus | `python inspecionar_wikipedia.py` |

| Testar retrieval | `python test_retrieval.py` / `python validar_retrieval.py` |

| Testar Ollama (LLM) | `python test_ollama.py` |

| Testar RAG + Ollama | `python test_rag_ollama.py` |

| Benchmark (Ollama) | `python run_benchmark_ollama.py` |

| Benchmark (genérico) | ver seção 7 acima |



## Estrutura (dados)



```

app/dados/

├── wikipedia_loader.py      # MediaWiki API + WIKI_TOPICS

├── chunking.py              # chunk_size / overlap + metadados

├── wikipedia_indexer.py     # pipeline até pgvector

├── benchmark_loader.py      # leitura do JSON de perguntas
├── benchmark_questions.json
└── benchmark_questions_v2_final.json

```



## Adicionar novos tópicos



Edite `WIKI_TOPICS` em `app/dados/wikipedia_loader.py` com o **título exato** da página na Wikipédia em português (como na URL, ex.: `Python_(linguagem_de_programação)`). Depois execute `python indexar_dados.py`.



## Documentação



| Documento | Conteúdo |

|-----------|----------|

| [docs/README.md](docs/README.md) | Guia técnico e reprodução do experimento |

| [docs/methodology.md](docs/methodology.md) | Metodologia, corpus, métricas |

| [docs/experiments.md](docs/experiments.md) | Protocolo de benchmark e análise |

| [docs/architecture.md](docs/architecture.md) | Arquitetura e fluxos |


