# Knowledge Mediation Platform

Plataforma local e reutilizável para **consulta documental** com *Retrieval-Augmented Generation* (RAG), voltada a pesquisa e prototipagem em sistemas inteligentes baseados em LLM.

> **Nome institucional do repositório:** `knowledge-mediation-platform`

Este repositório é a **plataforma**. O estudo experimental associado está em [`knowledge-mediation-study`](RELATED_RESEARCH.md).

### Compatibilidade de paths (não alterar)

Os scripts do estudo descobrem a plataforma via variável `RCC_TCC_PROJECT_ROOT` ou, por omissão, a pasta sibling `../tcc-project`.  
Esse default **não foi alterado** (preserva a reprodutibilidade da campanha do artigo). Ao clonar este repositório com o nome institucional, defina `RCC_TCC_PROJECT_ROOT` para o caminho local — ou mantenha um clone/symlink com o nome de pasta esperado pelo default.

---

## O que esta plataforma oferece

- Arquitetura em camadas com **Strategy Pattern** (retrieval, prompt, geração)
- Indexação de corpus (Wikipédia PT e corpora customizados)
- Embeddings densos (`sentence-transformers/all-MiniLM-L6-v2`)
- Armazenamento vetorial **PostgreSQL + pgvector**
- Reranking com cross-encoder
- Geração local via **Ollama** (padrão) ou OpenAI
- API **FastAPI** (`POST /ask`, OpenAPI em `/docs`)
- Avaliação automática **Exact Match / F1** e exportação de runs

---

## Relação com a pesquisa

| Repositório | Papel |
|-------------|--------|
| **Este** (`knowledge-mediation-platform`) | Software / infraestrutura RAG |
| **`knowledge-mediation-study`** | Protocolo, benchmark, campanhas, estatística, artigo |
| **`research-archive`** (privado) | Documentação histórica acadêmica |

Detalhes: [`RELATED_RESEARCH.md`](RELATED_RESEARCH.md).

---

## Pré-requisitos

| Dependência | Obrigatória? |
|-------------|--------------|
| Python 3.11+ | Sim |
| Docker + Compose | Sim (Postgres/pgvector) |
| Ollama + modelo `phi3` | Sim no modo padrão |
| Internet (1ª indexação / download de modelos HF) | Sim na setup |
| OpenAI API key | Não (só se `LLM_PROVIDER=openai`) |

---

## Início rápido

```bash
# 1. Banco
docker compose up -d

# 2. Ambiente
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # ajuste se necessário

# 3. Tabelas + corpus (exemplo)
python scripts/indexing/create_tables.py
python scripts/indexing/indexar_corpus.py --version wikipedia_benchmark_v3

# 4. Ollama
ollama pull phi3

# 5. API
make run
# ou: python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Health: `http://127.0.0.1:8000/health` · Swagger: `http://127.0.0.1:8000/docs`  
Exemplo de chamada: [`docs/examples/quickstart.md`](docs/examples/quickstart.md).

### Benchmark da plataforma

```bash
python scripts/benchmark/run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v3
```

Saídas locais em `results/` (não versionadas).

---

## Estrutura

```text
├── app/                 # Código da plataforma (API, domain, infrastructure…)
├── scripts/
│   ├── indexing/        # Corpus e tabelas
│   ├── benchmark/       # Runs de avaliação
│   ├── maintenance/     # Validação / migrações
│   └── development/     # Utilitários de desenvolvimento
├── docs/
│   ├── architecture/
│   ├── methodology/
│   ├── platform/
│   ├── examples/
│   └── legacy/          # Ponteiro para o arquivo histórico
├── tests/
├── docker-compose.yml
├── requirements.txt
└── RELATED_RESEARCH.md
```

---

## Configuração

Variáveis: [`.env.example`](.env.example).  
Postgres de desenvolvimento: `localhost:5433`, db/user/password `mba` / `postgres` / `postgres` (apenas lab).

---

## Documentação

- Índice: [`docs/README.md`](docs/README.md)
- Arquitetura: [`docs/architecture/architecture.md`](docs/architecture/architecture.md)
- Metodologia / experimentos: [`docs/methodology/`](docs/methodology/)

---

## Licença e citação

Veja [`LICENSE`](LICENSE) e [`CITATION.cff`](CITATION.cff).

Se usar esta plataforma em pesquisa, cite o software e, quando aplicável, o estudo experimental correspondente.
