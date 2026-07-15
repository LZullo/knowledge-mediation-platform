# Scripts da plataforma

Execute sempre a partir da **raiz do repositório**.

| Pasta | Uso |
|-------|-----|
| [`indexing/`](indexing/) | Criar tabelas, indexar corpus Wikipédia, validar tópicos |
| [`benchmark/`](benchmark/) | Runs de avaliação EM/F1 e gráficos auxiliares |
| [`maintenance/`](maintenance/) | Validação de retrieval e migrações |
| [`development/`](development/) | Utilitários de smoke-test (Ollama, DB, retrieval) |

Exemplos:

```bash
python scripts/indexing/create_tables.py
python scripts/indexing/indexar_corpus.py --version wikipedia_benchmark_v3
python scripts/benchmark/run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v3
```
