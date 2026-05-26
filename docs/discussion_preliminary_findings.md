# Discussão — Achados preliminares (Teste 1 e Teste 2)

Este documento sintetiza a **interpretação acadêmica** dos benchmarks preliminares `20260525_160434` (corpus v1, Teste 1) e `20260526_020326` (corpus v2, Teste 2). Os números citados provêm dos artefatos em `results/`; a discussão não substitui avaliação humana nem inferência estatística sobre populações maiores.

---

## 1. RAG superando o baseline `llm`

Em ambos os testes, o F1 médio dos cenários com recuperação superou o baseline paramétrico (0,0301):

| Teste | F1 `llm` | F1 `rag_basic` | F1 `rag_rerank` |
|-------|----------|----------------|-----------------|
| Teste 1 (v1) | 0,0301 | 0,1116 | 0,1317 |
| Teste 2 (v2) | 0,0301 | 0,1188 | 0,1216 |

O ganho relativo de `rag_basic` sobre `llm` situa-se entre **3,7×** (Teste 1) e **3,9×** (Teste 2) em F1 médio. Qualitativamente, as respostas RAG tendem a ser mais concisas e a incorporar terminologia presente nos chunks (ex.: *“sistema gerenciador de banco de dados objeto relacional”*), enquanto o `llm` produz texto enciclopédico com menor densidade de tokens do gabarito.

O baseline **não** se beneficiou da expansão do corpus (respostas idênticas), o que reforça que os ganhos observados nos cenários RAG no Teste 2 devem ser discutidos no eixo **índice + retrieval**, não no eixo conhecimento paramétrico adicional.

---

## 2. Trade-off entre qualidade (proxy lexical) e latência

Há tensão entre métricas de sobreposição lexical e tempo de resposta:

```text
Teste 1 — F1 médio vs latência média (s)
  llm:         F1 0,030  |  120 s
  rag_basic:   F1 0,112  |   75 s
  rag_rerank:  F1 0,132  |  133 s

Teste 2 — F1 médio vs latência média (s)
  llm:         F1 0,030  |  152 s
  rag_basic:   F1 0,119  |  171 s
  rag_rerank:  F1 0,122  |  436 s  ← dominado por outlier REST (~1272 s)
```

No Teste 1, `rag_basic` foi o cenário de **melhor compromisso** entre F1 e latência. No Teste 2, o custo temporal do pipeline completo aumentou — em parte por ambiente e índice maior, em parte por **falha de geração** (repetição em REST sob `rag_rerank`).

Para sistemas RAG em produção, a implicação é clara: o reranking e prompts com muitos chunks só se justificam se o requisito de latência da aplicação comportar o custo adicional **e** se o LLM for estável em comprimento de saída. Caso contrário, um estágio `rag_basic` bem calibrado pode ser preferível ao rerank com modelo local pequeno.

---

## 3. Dependência do corpus

A tríade **cobertura documental → qualidade do retrieval → qualidade da resposta** manifestou-se em dois polos:

**Polo positivo (machine learning, PostgreSQL):** com chunks relevantes no índice, RAG e rerank elevam F1 e aproximam o discurso do gabarito, mesmo com EM zero.

**Polo negativo (pgvector):** sem artigo dedicado, os cenários RAG admitem ausência de evidência ou respondem com confusão terminológica; o `llm` alucina conteúdo técnico inexistente. A expansão v2 indexou predominantemente *Recuperação de informação* e *LangChain*, **sem** fechar a lacuna de pgvector — logo, o Teste 2 **não** invalida a lição do Teste 1 sobre cobertura; apenas a reforça de forma parcial.

A recuperação via pgvector é **necessária mas não suficiente**: um índice vetorial sofisticado não compensa ausência semântica do documento-fonte correto.

---

## 4. Limitações do modelo local phi3

Três padrões recorrentes:

1. **Prolixidade** face a gabaritos de uma linha — penalização sistemática em EM/F1.
2. **Alucinação factual** no baseline (pgvector: referências a “GLOP”, SQL incorreto).
3. **Instabilidade generativa** no Teste 2 (loop repetitivo em REST com `rag_rerank`), degradando F1 e latência agregada.

Esses comportamentos limitam a generalização dos resultados para outros LLMs e reforçam a necessidade de, em trabalhos futuros, repetir o protocolo com modelo alternativo ou avaliação qualitativa cega.

---

## 5. Importância do reranking

No Teste 1, `rag_rerank` obteve o **maior F1 médio** (0,1317) e o melhor resultado pontual (PostgreSQL, F1 = 0,296). O CrossEncoder reordenou candidatos de forma a privilegiar chunks com vocabulário alinhado ao gabarito.

No Teste 2, o reranking **não** dominou o agregado: F1 médio 0,1216 < 0,1188 de `rag_basic` (diferença pequena) e < 0,1317 do Teste 1. Ainda assim, em perguntas isoladas (machine learning, Docker), o rerank manteve ou superou `rag_basic`.

Conclusão interpretativa: o reranking é um **refinador de recall/precisão na fronteira de candidatos**, cuja utilidade líquida depende de (i) corpus, (ii) estabilidade do gerador e (iii) ausência de outliers de decodificação. Não deve ser apresentado como melhoria monotônica garantida.

---

## 6. Implicações para sistemas RAG reais

| Achado | Implicação prática |
|--------|-------------------|
| Corpus versionado | Permite evoluir conhecimento sem apagar evidências experimentais passadas |
| Deduplicação e indexação incremental | Reduz redundância no índice, mas exige auditoria de quais tópicos foram efetivamente indexados |
| Métricas EM/F1 | Úteis para tendências controladas; insuficientes para SLA de qualidade em produção |
| RAG vs `llm` | Mitiga alucinação e melhora alinhamento lexical quando há cobertura |
| Rerank | Melhora casos selecionados; impõe custo e risco com LLMs locais instáveis |
| phi3 local | Viável para prototipagem acadêmica; exige validação humana antes de decisões críticas |

---

## 7. Inconsistências metodológicas a declarar na banca

1. **Não comparabilidade perfeita** entre Teste 1 e 2: número médio de chunks recuperados em `rag_basic` (3 vs. 5).
2. **Agregado de `rag_rerank` no Teste 2 inferior ao Teste 1** apesar da expansão do corpus — explicado em parte por outlier de geração, não apenas por regressão do rerank.
3. **Expansão temática incompleta** (2 de 12 tópicos novos efetivamente indexados na rodada v2).
4. **Discrepância** entre `chunk_size_config` no benchmark e chunking de indexação (300 vs. 500).
5. **n = 5** — tendências, não efeitos confirmados.

---

## 8. Encaminhamento para a dissertação

1. Preservar ambos os `run_id` e articular narrativa **v1 → v2** com tabelas explícitas.
2. Reportar métricas por pergunta, não só médias, destacando REST (Teste 2) como limite do phi3.
3. Planejar Teste 3 (`wikipedia_benchmark_v3`, overlap 150) como ablação de chunking, sem sobrescrever benchmarks anteriores.
4. Introduzir avaliação qualitativa humana (adequação factual, concisão) como complemento obrigatório a EM/F1.

---

*Documento de discussão vinculado a [preliminary_results_test_1.md](preliminary_results_test_1.md), [preliminary_results_test_2.md](preliminary_results_test_2.md), [methodology.md](methodology.md) e [corpus_evolution.md](corpus_evolution.md).*
