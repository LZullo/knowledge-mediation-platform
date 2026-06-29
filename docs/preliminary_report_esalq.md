# Relatório preliminar

**Avaliação experimental de um pipeline de Geração Aumentada por Recuperação com PostgreSQL, pgvector e modelo de linguagem local**

MBA em Engenharia de Software — USP/ESALQ  
Relatório preliminar de Trabalho de Conclusão de Curso

---

## Resumo

Este trabalho investiga, de forma experimental, um pipeline de Geração Aumentada por Recuperação (Retrieval-Augmented Generation — RAG) voltado a perguntas e respostas em português sobre temas técnicos de computação. Propõe-se uma arquitetura de referência configurável, na qual documentos da Wikipédia em português e material complementar curado são indexados em PostgreSQL com a extensão pgvector; a recuperação semântica emprega representações densas (embeddings); a geração é realizada localmente por meio do Ollama com o modelo phi3, o que permite contrastar inferência paramétrica isolada, RAG com recuperação vetorial simples e RAG com etapa adicional de reranking.

A metodologia compreendeu três rodadas sucessivas de benchmark (versões v1, v2 e v3 do corpus), com versionamento incremental do acervo documental, conjunto de dezoito perguntas com gabaritos definidos manualmente — organizadas nos subconjuntos histórico core_5 e complementar extended —, métricas de Exact Match e F1 em nível de token (com normalização inspirada no conjunto SQuAD), além de inspeção qualitativa dos trechos recuperados no top-5. Na rodada final (identificador de execução 20260526_171347, corpus wikipedia_benchmark_v3, índice cumulativo de 601 fragmentos textuais), observou-se F1 médio de 0,189 no cenário sem recuperação (baseline LLM), de 0,239 no RAG básico e de 0,202 no RAG com reranking, com latências médias aproximadas de 35 s, 117 s e 124 s, respectivamente. O Exact Match permaneceu nulo em todos os cenários, o que é compatível com respostas generativas mais extensas que os gabaritos concisos adotados na avaliação automática.

Conclui-se, em caráter preliminar, que a recuperação contextual elevou a aderência lexical média das respostas em relação ao modelo isolado; que a cobertura documental influencia de forma direta o desempenho observado; e que o reranking acrescentou custo de latência sem ganho proporcional de F1 neste corpus e nesta configuração — sem que isso invalide, por si só, o uso do mecanismo em outros contextos de escala ou de maior ruído no conjunto inicial de candidatos. A combinação PostgreSQL, pgvector e geração local demonstra viabilidade técnica para prototipagem e avaliação controlada, ressalvadas as limitações de generalização, o tamanho reduzido da amostra e a dependência da qualidade do corpus em português.

**Palavras-chave:** recuperação aumentada por geração; grandes modelos de linguagem; embeddings; bancos de dados vetoriais; pgvector; avaliação experimental; Wikipédia técnica.

---

## 1 Introdução

O avanço dos grandes modelos de linguagem (Large Language Models — LLMs) ampliou a capacidade de sistemas automatizados produzirem texto coerente em múltiplos domínios. Esses modelos armazenam conhecimento de forma paramétrica, aprendido durante o treinamento, o que os torna úteis para tarefas abertas de linguagem natural, mas também expõe limitações relevantes: conhecimento desatualizado ou ausente sobre fatos recentes, tendência a respostas plausíveis porém incorretas — frequentemente designadas como alucinações — e pouco controle explícito sobre a proveniência das afirmações. Em contextos técnicos e organizacionais, nos quais as respostas devem ser auditáveis e ancoradas em fontes confiáveis, tais limitações motivam arquiteturas que combinem geração com recuperação externa de evidências.

Nesse cenário consolidou-se a abordagem de Geração Aumentada por Recuperação (RAG), na qual a consulta do usuário dispara, em primeiro lugar, uma etapa de recuperação da informação sobre um corpus documental e, em seguida, o condicionamento do modelo de linguagem a partir dos trechos recuperados. A qualidade do sistema passa a depender não apenas do gerador, mas da recuperação semântica: representações vetoriais permitem localizar trechos lexicalmente distintos, porém semanticamente próximos; bancos de dados vetoriais, ou extensões vetoriais em sistemas gerenciadores de banco de dados relacionais, persistem essas representações e viabilizam buscas por similaridade em escala compatível com aplicações corporativas. Torna-se, assim, elemento central a avaliação experimental — medir tanto a adequação das respostas quanto o impacto de cada estágio do pipeline (recuperação densa, reranking, montagem de contexto e geração) sob condições reproduzíveis.

No âmbito deste trabalho adota-se uma solução de código aberto orientada à reprodutibilidade em ambiente local: PostgreSQL com pgvector para armazenamento e consulta por similaridade; modelo de embedding sentence-transformers/all-MiniLM-L6-v2; reranker cross-encoder/ms-marco-MiniLM-L-6-v2; e geração via Ollama com phi3 em temperatura zero. Essa escolha substitui, na prática consolidada do experimento, a dependência de API comercial prevista na concepção inicial do projeto, preservando o desenho comparativo entre cenários. O corpus experimental baseia-se em artigos técnicos da Wikipédia em português, complementado por documentação curada onde a enciclopédia não oferece cobertura estável — como ocorre com a extensão pgvector. O protocolo de avaliação inclui benchmark versionado em três iterações, métricas automáticas de Exact Match e F1 em nível de token e validação qualitativa manual dos fragmentos recuperados, de modo a distinguir falhas de recuperação de falhas de geração.

O objetivo deste trabalho consiste em implementar e avaliar experimentalmente um pipeline RAG configurável, com arquitetura de referência, registro das execuções e benchmark reproduzível, comparando geração apenas com modelo de linguagem, RAG com recuperação vetorial em pgvector e RAG com reranking semântico, a fim de caracterizar ganhos, tradeoffs de latência e dependência da cobertura documental em domínio técnico em português.

---

## 2 Metodologia

### 2.1 Desenho experimental

Trata-se de estudo quantitativo comparativo, com componente qualitativo complementar. Na rodada final avaliaram-se três cenários de inferência sobre o mesmo conjunto de perguntas, conforme a Tabela A (descrição dos cenários). A arquitetura organiza o fluxo de processamento em camadas funcionais — interface de consulta, orquestração dos casos de uso, estratégias de recuperação e de montagem de prompt, infraestrutura de embeddings e armazenamento — mantendo um único encadeamento de execução e variando apenas as estratégias associadas a cada cenário. Essa organização favorece a comparabilidade entre condições experimentais e o registro sistemático das execuções em base de dados.

**Tabela A — Cenários experimentais de inferência**

| Cenário | Recuperação vetorial | Reranking | Descrição |
|---------|---------------------|-----------|-----------|
| Baseline (llm) | Não | Não | Pergunta enviada diretamente ao modelo de linguagem |
| RAG básico (rag_basic) | Sim (pgvector; top-5) | Não | Contexto recuperado incorporado ao prompt |
| RAG com reranking (rag_rerank) | Sim (pool ampliado) | Sim (CrossEncoder) | Recuperação em dois estágios |

### 2.2 Corpus documental e evolução versionada

O domínio documental foi delimitado na origem por meio de lista controlada de títulos da Wikipédia em português, obtidos pela API MediaWiki. O texto das páginas foi submetido a limpeza, fragmentação (chunking) e geração de embeddings antes da persistência no banco. O acervo foi tratado como artefato versionado em três etapas, conforme a Tabela B.

**Tabela B — Versões do corpus experimental**

| Versão | Finalidade | Características principais |
|--------|------------|----------------------------|
| wikipedia_benchmark_v1 | Baseline (Teste 1) | Nove tópicos; fragmentos de 500 caracteres e sobreposição de 100; 411 fragmentos |
| wikipedia_benchmark_v2 | Expansão incremental (Teste 2) | Novos tópicos planejados; 35 fragmentos adicionais na rodada documentada; índice cumulativo de aproximadamente 446 fragmentos |
| wikipedia_benchmark_v3 | Refinamento (Teste 3) | Validação prévia de títulos; sobreposição de 150; deduplicação; corpus complementar; 155 fragmentos na rodada v3 |

Na rodada final o índice consultado acumulou 601 fragmentos, correspondentes às versões v1, v2 e v3. A recuperação emprega filtro cumulativo entre versões, o que preserva o histórico experimental, mas pode introduzir redundância entre fragmentos provenientes de reindexações sucessivas do mesmo artigo.

Na versão refinada (v3) aplicaram-se mecanismos de deduplicação: hash criptográfico do conteúdo normalizado, bloqueio por tópico de origem e descarte de trechos com similaridade textual superior a 95% no escopo da mesma versão, com o propósito de reduzir viés de recuperação por repetição semântica no conjunto dos cinco trechos retornados. Para suprir a lacuna documental relativa ao pgvector — ausência de artigo estável na Wikipédia em português — incluiu-se texto técnico curado, com indicação explícita da fonte oficial (repositório do projeto pgvector), indexado como documento complementar na versão v3.

### 2.3 Recuperação, reranking e geração

Na indexação da rodada v3 adotou-se tamanho de fragmento de 500 caracteres e sobreposição de 150. A busca vetorial utilizou o mesmo modelo de embedding empregado na indexação (384 dimensões, com normalização L2), recuperando os cinco trechos mais similares (top-5) por distância do cosseno no pgvector. No cenário com reranking ampliou-se o conjunto inicial de candidatos e aplicou-se pontuação de pares pergunta–trecho por CrossEncoder (ms-marco-MiniLM-L-6-v2), reordenando os candidatos antes da montagem do contexto — procedimento alinhado à literatura de recuperação em dois estágios, na qual busca-se ampliar o recall na primeira etapa e refinar a precisão na segunda.

A geração padrão do experimento final utilizou Ollama com o modelo phi3, temperatura zero, parâmetros de controle de verbosidade configurados na versão v3 e instrução de resposta objetiva em poucas frases. Embora a arquitetura admita provedor alternativo de geração por API comercial, tal opção não foi empregada nas rodadas consolidadas neste relatório.

### 2.4 Benchmark e métricas

As perguntas e as respostas de referência (gabaritos) foram definidas manualmente e não são fornecidas ao modelo no momento da consulta. Na rodada final o benchmark compreendeu dezoito perguntas, das quais cinco integram o subconjunto core_5 — correspondente ao conjunto histórico dos Testes 1 e 2, útil à comparabilidade longitudinal do enunciado — e treze integram o subconjunto extended, voltado a temas como embeddings, recuperação da informação, bancos vetoriais, busca semântica e ferramentas associadas a pipelines RAG.

Conduziram-se três rodadas de benchmark, cujos identificadores de execução e respectivos corpora constam da Tabela C. Os resultados das duas primeiras rodadas foram preservados sem reprocessamento retroativo, de modo a manter a série histórica documentada.

**Tabela C — Rodadas de benchmark**

| Teste | Identificador de execução | Versão do corpus | Número de perguntas |
|-------|---------------------------|------------------|---------------------|
| 1 | 20260525_160434 | v1 (rótulo legado: wikipedia_benchmark) | 5 |
| 2 | 20260526_020326 | v2 | 5 |
| 3 | 20260526_171347 | v3 | 18 |

Como métricas automáticas de qualidade lexical adotaram-se o Exact Match (EM) — proporção de respostas cuja forma normalizada coincide integralmente com o gabarito — e o F1 em nível de token, definido como a média harmônica de precisão e revocação de tokens após normalização (conversão a minúsculas, remoção de pontuação e de artigos em português e em inglês), em linha com protocolos de avaliação de perguntas e respostas como o SQuAD. Registraram-se, adicionalmente, a latência de ponta a ponta (em segundos), o número médio de fragmentos recuperados e, no reranking, o tempo médio da etapa de reordenação.

Complementarmente realizou-se validação qualitativa da recuperação, mediante inspeção manual dos cinco trechos retornados por consulta, avaliando-se a relevância do primeiro trecho, a diversidade entre candidatos, a repetição de conteúdo e a composição do resultado entre as versões v1, v2 e v3 do corpus.

A comparação direta de F1 entre o Teste 3 e os Testes 1 e 2 exige cautela interpretativa, pois na rodada v3 alteraram-se simultaneamente o tamanho amostral, os gabaritos, o controle de verbosidade na geração e a cobertura documental. A série v1–v2–v3 documenta tendência evolutiva; a atribuição causal isolada a cada fator demandaria experimentos adicionais não realizados nesta fase do trabalho.

---

## 3 Resultados preliminares

### 3.1 Resultados da rodada final (Teste 3)

A rodada final referiu-se ao corpus wikipedia_benchmark_v3, a dezoito perguntas e ao parâmetro top-5 na recuperação, com modelos de embedding e de reranking fixos conforme descrito na metodologia. A Tabela 1 apresenta as médias globais por cenário.

**Tabela 1 – Métricas médias globais do benchmark experimental (Teste 3; n = 18 perguntas)**

| Cenário | EM médio | F1 médio | Latência média (s) | Fragmentos médios recuperados |
|---------|----------|----------|-------------------|------------------------------|
| Baseline (llm) | 0,000 | 0,189 | 35,0 | 0 |
| RAG básico (rag_basic) | 0,000 | 0,239 | 117,0 | 5,0 |
| RAG com reranking (rag_rerank) | 0,000 | 0,202 | 123,9 | 5,0 |

O cenário de RAG básico apresentou o maior F1 médio, com incremento absoluto de 0,050 em relação ao baseline (aproximadamente 26% em termos relativos). O Exact Match nulo em todos os cenários indica que, sob métrica lexical estrita, as respostas generativas não reproduzem literalmente os gabaritos; tal resultado não exclui adequação semântica parcial, conforme evidenciado na análise qualitativa.

A Tabela 2 desagrega o F1 médio pelos subconjuntos de perguntas.

**Tabela 2 – F1 médio por subconjunto de perguntas (Teste 3)**

| Subconjunto | N | Baseline (llm) | RAG básico | RAG com reranking |
|-------------|---|----------------|------------|-------------------|
| core_5 | 5 | 0,282 | 0,332 | 0,294 |
| extended | 13 | 0,153 | 0,204 | 0,166 |

O subconjunto extended concentrou temas de maior dificuldade documental e lexical, apresentando F1 médios inferiores aos do core_5 em todos os cenários — o que é compatível com a ampliação temática e com lacunas residuais de cobertura na Wikipédia em português.

### 3.2 Evolução entre as três rodadas

A Tabela 3 sintetiza as médias de F1 e de latência ao longo dos Testes 1, 2 e 3. O Exact Match permaneceu nulo em todas as células.

**Tabela 3 – Evolução das métricas médias por teste e cenário experimental**

| Teste | Corpus | N perguntas | Cenário | F1 médio | Latência média (s) |
|-------|--------|-------------|---------|----------|-------------------|
| 1 | v1 | 5 | Baseline (llm) | 0,030 | 120,2 |
| 1 | v1 | 5 | RAG básico | 0,112 | 74,7 |
| 1 | v1 | 5 | RAG com reranking | 0,132 | 133,2 |
| 2 | v2 | 5 | Baseline (llm) | 0,030 | 152,4 |
| 2 | v2 | 5 | RAG básico | 0,119 | 170,7 |
| 2 | v2 | 5 | RAG com reranking | 0,122 | 435,7 |
| 3 | v3 | 18 | Baseline (llm) | 0,189 | 35,0 |
| 3 | v3 | 18 | RAG básico | 0,239 | 117,0 |
| 3 | v3 | 18 | RAG com reranking | 0,202 | 123,9 |

Entre os Testes 1 e 2 — conduzidos sobre as mesmas cinco perguntas, com expansão incremental do corpus — observou-se melhoria modesta do F1 no RAG básico (de 0,112 para 0,119) e queda agregada no cenário com reranking no Teste 2, associada a valor extremo de latência e a falha generativa pontual na pergunta sobre REST, o que ilustra a sensibilidade das médias a eventos isolados. O Teste 3 não é diretamente equiparável quanto ao tamanho amostral e aos gabaritos; ainda assim reforça, na rodada final, o padrão de superioridade do RAG básico sobre o modelo isolado. Material gráfico complementar (comparação de F1 e de latência entre versões do corpus e entre cenários) foi produzido a partir dos relatórios consolidados das três rodadas e poderá ser inserido na versão Word do relatório.

### 3.3 Análise do impacto da recuperação e do reranking

A recuperação vetorial elevou o F1 médio na rodada final e viabilizou respostas factualmente mais alinhadas em tópicos com cobertura consolidada — como PostgreSQL e LangChain no cenário de RAG básico, quando os trechos recuperados continham passagens adequadas. A cobertura documental emergiu como condição necessária: nos Testes 1 e 2 a pergunta sobre pgvector permaneceu mal atendida até a inclusão controlada do corpus complementar na versão v3.

O reranking acrescentou latência média adicional — incluindo cerca de 1,6 s na etapa de reordenação, além do custo total superior ao do RAG básico — sem elevar o F1 médio agregado neste experimento. Interpreta-se tal resultado como tradeoff custo–benefício desfavorável na média para o tamanho e a composição atuais do índice, e não como refutação geral do mecanismo; contextos com maior ruído no conjunto inicial de candidatos ou com índices mais amplos podem beneficiar-se do refinamento.

### 3.4 Validação qualitativa e casos ilustrativos

A inspeção manual do top-5 revelou repetição de fragmentos do mesmo artigo em diversas perguntas, predominância de trechos indexados na versão v1 do corpus — com complementação pontual da v3 em temas como recuperação da informação e pgvector — e diversidade média entre candidatos na maioria das consultas. No caso de pgvector, o primeiro trecho retornado foi frequentemente irrelevante (por exemplo, conteúdo sobre redes neurais artificiais), enquanto o trecho do documento complementar aparecia em posição intermediária, o que ajuda a explicar ganhos parciais na geração mesmo com recuperação imperfeita.

Entre os casos ilustrativos destaca-se LangChain: no baseline o modelo negou a existência do framework; com RAG a resposta alinhou-se à definição esperada, evidenciando limitação paramétrica do phi3 e o papel do contexto recuperado. Na pergunta sobre bancos vetoriais ocorreu confusão lexical entre “vetoriais” e “virtuais” no baseline; com RAG houve desvio para conteúdo sobre PostgreSQL e dados geoespaciais, sugerindo ambiguidade semântica em português. Em perguntas sobre embeddings as respostas foram parcialmente corretas, porém vagas, frequentemente ancoradas em subseções periféricas de artigos de aprendizado de máquina.

### 3.5 Limitações observadas

As métricas lexicais EM e F1 não capturam plenamente equivalência semântica; o EM nulo coexistiu com respostas parcialmente adequadas em inspeção manual. A Wikipédia em português apresenta cobertura incompleta para software especializado — dez tópicos planejados na v3 não foram indexados por ausência ou insuficiência de artigo. O modelo phi3 produziu respostas prolixas ou imprecisas em conceitos abstratos, mesmo com RAG. O acervo de 601 fragmentos e a amostra de dezoito perguntas limitam a generalização dos achados; o índice cumulativo mistura efeitos das três versões do corpus. Os modelos de embedding e de reranking, com treinamento predominantemente em inglês, podem sub-representar termos em português. Por fim, as latências registradas dependem do hardware local empregado nas rodadas e não devem ser extrapoladas sem ressalva.

---

## 4 Considerações finais

Nesta fase do trabalho a arquitetura do pipeline RAG encontra-se estabilizada: ingestão versionada, armazenamento vetorial em PostgreSQL com pgvector, recuperação densa, reranking opcional, geração local e consolidação dos resultados experimentais. O benchmark foi finalizado na terceira rodada (identificador de execução 20260526_171347), com preservação dos resultados históricos dos Testes 1 e 2 para fins de rastreabilidade metodológica.

Os resultados preliminares indicam viabilidade técnica da abordagem proposta para prototipagem e estudo comparativo em português, com ganho médio modesto do RAG básico sobre o modelo isolado e com evidência clara de que a qualidade da recuperação e a cobertura documental condicionam a resposta final. O reranking, embora pertinente a desenhos de maior escala, não se mostrou vantajoso na média deste corpus específico, o que reforça a necessidade de avaliar tradeoffs de latência em conjunto com métricas de qualidade — e não isoladamente.

Trata-se, contudo, de considerações preliminares, e não de conclusão definitiva da dissertação. Permanecem em aberto a redação integral do capítulo de fundamentação teórica com referências bibliográficas em conformidade com as normas da USP/ESALQ, a avaliação humana em escala estruturada, a possível ampliação do corpus e do conjunto de perguntas, experimentos de busca híbrida (lexical e vetorial) e o emprego de métricas semânticas adequadas ao português. Como perspectivas de continuidade mencionam-se a expansão controlada do acervo, a redução de redundância entre versões indexadas, a ablação do reranking em índices maiores, a comparação com modelos geradores alternativos e a integração de rubrica de avaliação manual complementar às métricas EM e F1.

---

## Referências

As referências a seguir correspondem a fontes, ferramentas e bases conceituais efetivamente utilizadas no experimento. A formatação definitiva segundo as normas da USP/ESALQ será concluída na versão final do trabalho; entradas ainda em revisão bibliográfica estão indicadas entre colchetes.

LEWIS, Patrick et al. Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *[Referência completa a confirmar na versão final.]*

POSTGRESQL GLOBAL DEVELOPMENT GROUP. PostgreSQL. *[Documentação oficial; dados de acesso a completar.]*

PGVECTOR CONTRIBUTORS. pgvector: open-source vector similarity search for PostgreSQL. Disponível em: https://github.com/pgvector/pgvector. Acesso em: *[data a completar].*

REIMERS, Nils; GUREVYCH, Iryna. Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks. *[Referência completa a confirmar — modelo all-MiniLM-L6-v2 empregado no projeto.]*

RAJPURKAR, Pranav et al. SQuAD: 100,000+ Questions for Machine Comprehension of Text. *[Referência completa a confirmar — protocolo de normalização das métricas EM/F1.]*

OLLAMA. Ollama: local LLM runtime. *[Referência oficial; dados de acesso a completar.]*

MICROSOFT. Phi-3 technical report. *[Referência oficial do modelo phi3; a confirmar.]*

HUGGING FACE. Model card: cross-encoder/ms-marco-MiniLM-L-6-v2. *[Referência completa a confirmar.]*

WIKIMEDIA FOUNDATION. Wikipédia, a enciclopédia livre. Edição em língua portuguesa. Conteúdo obtido via MediaWiki API. *[Política de citação a adequar na versão final.]*

---

## Apêndice — Nota sobre origem dos dados experimentais

As Tabelas 1 e 2 derivam dos agregados da rodada final (identificador de execução 20260526_171347, corpus wikipedia_benchmark_v3). A Tabela 3 consolida as médias reportadas nas três rodadas (identificadores 20260525_160434, 20260526_020326 e 20260526_171347). A validação qualitativa da recuperação baseou-se em inspeção manual do top-5 das consultas do Teste 3. As estatísticas de indexação da versão v3 do corpus constam do relatório de corpus correspondente à mesma rodada.

Para a versão final do TCC permanecem previstos: revisão bibliográfica completa; avaliação humana com rubrica; inserção das figuras no template institucional; e, se indicado pelo orientador, reporte de mediana de latência excluindo valores extremos pontuais observados no Teste 2.
