# Limitações da plataforma

Limitações conhecidas do **software** e oportunidades de evolução técnica.

> Limitações e ameaças à validade do estudo científico: `knowledge-mediation-study` e `research-archive`.

---

## 1. Geração: Ollama local (padrão) ou OpenAI

**Situação atual:** padrão `LLM_PROVIDER=ollama` com modelo configurável (ex.: `phi3`). OpenAI via `LLM_PROVIDER=openai`.

**Limitação (Ollama):** latência maior em CPU; `tokens_used` pode não ser preenchido.

**Limitação (OpenAI):** custo por token, rede e quota.

**Trabalho futuro:** ablação de modelos no mesmo protocolo operacional.

---

## 2. Escala do conjunto de perguntas de exemplo

**Limitação:** fixtures JSON têm N limitado; ampliar N aumenta tempo (modelo local + rerank).

**Trabalho futuro:** execução paralela com rate limit; seeds múltiplas no runner.

---

## 3. Chunking por caracteres

**Limitação:** não respeita fronteiras de frase/parágrafo.

**Trabalho futuro:** chunk por sentenças/tokens ou semantic chunking.

---

## 4. Ausência de busca híbrida (BM25 + denso)

**Limitação:** apenas similaridade de embeddings.

**Trabalho futuro:** `tsvector` + fusão RRF com pgvector.

---

## 5. Custo do reranking

**Limitação:** CrossEncoder cresce com `rerank_top_k`.

**Trabalho futuro:** top-k adaptativo, modelos menores, GPU batch, cache.

---

## 6. Encoders predominantemente anglófonos

**Limitação:** MiniLM / MS MARCO CrossEncoder não focados em português.

**Trabalho futuro:** ablação com embeddings multilíngues.

---

## 7. Cobertura do corpus Wikipédia

**Limitação:** apenas `WIKI_TOPICS`; texto enciclopédico.

**Trabalho futuro:** mais tópicos; corpus PDF/institucional com a mesma arquitectura.

---

## 8. Desalinhamento pergunta ↔ chunk

**Limitação:** na consulta, só a pergunta é embedada.

**Trabalho futuro:** filtros por `source`; metadata; recall@k.

---

## 9. Metadata e filtros limitados

**Limitação:** sem JSONB de metadata rico; `score_threshold` sobretudo no rerank.

**Trabalho futuro:** coluna `metadata JSONB` + filtros SQL na retrieval.

---

## 10. `chunk_size` na API não reindexa

**Limitação:** parâmetro em `/ask` é logado; não altera o índice.

**Trabalho futuro:** grelha de indexação + benchmark por configuração.

---

## 11. Métricas EM/F1

**Limitação:** paráfrases corretas podem ser penalizadas; F1 token-level ignora sinonímia profunda.

**Trabalho futuro:** métricas semânticas opcionais na camada de avaliação.

---

## 12. Cobertura de testes automatizados

**Limitação:** suite ainda pequena face ao perímetro completo.

**Trabalho futuro:** pytest com mocks; golden set mínimo.

---

## Síntese

| Área | Limitação atual | Próximo passo técnico |
|------|-----------------|------------------------|
| Geração | Modelo local por defeito | Ablação de providers |
| Retrieval | Só vetor | Híbrido BM25+vetor |
| Rerank | Latência | top_k adaptativo / modelo PT |
| Dados | Lista de tópicos | Mais fontes documentais |
| Avaliação | EM/F1 | Métricas semânticas opcionais |
