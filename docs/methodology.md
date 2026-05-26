# Metodologia experimental



Este capítulo documenta **o pipeline de dados**, **os cenários comparados** e **as métricas** — material direto para a seção de Metodologia do TCC e para slides de apresentação.



## 1. Corpus e benchmark



### Base documental: Wikipédia técnica (PT)



- **Fonte:** MediaWiki API (`pt.wikipedia.org`).

- **Lista controlada:** `WIKI_TOPICS` em `app/dados/wikipedia_loader.py` (ex.: Aprendizado de máquina, PostgreSQL, Docker, REST).

- **Texto das páginas** → chunking → embeddings → tabela `documents` (base do RAG).

- **Perguntas de avaliação (v2 oficial):** `app/dados/benchmark_questions_v2_final.json` — pares `question` / `answer` (gold), **não** enviados ao modelo na consulta. Conjunto congelado (5 perguntas) para comparabilidade entre execuções.



**Justificativa:** corpus em português, domínio técnico explícito e reprodutível; benchmark manual alinhado aos tópicos indexados; métricas EM/F1 comparáveis à literatura QA (normalização estilo SQuAD).



### Controle de domínio



O domínio é definido **na origem**, não por filtro pós-hoc em dataset genérico:



- Apenas títulos em `WIKI_TOPICS` são baixados e indexados.

- Páginas com conteúdo abaixo de `_MIN_CONTENT_CHARS` (200) são ignoradas (`topics_skipped` no relatório de indexação).

- Novos tópicos: editar `WIKI_TOPICS` e rodar `python indexar_dados.py`.



**Limitação metodológica:** cobertura limitada à lista de tópicos; qualidade do texto depende da Wikipédia (atualizações, desambiguação de títulos).



### Benchmark manual



- Carregamento: `benchmark_loader.load_benchmark_questions()`.

- Execução: `run_benchmark_experiment` / `run_benchmark_ollama.py` → `execute_rag` por cenário.

- `limit` opcional restringe quantas perguntas do JSON são avaliadas (testes rápidos).



## Organização do Benchmark Experimental

O benchmark experimental v1→v2→v3 foi organizado em subconjuntos para preservar a comparabilidade histórica e, ao mesmo tempo, permitir uma expansão metodológica controlada.

A separação evita a mistura de populações distintas de perguntas ao interpretar variações de EM/F1 e demais métricas. Em particular:

- **core_5** (conjunto histórico):
  - contém as **5 perguntas** utilizadas nos testes v1 e v2;
  - serve como base para comparação quantitativa controlada, preservando o caráter histórico do experimento.

- **extended** (conjunto complementar introduzido na v3):
  - contém as **13 perguntas adicionais** introduzidas no Teste 3;
  - foca em perguntas relacionadas a embeddings, recuperação da informação, bancos vetoriais, busca semântica e sistemas RAG;
  - é utilizado principalmente para robustez interpretativa e análise qualitativa de cobertura temática e adequação do retrieval.

A lógica de comparabilidade deve ser mantida explicitamente:

- **v1 ↔ v2**: comparação quantitativa mais confiável, pois o conjunto base de perguntas (core_5) permanece o mesmo e o procedimento de avaliação foi padronizado.
- **v3**: refinamento experimental e ampliação metodológica; as métricas envolvendo o benchmark expandido podem refletir tanto efeitos do corpus/curadoria quanto efeitos da expansão do conjunto de perguntas.

Por isso, não deve haver inferência direta baseada em métricas agregadas quando o conjunto de perguntas (subset) diferir entre versões, especialmente quando perguntas e gabaritos passaram por refinamentos.

| Subset   | Objetivo                                  |
| -------- | ----------------------------------------- |
| core_5   | comparabilidade histórica                 |
| extended | robustez qualitativa e ampliação temática |

## 2. Pipeline de ingestão e indexação



```text

WIKI_TOPICS → fetch_wikipedia_corpus → clean_text → chunk_text → embed_texts → INSERT documents

```



| Etapa | Implementação | Parâmetros padrão (`indexar_dados.py`) |

|-------|---------------|----------------------------------------|

| Coleta | `wikipedia_loader.fetch_wikipedia_page` | API MediaWiki, User-Agent identificado |

| Limpeza | `utils/text_processing.clean_text` | Unicode NFKC, normalização de espaços |

| Chunking | `chunk_wikipedia_page` | `chunk_size=500`, `overlap=100` (caracteres) |

| Embedding | `all-MiniLM-L6-v2` | 384 dimensões, L2-normalizado |

| Persistência | `index_documents` → `PgVectorStore` | `source` serializado (ver abaixo) |



**Campo `source` (metadata em string):**



```text

wikipedia|topic=<tópico>|title=<título>|url=<url>|chunk=<índice>

```



Parse auxiliar: `chunking.parse_wikipedia_source()`.



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



- Provedor: `LLM_PROVIDER` (`ollama` padrão | `openai`).

- **Ollama:** `OLLAMA_MODEL` (padrão `phi3`), integração `langchain-ollama` (`OllamaGenerationStrategy`).

- **OpenAI:** `OPENAI_MODEL` (`OpenAIGenerationStrategy`).

- Seleção centralizada em `app/application/providers/factory.py`.

- Prompt inclui instrução de usar apenas o contexto (varia entre cenários `PromptStrategy`).



## 4. Cenários experimentais



Cada cenário isola uma variável de desenho para comparação controlada.



| Cenário | Hipótese de comparação | Retrieval | Prompt | top_k final |

|---------|------------------------|-----------|--------|-------------|

| `llm` | Baseline sem conhecimento externo | — | pergunta direta | — |

| `rag_basic` | RAG mínimo viável | pgvector | padrão | configurável (padrão 3) |

| `rag_optimized` | RAG + instrução restritiva + k ajustável | pgvector | restritivo | padrão 5 (API) |

| `rag_rerank` | RAG + reranking semântico | pgvector + CrossEncoder | restritivo | padrão 3 |



**Nota metodológica:** `rag_optimized` e `rag_rerank` diferem em **mecanismo de retrieval** e parâmetros padrão de k — ao reportar resultados, documente `top_k` e `rerank_top_k` usados em cada rodada.



### Parâmetros configuráveis



| Parâmetro | Onde | Efeito |

|-----------|------|--------|

| `top_k` | API / benchmark | Chunks finais no contexto (`rag_basic`, `rag_optimized`, `rag_rerank`) |

| `rerank_top_k` | API / benchmark | Candidatos antes do rerank |

| `score_threshold` | API / `.env` | Descarta chunks com score CrossEncoder baixo |

| `chunk_size` / overlap | Indexação (`index_wikipedia_corpus`) | Granularidade dos trechos na base |

| `LLM_PROVIDER` | `.env` | `ollama` ou `openai` |

| `OLLAMA_MODEL` | `.env` | Modelo local (ex. `phi3`) |

| `OPENAI_MODEL` | `.env` | Modelo OpenAI (se `LLM_PROVIDER=openai`) |

| `limit` | Benchmark | Quantidade de perguntas do JSON avaliadas |



## 5. Métricas de avaliação



Implementadas em `app/evaluation/metrics.py`, com **normalização inspirada no SQuAD** (EM/F1 token-level):



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

| Tokens | OpenAI `usage` quando disponível; `None` no Ollama | Custo financeiro (se OpenAI) |

| Chunks recuperados | `len(retrieved_chunks)` | Tamanho do contexto |

| Tamanho do prompt | caracteres em `experiment_runs.parameters` | Carga no LLM |

| Similaridade vetorial | resposta `/ask` | Qualidade retrieval (auxiliar) |



Agregação no benchmark: **média por cenário** sobre N perguntas.



## 6. Protocolo de benchmark reproduzível



1. Indexar corpus (`python indexar_dados.py` → `index_wikipedia_corpus`).

2. Garantir Ollama (`ollama pull phi3`) ou `OPENAI_API_KEY` conforme `LLM_PROVIDER`.

3. Executar `python run_benchmark_ollama.py` ou `run_benchmark_experiment(session, ...)`.

4. Exportar `results/benchmark_*.json` e `.csv`.

5. Gerar gráficos: EM vs cenário, F1 vs cenário, latência vs cenário.


## 6.1 Evolução metodológica do benchmark (v1 → v2 oficial)

- **v1 (preliminar exploratório):** executado para validar o pipeline e levantar hipóteses iniciais; resultados preservados como histórico, não como versão final do experimento.
- **Tentativa inicial da v2 (inválida):** execução interrompida (Ollama indisponível) antes da geração dos artefatos finais (JSON/CSV), portanto não compõe a base oficial de resultados.
- **v2 (oficial/final):** consolida correções metodológicas e padroniza os artefatos experimentais:
  - **corpus versionado:** `wikipedia_benchmark_v2` como referência oficial (expansão de cobertura e rastreabilidade por `corpus_version`);
  - **perguntas congeladas:** `app/dados/benchmark_questions_v2_final.json` (5 perguntas) configurado explicitamente via `questions_path`;
  - **correção de comparabilidade:** o cenário `rag_basic` passa a respeitar `top_k` parametrizado pelo benchmark (antes havia comportamento fixo que quebrava o controle de variáveis).


## 6.2 Reprodutibilidade experimental (protocolo oficial v2)

**Configuração experimental (registrar no capítulo experimental):**

- `corpus_version`: `wikipedia_benchmark_v2`
- `questions_path`: `app/dados/benchmark_questions_v2_final.json`
- cenários: `llm`, `rag_basic`, `rag_rerank`
- modelo (Ollama): `OLLAMA_MODEL=phi3`
- temperatura: `LLM_TEMPERATURE=0`
- `top_k`: 5
- `rerank_top_k`: 10

**Artefatos gerados (saída):**

- `results/benchmark_<run_id>.json` — relatório completo (`summaries` + `results`)
- `results/benchmark_<run_id>.csv` — uma linha por (cenário, pergunta), para tabelas/gráficos

**Validação do Ollama (pré-execução):**

```bash
curl http://localhost:11434/api/tags
ollama pull phi3
```

**Comando oficial de execução (v2):**

```bash
python run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v2 --questions-path app/dados/benchmark_questions_v2_final.json
```

## 6.3 Teste 3 — corpus refinado (v3, protocolo controlado)

**Motivação:** a v2 planejou 12 tópicos e indexou 2; lacunas documentais (pgvector) e gabaritos minimalistas limitaram a validade das métricas. A v3 **não** altera embeddings, retrieval nem rerank — refina corpus, benchmark e geração.

**Configuração (registrar no capítulo experimental):**

- `corpus_version`: `wikipedia_benchmark_v3`
- `questions_path`: `app/dados/benchmark_questions_v3.json` (18 perguntas; subconjuntos `core_5`, `extended`)
- validação prévia: `python validate_wiki_topics_v3.py` → `results/wiki_topic_validation_wikipedia_benchmark_v3.json`
- corpus complementar: `docs/custom_corpus/pgvector.md` (fonte oficial documentada)
- `OLLAMA_NUM_PREDICT=256`, `OLLAMA_REPEAT_PENALTY=1.15` (via `.env` / `Settings`)
- instrução de prompt: resposta objetiva em 1–3 frases

**Comparabilidade de métricas:**

- **Não** comparar F1 global Teste 3 vs Teste 1/2 sem separar efeitos de gabarito, N perguntas e cobertura.
- Subconjunto `core_5`: mesmas perguntas históricas; gabaritos refinados → F1 não é diretamente comparável aos JSON antigos.

**Comando de execução (v3):**

```bash
python validate_wiki_topics_v3.py
python indexar_corpus.py --version wikipedia_benchmark_v3 --no-incremental
python run_benchmark_ollama.py --corpus-version wikipedia_benchmark_v3
```

Documentação: [corpus_evolution.md](corpus_evolution.md), [preliminary_results_test_3.md](preliminary_results_test_3.md).


**Não usar HTTP** no experimento principal — evita variância de rede e facilita replicação.



Sequência: [diagrams/benchmark_sequence.mmd](diagrams/benchmark_sequence.mmd).



Detalhes operacionais: [experiments.md](experiments.md).



## 7. O que reportar na dissertação



Sugestão de subseções:



1. **Desenho experimental** — cenários, N perguntas, `WIKI_TOPICS`, hardware.

2. **Configuração** — `LLM_PROVIDER`, modelos (phi3 / OpenAI), k, chunking, versões de dependências.

3. **Métricas** — EM, F1, latência, tokens (média ± desvio se repetir runs).

4. **Resultados** — tabelas/gráficos a partir do CSV.

5. **Discussão** — trade-offs (ver [decisions.md](decisions.md), [limitations.md](limitations.md)).



## 8. Hipóteses qualitativas (para discussão na banca)



- `llm` deve ter EM/F1 baixos em perguntas factuais do corpus, salvo conhecimento paramétrico do modelo.

- `rag_basic` deve superar `llm` quando o chunk correto estiver no top_k.

- `rag_optimized` pode reduzir alucinação com prompt restritivo (qualitativo + F1).

- `rag_rerank` pode melhorar F1 quando o embedding bi-encoder ranqueia mal o chunk certo, à custa de latência.



Validação empírica: seus CSVs exportados.



## 9. Limitações das Métricas EM/F1 em Respostas Generativas

Esta seção formaliza limitações observadas nos Testes 1 e 2 (`run_id` `20260525_160434` e `20260526_020326`), nos quais **EM = 0** em todas as perguntas e cenários, enquanto o **F1** capturou diferenças entre `llm`, `rag_basic` e `rag_rerank`.

### 9.1 Respostas semanticamente corretas com EM = 0

O Exact Match exige igualdade literal após normalização (minúsculas, remoção de pontuação e artigos). Gabaritos do benchmark são definições de **uma linha** (ex.: *“Estilo de arquitetura de software”* para REST). Respostas que descrevem corretamente REST como estilo arquitetural baseado em HTTP recebem **EM = 0** por divergência lexical e extensão. Nos dois testes preliminares, nenhuma resposta atingiu EM positivo — o que **não** implica ausência de correção semântica.

### 9.2 Respostas mais longas penalizadas lexicalmente

Modelos generativos — em especial o `phi3` local — tendem a produzir parágrafos explicativos. O F1 token-level calcula precisão e revocação de tokens entre resposta e gabarito; tokens adicionais na hipótese (resposta longa) **reduzem a precisão** mesmo quando factualmente aceitáveis. Por isso:

- o baseline `llm` mantém F1 médio baixo (≈ 0,030);
- cenários RAG com respostas mais concisas elevam F1 (≈ 0,11–0,13 no Teste 1);
- falhas de **prolixidade extrema** (repetição em loop no Teste 2, pergunta REST, `rag_rerank`) destroem F1 (≈ 0,004) independentemente da correção inicial.

### 9.3 Adequação parcial do F1 para LLMs generativos

O F1 sobre tokens normalizados é **mais discriminativo que o EM** neste protocolo (evidenciado pelos ganhos de RAG nos Testes 1 e 2), mas permanece:

- **insensível** a paráfrases sem sobreposição lexical;
- **insensível** a erros factuais com vocabulário coincidente;
- **sensível** a idioma e a modelos de embedding/rerank anglófonos aplicados a português.

Valores absolutos de F1 abaixo de 0,30 coexistem, em inspeção qualitativa, com respostas parcialmente adequadas (ex.: PostgreSQL como SGBDOR com F1 = 0,296).

### 9.4 Motivação para futura avaliação qualitativa

Recomenda-se complementar EM/F1 com:

1. **Avaliação humana** em escala de adequação factual e concisão (ex.: 1–5 por pergunta e cenário).
2. **Métricas semânticas** (BERTScore, embeddings de similaridade) calibradas para português.
3. **Rubricas por pergunta** que separarem “definição mínima” de “explicação aceitável”.
4. **Registro de falhas de geração** (repetição, recusa, alucinação) fora do escopo lexical.

Os benchmarks históricos em `results/` devem ser preservados; novas rodadas devem acrescentar colunas ou relatórios de avaliação qualitativa **sem sobrescrever** métricas automáticas já exportadas.

Documentação analítica: [preliminary_results_test_2.md](preliminary_results_test_2.md), [discussion_preliminary_findings.md](discussion_preliminary_findings.md).


