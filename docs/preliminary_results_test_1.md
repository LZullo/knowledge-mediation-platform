# Resultados Preliminares — Benchmark de Teste 1

**Identificador da execução:** `20260525_160434`  
**Data da execução:** 25/05/2026, 16:31:56 UTC  
**Artefatos:** `results/benchmark_20260525_160434.json`, `results/benchmark_20260525_160434.csv`  
**Corpus:** `wikipedia_benchmark`

---

## 1. Introdução breve

Este documento registra a **análise experimental preliminar** do primeiro benchmark formal do sistema RAG desenvolvido no Trabalho de Conclusão de Curso (TCC). O objetivo imediato não é estabelecer conclusões definitivas sobre desempenho, mas **validar o protocolo de avaliação**, comparar cenários de inferência sob condições controladas e produzir evidências iniciais para a seção de resultados do texto acadêmico.

O benchmark compara três cenários de resposta a perguntas técnicas em português:

| Cenário | Descrição |
|---------|-----------|
| `llm` | Baseline: geração apenas com o modelo de linguagem, sem recuperação de contexto |
| `rag_basic` | RAG com recuperação vetorial simples (pgvector + top-*k*) |
| `rag_rerank` | RAG com recuperação expandida, reranking semântico e seleção refinada de chunks |

A motivação do uso de **Retrieval-Augmented Generation (RAG)** reside na limitação de modelos locais pequenos quando confrontados com conhecimento factual especializado: sem ancoragem em um corpus controlado, o modelo tende a produzir respostas genéricas, extensas ou factualmente imprecisas. A hipótese avaliada neste teste preliminar é que a injeção de contexto recuperado do corpus técnico melhora o alinhamento lexical e conceitual das respostas em relação a gabaritos curtos de referência.

---

## 2. Configuração experimental

### 2.1 Ambiente e componentes

| Componente | Configuração |
|------------|--------------|
| **Corpus** | Artigos técnicos da Wikipédia em português (`wikipedia_benchmark`), com tópicos controlados e indexação vetorial |
| **Armazenamento vetorial** | PostgreSQL 16 + extensão **pgvector** |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (384 dimensões, normalizados) |
| **Reranking** | CrossEncoder `cross-encoder/ms-marco-MiniLM-L-6-v2` (cenário `rag_rerank`) |
| **LLM** | **Ollama**, modelo **`phi3`**, provedor `ollama` |
| **Temperatura** | `0.0` (geração determinística para reprodutibilidade) |
| **top_k (recuperação final)** | `5` |
| **chunk_size (benchmark)** | `300` caracteres |
| **Perguntas avaliadas** | `5` questões técnicas de definição |

### 2.2 Definição dos cenários

- **`llm` (baseline):** o modelo responde exclusivamente com conhecimento paramétrico interno. Nenhum chunk é recuperado (`mean_chunks_retrieved = 0`).
- **`rag_basic`:** após embedding da consulta, recupera os *k* chunks mais similares via busca vetorial em pgvector e monta o prompt com esse contexto. Nesta execução, a média de chunks efetivamente utilizados foi **3,0** por pergunta.
- **`rag_rerank`:** recupera um conjunto expandido de candidatos, reordena com CrossEncoder e mantém os **5** chunks finais (`mean_chunks_retrieved = 5,0`) para geração.

### 2.3 Métricas

- **Exact Match (EM):** correspondência exata normalizada entre resposta gerada e gabarito.
- **F1:** sobreposição de tokens (estilo avaliação extractiva), mais tolerante a variações de redação.
- **Latência (`latency_seconds`):** tempo total observado por pergunta, incluindo retrieval (quando aplicável) e geração.

### 2.4 Gabaritos de referência

| Pergunta | Gabarito (`expected_answer`) |
|----------|------------------------------|
| O que é machine learning? | Subcampo da inteligência artificial. |
| O que é PostgreSQL? | Sistema gerenciador de banco de dados objeto relacional. |
| O que é REST? | Estilo de arquitetura de software. |
| O que é Docker? | Plataforma de containers. |
| O que é pgvector? | Extensão do PostgreSQL para busca vetorial. |

---

## 3. Resultados agregados

### 3.1 Tabela principal (médias por cenário)

Valores extraídos diretamente do campo `summaries` do artefato JSON.

| Cenário | Mean EM | Mean F1 | Mean Latency (s) |
|---------|---------|---------|------------------|
| `llm` | 0,000 | 0,030 | 120,21 |
| `rag_basic` | 0,000 | 0,112 | 74,66 |
| `rag_rerank` | 0,000 | 0,132 | 133,16 |

### 3.2 Decomposição complementar de latência

| Cenário | Mean retrieval (s) | Mean generation (s) | Mean chunks |
|---------|-------------------|----------------------|-------------|
| `llm` | ≈ 0,000 | 101,09 | 0,0 |
| `rag_basic` | 7,32 | 66,50 | 3,0 |
| `rag_rerank` | 9,54 | 123,31 | 5,0 |

### 3.3 Resultados por pergunta (F1 e latência)

| Pergunta | F1 `llm` | F1 `rag_basic` | F1 `rag_rerank` | Lat. `llm` (s) | Lat. `rag_basic` (s) | Lat. `rag_rerank` (s) |
|----------|----------|----------------|-----------------|----------------|----------------------|----------------------|
| Machine learning | 0,038 | 0,154 | **0,178** | 219,54 | 94,55 | 163,43 |
| PostgreSQL | 0,047 | 0,111 | **0,296** | 97,82 | 78,18 | 116,66 |
| REST | 0,020 | **0,087** | 0,085 | 101,88 | 62,48 | 103,29 |
| Docker | 0,016 | **0,073** | 0,043 | 79,21 | 71,09 | 135,28 |
| pgvector | 0,030 | **0,133** | 0,056 | 102,58 | 66,97 | 147,16 |

### 3.4 Interpretação dos agregados

1. **Ganho de F1 com RAG:** o F1 médio passou de **0,030** (`llm`) para **0,112** (`rag_basic`), um aumento relativo de aproximadamente **3,7×**. Com reranking, atingiu **0,132** (**≈ 4,4×** em relação ao baseline). Os valores absolutos permanecem modestos — coerente com gabaritos extremamente curtos e respostas mais elaboradas.

2. **Melhor cenário agregado em F1:** `rag_rerank` apresentou o maior F1 médio (**0,132**), embora **não tenha superado `rag_basic` em todas as perguntas** (ex.: Docker e pgvector).

3. **Exact Match nulo em todos os cenários:** nenhuma resposta reproduziu literalmente o gabarito. Isso não implica, por si só, invalidade semântica das respostas — tema desenvolvido na Seção 5.

4. **Latência e trade-off:** `rag_rerank` elevou a latência média para **133,16 s** (+**78%** vs. `rag_basic` e +**11%** vs. `llm`). A maior parte do tempo em `rag_rerank` concentra-se na **geração** (média 123,31 s), possivelmente associada a prompts mais longos com cinco chunks. Em `rag_basic`, a latência média (**74,66 s**) ficou **abaixo** do baseline `llm` (**120,21 s**), em parte porque as respostas RAG tendem a ser mais concisas, reduzindo tempo de decodificação no phi3.

5. **Caráter preliminar:** cinco perguntas não permitem inferência estatística robusta; os números indicam **tendências experimentais**, não efeitos generalizáveis.

---

## 4. Análise qualitativa

### 4.1 PostgreSQL — efeito do retrieval e do reranking

**Gabarito:** *Sistema gerenciador de banco de dados objeto relacional.*

| Cenário | F1 | Trecho representativo da resposta |
|---------|-----|-----------------------------------|
| `llm` | 0,047 | Resposta longa, com detalhes históricos questionáveis (ex.: autores, licença LGPL, menções repetitivas à comunidade) |
| `rag_basic` | 0,111 | Define PostgreSQL como SGBDR relacional open source, com histórico Postgres95/Ingres |
| `rag_rerank` | **0,296** | *"PostgreSQL é um sistema gerenciador de banco de dados objeto relacional (SGBD) de código aberto..."* |

**Observações:**

- O cenário **`llm`** produziu texto **prolixo e enciclopédico**, com baixa densidade de termos do gabarito (F1 = 0,047).
- **`rag_basic`** ancora a resposta em material do corpus, porém ainda enfatiza aspectos históricos e licenciamento, afastando-se do gabarito minimalista.
- **`rag_rerank`** aproximou-se semanticamente do gabarito ao empregar explicitamente *"sistema gerenciador de banco de dados objeto relacional"*, refletindo melhor seleção de chunks — F1 **0,296**, o maior valor individual deste benchmark.

### 4.2 Machine learning — alinhamento conceitual via retrieval

**Gabarito:** *Subcampo da inteligência artificial.*

| Cenário | F1 | Observação |
|---------|-----|------------|
| `llm` | 0,038 | Resposta extensa sobre técnicas (supervisionado, SVM, aplicações industriais), sem enunciar claramente "subcampo" |
| `rag_basic` | 0,154 | Resposta mais curta; posiciona ML dentro da IA |
| `rag_rerank` | **0,178** | Explicita: *"Machine Learning é um subcampo da Inteligência Artificial..."* |

O retrieval direcionou o modelo para formulações mais próximas da definição esperada. O reranking reforçou a menção explícita de **subcampo**, elevando o F1. A resposta permanece mais longa que o gabarito, limitando o EM.

### 4.3 pgvector — limitação de cobertura do corpus

**Gabarito:** *Extensão do PostgreSQL para busca vetorial.*

| Cenário | F1 | Comportamento observado |
|---------|-----|-------------------------|
| `llm` | 0,030 | Alucinação factual grave (referências a "GLOP", funções inexistentes, exemplos SQL incorretos) |
| `rag_basic` | **0,133** | Reconhece ausência de contexto adequado; não define corretamente a extensão |
| `rag_rerank` | 0,056 | Resposta longa admitindo impossibilidade de responder com os chunks recuperados |

**Interpretação:** trata-se do caso mais ilustrativo da **dependência do RAG em relação à cobertura do corpus**. Sem artigo ou chunk sobre pgvector indexado, nem o retrieval nem o reranking suprimentam a lacuna — o sistema declara falta de evidência (`rag_basic`/`rag_rerank`) ou o baseline inventa conteúdo (`llm`). O F1 de `rag_basic` (0,133) reflete tokens parcialmente alinhados ao domínio PostgreSQL, não uma definição correta de pgvector.

Este resultado reforça que **qualidade do corpus ≥ sofisticação do pipeline** em tarefas factuais especializadas.

### 4.4 Síntese transversal (REST e Docker)

- **REST:** os três cenários capturaram o caráter arquitetural; `rag_basic` (F1 = 0,087) ligeiramente superou `rag_rerank` (0,085).
- **Docker:** `rag_basic` (F1 = 0,073) superou `rag_rerank` (0,043), sugerindo que reranking nem sempre melhora a seleção quando o gabarito é uma definição de uma linha e o modelo expande a resposta.

---

## 5. Discussão metodológica

### 5.1 Exact Match igual a zero não equivale a resposta incorreta

Todos os cenários obtiveram **EM = 0,0** em todas as perguntas. Os gabaritos são definições **ultra-curtas** (4–9 palavras), enquanto o phi3 tende a produzir parágrafos explicativos. A métrica EM exige correspondência literal após normalização; respostas semanticamente adequadas — por exemplo, descrever REST como estilo arquitetural baseado em HTTP — são penalizadas.

### 5.2 F1 como métrica mais representativa neste experimento

O **F1 token-level** capturou parcialmente a sobreposição lexical entre resposta e gabarito, refletindo melhor os ganhos do RAG (ex.: presença de *"subcampo"*, *"objeto relacional"*, *"containers"*). Contudo, o F1 **não mede equivalência semântica completa** (sinonímia, ordem de palavras, implicação). Valores absolutos baixos (< 0,30) coexistem com respostas que um avaliador humano poderia considerar aceitáveis.

### 5.3 Limitações do desenho amostral

| Fator | Implicação |
|-------|------------|
| **n = 5 perguntas** | Alta variância; um único outlier (ex.: latência de 219 s em machine learning no `llm`) distorce médias |
| **Benchmark preliminar** | Protocolo em validação, não avaliação conclusiva |
| **Modelo phi3 local** | Capacidade paramétrica limitada; alucinações no baseline; latências elevadas |
| **Gabaritos minimalistas** | Desalinhamento sistemático com estilo de resposta do modelo |
| **Ausência de avaliação humana** | Métricas automáticas não substituem julgamento de adequação factual |

### 5.4 Reprodutibilidade

Temperatura zero, corpus identificado (`wikipedia_benchmark`), `run_id` e exportação JSON/CSV permitem auditoria e replicação. Contudo, latências dependem de hardware, carga do Ollama e estado do índice vetorial — devem ser reportadas como ordens de grandeza, não como SLA.

---

## 6. Trade-offs observados

### 6.1 Qualidade vs latência

```text
        F1 médio ↑
            │
    0,132 ──┼── rag_rerank  (latência média: 133 s)
    0,112 ──┼── rag_basic   (latência média: 75 s)
    0,030 ──┼── llm         (latência média: 120 s)
            └────────────────────────────→ tempo
```

**Principais observações:**

| Dimensão | `rag_basic` | `rag_rerank` |
|----------|-------------|--------------|
| F1 médio | 0,112 | **0,132** (+18% relativo) |
| Latência média | 74,66 s | **133,16 s** (+78% relativo) |
| Chunks médios | 3,0 | 5,0 |
| Custo adicional | Busca vetorial | + CrossEncoder sobre candidatos expandidos |

O reranking melhorou a qualidade lexical média, especialmente em perguntas bem cobertas pelo corpus (PostgreSQL, machine learning), ao custo de **maior latência de geração** (prompts mais extensos) e **processamento adicional** na etapa de retrieval. Para um TCC com foco em sistemas locais e corpus técnico controlado, o trade-off é apresentável: ganhos incrementais de F1 devem ser justificados pelo requisito de latência da aplicação alvo.

---

## 7. Limitações atuais

1. **Amostra reduzida:** apenas cinco perguntas, insuficiente para intervalos de confiança ou testes de significância.
2. **Corpus limitado:** lacunas documentais (pgvector) comprometem o RAG independentemente do pipeline.
3. **Modelo local pequeno (phi3):** limitações de factualidade, prolixidade e latência de decodificação.
4. **Métricas automáticas restritas:** EM/F1 token-level sem avaliação humana nem métricas semânticas (ex.: BERTScore, LLM-as-judge calibrado).
5. **Modelos de embedding/rerank majoritariamente anglófonos:** possível subótimo para português técnico.
6. **Benchmark preliminar:** configuração (`chunk_size=300`, `top_k=5`) sujeita a refinamento antes da avaliação final.
7. **Instabilidade pontual de latência:** outlier de 219 s em uma pergunta do cenário `llm` afeta a média agregada.

---

## 8. Próximos passos

| Prioridade | Ação |
|------------|------|
| Alta | Ampliar o benchmark para **15–30 perguntas**, estratificadas por domínio técnico |
| Alta | **Expandir o corpus** com artigos sobre pgvector, embeddings e componentes do próprio pipeline |
| Média | Incluir **avaliação qualitativa humana** (escala de adequação factual e concisão) |
| Média | Comparar **phi3** com modelos alternativos (local maiores e/ou API comercial como contraste) |
| Média | Reportar intervalos de confiança via bootstrap sobre F1 por pergunta |
| Baixa | Ablação de `top_k`, `chunk_size` e threshold do reranker |
| Baixa | Métricas semânticas complementares ao F1 |

---

## 9. Conclusão preliminar

O benchmark de teste 1 (`20260525_160434`), conduzido sobre cinco perguntas técnicas em português, fornece evidências **preliminares e consistentes com a hipótese de RAG**, porém insuficientes para generalização estatística:

1. A introdução de **retrieval vetorial** elevou o F1 médio de **0,030** para **0,112**, indicando maior sobreposição lexical com gabaritos curtos e respostas geralmente mais objetivas.
2. O **reranking** (`rag_rerank`) alcançou o maior F1 médio (**0,132**) e o melhor desempenho pontual em PostgreSQL (F1 = **0,296**), com ganho incremental sobre `rag_basic` no agregado.
3. A **latência** do cenário com reranking aumentou substancialmente (média **133 s**), materializando o trade-off entre qualidade lexical proxy (F1) e custo computacional.
4. O caso **pgvector** demonstrou que pipeline RAG **não compensa ausência de cobertura documental**, e que o baseline sem retrieval pode **alucinar** conteúdo técnico incorreto.
5. O pipeline RAG integrado (pgvector + sentence-transformers + Ollama/phi3 + rerank opcional) mostrou **viabilidade experimental** para continuidade do TCC, devendo evoluir em escala amostral, corpus e métodos de avaliação.

---

## Referência rápida — principais números

| Indicador | Valor |
|-----------|-------|
| Perguntas | 5 |
| Cenários | 3 (`llm`, `rag_basic`, `rag_rerank`) |
| Melhor F1 médio | **0,132** (`rag_rerank`) |
| Melhor F1 individual | **0,296** (PostgreSQL, `rag_rerank`) |
| EM em todos os cenários | **0,000** |
| Maior latência média | **133,16 s** (`rag_rerank`) |
| Menor latência média | **74,66 s** (`rag_basic`) |

---

## Nota para apresentação preliminar do TCC

As interpretações metodológicas **mais importantes** para comunicação à banca neste estágio são:

1. **Diferenciar falha de EM de incorreção semântica** — respostas longas e corretas em essência podem ter EM zero; o F1 foi mais informativo, mas ainda subestima qualidade percebida.
2. **Apresentar RAG como mitigação de alucinação e prolixidade**, não como garantia de acerto — especialmente com modelo local pequeno.
3. **Explicitar o trade-off qualidade–latência do reranking** com números reais (+18% F1 médio relativo vs. `rag_basic`, +78% latência média).
4. **Usar pgvector como contraponto metodológico** — qualidade do corpus é pré-requisito; pipeline sofisticado não substitui indexação adequada.
5. **Enfatizar caráter preliminar (n=5)** — tendências promissoras, conclusões definitivas adiadas para benchmark ampliado com avaliação humana.

---

*Documento gerado com base exclusiva nos artefatos `benchmark_20260525_160434.json` e `.csv`. Métricas não foram estimadas ou extrapoladas além dos valores registrados na execução.*
