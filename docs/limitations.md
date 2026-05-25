# Limitações e trabalhos futuros

Transparência sobre o que o sistema **não faz** (ou faz de forma simplificada) fortalece a credibilidade na banca. Cada limitação abaixo inclui **impacto** e **oportunidade de pesquisa futura**.

---

## 1. Dependência da OpenAI na geração

**Limitação:** respostas finais dependem de API externa (`OPENAI_API_KEY`), com custo por token e possível indisponibilidade.

**Impacto no TCC:** resultados variam com modelo (`gpt-3.5-turbo` vs `gpt-4o-mini`); reprodutibilidade exige registrar modelo e data.

**Trabalho futuro:** avaliar LLMs open locais (Llama, Mistral) com mesma metodologia; comparar custo × qualidade.

---

## 2. Benchmark limitado por amostra e custo

**Limitação:** `limit` de perguntas (ex. 50–1000) por tempo e custo de API; uma execução por configuração, sem intervalo de confiança automático.

**Impacto:** generalização estatística fraca se N for pequeno.

**Trabalho futuro:** múltiplas seeds, bootstrap de intervalos de confiança, execução paralela com rate limit.

---

## 3. Chunking simples por caracteres

**Limitação:** não respeita fronteiras de frase/parágrafo; pode dividir entidades ou frases relevantes.

**Impacto:** EM/F1 podem subestimar o RAG quando a resposta gold está em outro chunk.

**Trabalho futuro:** chunk por sentenças (spaCy), por tokens, ou semantic chunking; reindexar e re-benchmarkar.

---

## 4. Ausência de busca híbrida (BM25 + denso)

**Limitação:** apenas similaridade de embeddings; termos raros ou exatos podem falhar no recall.

**Impacto:** perguntas com nomes/datas específicas podem não recuperar o chunk certo no top_k.

**Trabalho futuro:** PostgreSQL `tsvector` + fusão RRF com pgvector; ou motor dedicado.

---

## 5. Custo computacional do reranking

**Limitação:** CrossEncoder pontua cada par (pergunta, chunk) — latência cresce linearmente com `rerank_top_k`.

**Impacto:** cenário `rag_rerank` mais lento que `rag_basic`; trade-off qualidade × tempo na apresentação.

**Trabalho futuro:** rerank apenas top-20→5; modelos menores; GPU batch; cache de scores.

---

## 6. Modelos majoritariamente anglófonos no retrieval/rerank

**Limitação:** MiniLM e MS MARCO CrossEncoder não foram treinados primariamente para português.

**Impacto:** possível gap versus pipeline com embeddings multilíngues (`paraphrase-multilingual-mpnet-base-v2`).

**Trabalho futuro:** ablação trocando apenas o encoder; medir EM/F1 e latência.

---

## 7. Viés e cobertura do SQuAD-pt

**Limitação:** domínio Wikipedia-like; perguntas artificiais; contexts duplicados após deduplicação reduzem diversidade.

**Impacto:** resultados não generalizam para domínios fechados (jurídico, médico, municipal).

**Trabalho futuro:** segundo corpus (ex. documentos institucionais) mantendo mesma arquitetura de avaliação.

---

## 8. Desalinhamento pergunta ↔ chunk após indexação

**Limitação:** na consulta, só a **pergunta** é embedada; o context SQuAD original não é reenviado ao modelo.

**Impacto:** se o chunk errado entrar no top_k, o LLM pode alucinar mesmo com prompt restritivo.

**Trabalho futuro:** filtrar retrieval por `source`; incluir metadata de paragraph_id; avaliar recall@k do chunk gold.

---

## 9. Metadata e filtros limitados

**Limitação:** tabela `documents` sem JSON de metadata; `score_threshold` só no rerank.

**Impacto:** não é possível “buscar só no split train” ou por título sem convenção em `source`.

**Trabalho futuro:** coluna `metadata JSONB` + `RetrievalStrategy` com filtros SQL.

---

## 10. `chunk_size` na API não altera índice em tempo real

**Limitação:** parâmetro `chunk_size` em `/ask` é logado mas não re-chunca a base.

**Impacto:** experimentos que variam chunk na consulta sem reindexar não são válidos.

**Trabalho futuro:** grid de indexação (já esboçado em `experiments/runner.py`) + benchmark por configuração.

---

## 11. Métricas EM/F1 não capturam qualidade semântica plena

**Limitação:** paráfrases corretas penalizadas no EM; F1 token-level ignora sinonímia profunda.

**Impacto:** respostas “certas” para humanos podem ter F1 baixo.

**Trabalho futuro:** BERTScore, avaliação humana em subamostra, LLM-as-judge (com cautela metodológica).

---

## 12. Ausência de testes automatizados de regressão

**Limitação:** validação manual e benchmark ad hoc.

**Trabalho futuro:** pytest com mocks OpenAI/pgvector; golden set pequeno com EM/F1 mínimos esperados.

---

## Síntese para a apresentação (slide “Limitações e futuro”)

| Área | Limitação atual | Próximo passo |
|------|-----------------|---------------|
| Geração | API OpenAI | LLM local / híbrido |
| Retrieval | Só vetor | Híbrido BM25+vetor |
| Rerank | Latência + modelo EN | Modelo PT + top_k adaptativo |
| Dados | SQuAD-pt amostral | Corpus de domínio + N maior |
| Avaliação | EM/F1 | Métricas semânticas + humano |

Reconhecer limitações **não enfraquece** o TCC — demonstra maturidade científica e agenda de continuidade.
