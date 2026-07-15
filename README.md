# Knowledge Mediation Platform

An open-source software platform for building and evaluating intelligent document question-answering systems based on Large Language Models (LLMs).

The platform provides reusable infrastructure for document ingestion, indexing, retrieval, context construction, language model orchestration, evaluation, and experimentation. It serves as the software foundation for research on intelligent knowledge mediation systems.

---

## Motivation

Modern AI applications require much more than a language model.

Reliable document-based systems depend on reproducible pipelines capable of transforming unstructured information into trustworthy knowledge that can support human decision-making.

Knowledge Mediation Platform was created to provide this reusable software infrastructure, allowing researchers and developers to build, evaluate, and evolve intelligent document consultation systems independently of a specific experimental study.

---

## Research Context

This repository contains **only the reusable software platform**.

Experimental campaigns, benchmarks, statistical analyses, scientific protocols, and research artifacts are intentionally maintained in a separate repository:

- **knowledge-mediation-study** — Scientific experiments and research artifacts
- **research-archive** *(private)* — Historical academic materials and previous research iterations

This separation ensures long-term maintainability, reproducibility, and a clear distinction between reusable software and scientific evidence.

---

## Core Capabilities

- Layered architecture based on the Strategy Pattern
- Document ingestion and corpus indexing
- Dense embeddings using Sentence Transformers
- PostgreSQL + pgvector vector storage
- Retrieval-Augmented Generation (RAG)
- Cross-Encoder reranking
- Local inference using Ollama
- Optional OpenAI integration
- FastAPI REST API
- Automatic evaluation (Exact Match and F1)
- Experimental run management

---

## Architecture

The platform is organized into independent layers:

- Document ingestion
- Corpus indexing
- Embedding generation
- Vector storage
- Retrieval strategies
- Context construction
- LLM orchestration
- Automatic evaluation
- REST API

This modular architecture allows individual components to evolve independently while maintaining a consistent experimentation workflow.

---

## Requirements

| Dependency | Required |
|------------|----------|
| Python 3.11+ | ✅ |
| Docker + Docker Compose | ✅ |
| PostgreSQL + pgvector | ✅ |
| Ollama (default runtime) | ✅ |
| Internet connection (first setup) | ✅ |
| OpenAI API Key | Optional |

---

## Quick Start

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### 2. Create the Python environment

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

cp .env.example .env
```

### 3. Create database tables and index the corpus

```bash
python scripts/indexing/create_tables.py

python scripts/indexing/indexar_corpus.py \
    --version wikipedia_benchmark_v3
```

### 4. Download the language model

```bash
ollama pull phi3
```

### 5. Run the API

```bash
make run
```

or

```bash
python -m uvicorn app.main:app \
    --reload \
    --host 127.0.0.1 \
    --port 8000
```

Swagger:

```
http://127.0.0.1:8000/docs
```

Health endpoint:

```
http://127.0.0.1:8000/health
```

---

## Evaluation

The platform includes a complete evaluation pipeline capable of executing benchmark campaigns and exporting experimental results.

Example:

```bash
python scripts/benchmark/run_benchmark_ollama.py \
    --corpus-version wikipedia_benchmark_v3
```

Generated outputs are stored under `results/`, which is intentionally excluded from version control.

---

## Project Structure

```
knowledge-mediation-platform/
│
├── app/                  # Platform source code
├── scripts/
│   ├── indexing/
│   ├── benchmark/
│   ├── maintenance/
│   └── development/
│
├── docs/
│   ├── architecture/
│   ├── methodology/
│   ├── platform/
│   ├── examples/
│   └── legacy/
│
├── tests/
├── docker-compose.yml
├── requirements.txt
├── LICENSE
└── CITATION.cff
```

---

## Documentation

- Architecture → `docs/architecture/`
- Methodology → `docs/methodology/`
- Platform Decisions → `docs/platform/`
- Examples → `docs/examples/`

---

## Configuration

Configuration parameters are documented in `.env.example`.

The default development environment uses:

- PostgreSQL
- pgvector
- Ollama
- Phi-3
- Sentence Transformers (MiniLM-L6-v2)

---

## Compatibility Notes

The companion repository (`knowledge-mediation-study`) locates this platform through the environment variable:

```
RCC_TCC_PROJECT_ROOT
```

If the variable is not defined, it falls back to the historical sibling directory (`../tcc-project`) to preserve backward compatibility with previous experimental campaigns.

---

## License

This project is distributed under the MIT License.

---

## Citation

If you use this platform in academic work, please cite the software using the information provided in `CITATION.cff`.

For experimental protocols, benchmark datasets, and statistical analyses, please cite the companion repository **knowledge-mediation-study**.
