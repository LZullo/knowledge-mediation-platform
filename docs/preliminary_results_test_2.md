# Resultados Preliminares — Benchmark de Teste 2

**Identificador da execução:** `20260526_020326`  
**Data da execução:** 26/05/2026, 03:07:13 UTC  
**Artefatos:** `results/benchmark_20260526_020326.json`, `results/benchmark_20260526_020326.csv`  
**Corpus:** `wikipedia_benchmark_v2` (recuperação cumulativa sobre documentos v1 + v2)  
**Comparativo de referência (Teste 1):** `results/benchmark_20260525_160434.json` (`wikipedia_benchmark_v1`)

---

## 1. Objetivo do experimento

O Teste 2 avalia o impacto da **expansão controlada e versionada do corpus** sobre o desempenho do pipeline RAG, mantendo o protocolo comparável ao Teste 1: mesmas cinco perguntas técnicas em português, mesmos três cenários (`llm`, `rag_basic`, `rag_rerank`), temperatura zero e modelos de embedding, reranking e geração documentados no artefato de exportação.

A hipótese central é que o aumento da **cobertura documental** — em especial em tópicos de recuperação de informação e ferramentas do ecossistema RAG — eleva a sobreposição lexical (F1) e a adequação factual das respostas ancoradas em contexto, sem alterar o baseline paramétrico (`llm`). O experimento **não** substitui o Teste 1: ambos os benchmarks permanecem arquivados para comparação longitudinal e rastreabilidade metodológica.

---

## 2. Evolução do corpus

### 2.1 Estado do Teste 1 (`wikipedia_benchmark_v1`)

Conforme `results/corpus_report_wikipedia_benchmark_v1.json`:

| Indicador | Valor |
|-----------|-------|
| Documentos/chunks indexados | 411 |
| Tópicos com chunks | 9 |
| Tamanho médio do chunk | 494,91 caracteres |
| Parâmetros de chunking | 500 / overlap 100 |

### 2.2 Expansão incremental do Teste 2 (`wikipedia_benchmark_v2`)

Conforme `results/corpus_report_wikipedia_benchmark_v2.json`:

| Indicador | Valor |
|-----------|-------|
| Novos documentos/chunks (rodada incremental) | 35 |
| Tópicos efetivamente indexados nesta rodada | 2 (`Recuperação_de_informação`, `LangChain`) |
| Tópicos solicitados e ignorados (já presentes ou indisponíveis) | 10 |
| Tamanho médio do chunk (expansão) | 480,63 caracteres |

O benchmark do Teste 2 registra **446** documentos/chunks visíveis na recuperação (`corpus_document_count` / `corpus_chunk_count` no JSON), consistente com índice **cumulativo** (v1 + acréscimo v2). Onze tópicos aparecem em `corpus_topics_indexed` no artefato de benchmark, incluindo os nove da v1 e os dois acrescentados na expansão.

### 2.3 Lacuna persistente: pgvector

A expansão v2 **não** indexou conteúdo específico sobre a extensão **pgvector** do PostgreSQL. Tópicos planejados como *Embedding*, *Banco de dados vetorial* e similares foram majoritariamente ignorados na rodada incremental (já cobertos ou sem página adequada na Wikipédia PT). Assim, a pergunta sobre pgvector continua dependente de material indireto (PostgreSQL, redes neurais), o que limita a validade de inferências sobre “melhoria universal” do RAG após a expansão.

---

## 3. Configuração experimental

| Componente | Configuração (Teste 2) |
|------------|------------------------|
| **Corpus version** | `wikipedia_benchmark_v2` |
| **Perguntas** | 5 (mesmo conjunto do Teste 1) |
| **Cenários** | `llm`, `rag_basic`, `rag_rerank` |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Reranking** | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| **LLM** | Ollama, `phi3`, temperatura `0.0` |
| **top_k** | 5 |
| **chunk_size (metadado do benchmark)** | 300 caracteres |
| **run_id** | `20260526_020326` |

**Nota metodológica:** o campo `chunk_size_config=300` no artefato de benchmark refere-se à configuração reportada na execução; o corpus indexado utiliza janelas de **500** caracteres com overlap **100** (v1/v2). Essa discrepância deve ser explicitada na dissertação ao interpretar granularidade de recuperação versus metadado exportado.

O Teste 1 apresenta configuração equivalente nos cenários e hiperparâmetros de inferência; diferença estrutural relevante: na v1, `rag_basic` recuperou em média **3,0** chunks por pergunta, enquanto na v2 a média foi **5,0** (alinhada ao `top_k=5`).

---

## 4. Comparação v1 vs v2

### 4.1 Tabela comparativa — F1 médio por cenário

Valores extraídos dos campos `summaries` dos artefatos JSON (sem arredondamento na origem; apresentação com quatro casas decimais).

| Cenário | v1 F1 (Teste 1) | v2 F1 (Teste 2) | Diferença (v2 − v1) | Variação relativa |
|---------|----------------|-----------------|---------------------|-------------------|
| `llm` | 0,0301 | 0,0301 | 0,0000 | 0% |
| `rag_basic` | 0,1116 | 0,1188 | **+0,0072** | +6,4% |
| `rag_rerank` | 0,1317 | 0,1216 | **−0,0100** | −7,6% |

### 4.2 Tabela comparativa — latência média (s)

| Cenário | v1 latência (s) | v2 latência (s) | Diferença (v2 − v1) |
|---------|-----------------|-----------------|---------------------|
| `llm` | 120,21 | 152,43 | +32,22 |
| `rag_basic` | 74,66 | 170,70 | +96,04 |
| `rag_rerank` | 133,16 | 435,74 | **+302,58** |

### 4.3 Tabela comparativa — F1 por pergunta (`rag_basic`)

| Pergunta | v1 F1 | v2 F1 | Diferença |
|----------|-------|-------|-----------|
| Machine learning | 0,154 | **0,286** | +0,132 |
| PostgreSQL | 0,111 | 0,103 | −0,008 |
| REST | 0,087 | 0,081 | −0,006 |
| Docker | 0,073 | 0,056 | −0,017 |
| pgvector | **0,133** | 0,069 | −0,064 |

### 4.4 Tabela comparativa — F1 por pergunta (`rag_rerank`)

| Pergunta | v1 F1 | v2 F1 | Diferença |
|----------|-------|-------|-----------|
| Machine learning | 0,178 | 0,186 | +0,008 |
| PostgreSQL | **0,296** | **0,296** | 0,000 |
| REST | 0,085 | **0,004** | −0,081 |
| Docker | 0,043 | 0,056 | +0,013 |
| pgvector | 0,056 | 0,067 | +0,011 |

### 4.5 Exact Match

Em **ambos** os testes, **EM médio = 0,000** em todos os cenários e perguntas. Nenhuma resposta reproduziu literalmente o gabarito ultra-curto após normalização.

### 4.6 Baseline `llm` invariante

O F1 médio e as respostas do cenário `llm` são **idênticos** entre Teste 1 e Teste 2 (mesmos valores por pergunta no JSON). Isso corrobora a reprodutibilidade do baseline paramétrico e confirma que alterações observadas nos cenários RAG devem ser atribuídas principalmente ao índice e ao pipeline de recuperação, não a variação aleatória do modelo na temperatura zero.

---

## 5. Discussão das métricas

### 5.1 Exact Match (EM) permanece nulo

Os gabaritos possuem entre quatro e nove palavras (definições minimalistas). O modelo `phi3` produz parágrafos explicativos. A métrica EM exige igualdade literal pós-normalização; respostas semanticamente adequadas recebem EM = 0. Esse padrão é **estável** entre v1 e v2 e não deve ser interpretado como ausência total de acerto factual.

### 5.2 F1 como métrica mais representativa neste desenho

O F1 token-level captura sobreposição parcial com o gabarito (ex.: *“subcampo”*, *“objeto relacional”*). No Teste 2:

- **`rag_basic`** apresentou ganho médio de F1 (+0,0072) em relação à v1, com destaque em *machine learning* (0,286 vs. 0,154).
- **`rag_rerank`** apresentou **queda** média (−0,0100), dominada pelo colapso lexical na pergunta REST (ver Seção 7).

O F1 **não** mede equivalência semântica completa nem factualidade; valores absolutos baixos (< 0,30) coexistem com respostas que um avaliador humano poderia aceitar parcialmente.

### 5.3 Impacto de respostas curtas esperadas

Gabaritos do tipo *“Subcampo da inteligência artificial”* penalizam sistematicamente respostas corretas mas expandidas. O efeito é amplificado quando o modelo inclui listas, histórico ou aplicações — padrão frequente no `llm` e, em menor grau, nos cenários RAG com contexto longo.

### 5.4 Prolixidade e repetição do phi3

No Teste 2, a resposta `rag_rerank` para REST contém **repetição em loop** de um mesmo bullet (“Independência dos sistemas…”), com F1 = **0,0036** e latência de geração ≈ **1251,7 s**. Trata-se de falha de **decodificação/generação**, não de retrieval isolado: o contexto recuperado foi suficiente para iniciar uma definição correta, mas o modelo degradou a saída. Esse evento **infla** a latência média de `rag_rerank` no Teste 2 e **deprime** o F1 agregado, mascarando ganhos pontuais em outras perguntas.

---

## 6. Discussão de latência

| Observação | Evidência |
|------------|-----------|
| Aumento global no Teste 2 | Latências médias superiores em todos os cenários RAG e em `llm` |
| Outlier REST (`rag_rerank`) | `latency_seconds` = 1271,99 s numa única pergunta |
| Retrieval mais pesado em ML (`rag_basic` v2) | `retrieval_latency_seconds` = 59,24 s vs. 35,96 s (v1) na pergunta sobre machine learning |
| Custo de geração | `mean_generation_latency_seconds` de `rag_rerank` na v2: **415,49 s** (v1: 123,31 s) |

A comparação v1 → v2 **não** isola apenas o efeito do corpus: carga do ambiente (Ollama, CPU/GPU), tamanho do índice (446 vs. 411 documentos) e o outlier de geração compõem o aumento observado. Latências devem ser reportadas como **ordens de grandeza** e acompanhadas de análise por pergunta, não apenas médias.

---

## 7. Impacto do rerank

| Aspecto | Teste 1 (v1) | Teste 2 (v2) |
|---------|--------------|--------------|
| F1 médio `rag_rerank` | **0,1317** (melhor agregado) | 0,1216 (abaixo de `rag_basic`) |
| PostgreSQL | F1 = 0,296 (melhor caso individual) | F1 = 0,296 (mantido) |
| Machine learning | F1 = 0,178 | F1 = 0,186 (ligeira melhora) |
| REST | F1 = 0,085 | F1 = 0,004 (degradação severa) |

**Interpretação:** o reranking continuou eficaz quando o corpus fornecia chunks alinhados (PostgreSQL, machine learning). No Teste 2, o benefício médio do rerank foi **anulado** pelo fracasso generativo em REST. Em Docker, v2 `rag_rerank` (0,056) superou v1 (0,043), indicando que o rerank nem sempre piora — o efeito é **dependente da pergunta e da estabilidade do LLM**.

Custo computacional: além do CrossEncoder, o Teste 2 manteve `top_k=5` com índice maior; o tempo de rerank por si só não explica o salto de +302 s na média — a geração repetitiva é o fator dominante.

---

## 8. Limitações observadas

1. **Amostra n = 5:** insuficiente para inferência estatística; uma pergunta outlier altera médias.
2. **Expansão de corpus parcial:** apenas dois tópicos novos indexados na rodada v2; pgvector permanece sem cobertura dedicada.
3. **Comparabilidade imperfeita:** média de chunks em `rag_basic` passou de 3,0 (v1) para 5,0 (v2).
4. **EM/F1 lexicais:** inadequados para julgar correção semântica e prolixidade.
5. **Modelo local phi3:** alucinações no baseline; repetição em respostas longas no Teste 2.
6. **Latência dependente de hardware e de falhas pontuais de geração.**
7. **Metadado `chunk_size_config` vs. indexação real (500/100).**
8. **Agregado `rag_rerank` v2 inferior ao v1** apesar da hipótese de melhoria — exige discussão honesta (outlier + cobertura), não ocultação.

---

## 9. Observações sobre o modelo phi3

- **Baseline (`llm`):** respostas extensas; em pgvector, conteúdo factualmente incorreto (*“GLOP”*, funções SQL inexistentes) — risco de alucinação sem ancoragem documental.
- **Com RAG:** respostas tendencialmente mais curtas e alinhadas ao contexto quando o tema está no índice (ex.: definição de PostgreSQL como SGBDOR).
- **Teste 2 — patologia de repetição:** loop textual em REST sob `rag_rerank`, com destruição do F1 e latência extremada; evidencia limitação do modelo local para controle de comprimento e parada.
- **Tokens:** `mean_tokens_used` = null (Ollama); impossibilita análise de custo por token nesta rodada.

---

## 10. Dependência entre qualidade do corpus e recuperação

A pergunta sobre **pgvector** ilustra o limite estrutural:

| Cenário | v1 F1 | v2 F1 | Comportamento |
|---------|-------|-------|---------------|
| `rag_basic` | 0,133 | 0,069 | Admissão de ausência de contexto; sem definição correta |
| `rag_rerank` | 0,056 | 0,067 | Mesma limitação; leve variação lexical sem ganho conceitual |
| `llm` | 0,030 | 0,030 | Alucinação elaborada |

A expansão v2 **não** introduziu artigo sobre pgvector. O pgvector depende da **interseção** pergunta–índice: embeddings e busca vetorial no índice não substituem a ausência do artigo-alvo.

Em **machine learning**, com chunks da v1 já presentes e índice ampliado, o F1 de `rag_basic` subiu de 0,154 para **0,286**, compatível com melhor recuperação e/ou maior volume de contexto (`chunks_retrieved` = 5).

---

## 11. Conclusões preliminares

1. A expansão incremental do corpus (v2 sobre v1) associou-se a **melhoria modesta** do F1 médio em `rag_basic` (+6,4% relativo), com ganho expressivo em *machine learning* e sem melhoria em pgvector.
2. O baseline `llm` permaneceu **invariante**, validando o controle experimental do cenário sem retrieval.
3. O **reranking** não garantiu superioridade no Teste 2: F1 médio de `rag_rerank` ficou **abaixo** do Teste 1 e abaixo de `rag_basic` na v2, principalmente devido à falha generativa em REST.
4. A **latência** aumentou substancialmente no Teste 2, especialmente em `rag_rerank`; o outlier REST deve ser reportado separadamente das medianas futuras.
5. **F1** permanece mais informativo que **EM** neste protocolo; ambos exigem complementação por avaliação qualitativa humana.
6. Os benchmarks históricos (`20260525_160434` e `20260526_020326`) devem ser preservados **sem reescrita** de métricas para manter a rastreabilidade v1 → v2.

---

## Referência cruzada

| Documento | Conteúdo |
|-----------|----------|
| [preliminary_results_test_1.md](preliminary_results_test_1.md) | Análise detalhada do Teste 1 |
| [discussion_preliminary_findings.md](discussion_preliminary_findings.md) | Síntese interpretativa v1 + v2 |
| [corpus_evolution.md](corpus_evolution.md) | Versionamento e expansão do corpus |
| [experiments.md](experiments.md) | Protocolo operacional e comparação |

---

*Documento elaborado exclusivamente a partir de `benchmark_20260525_160434.json`, `benchmark_20260526_020326.json`, `corpus_report_wikipedia_benchmark_v1.json` e `corpus_report_wikipedia_benchmark_v2.json`. Nenhuma métrica foi estimada além dos valores registrados nas execuções.*
