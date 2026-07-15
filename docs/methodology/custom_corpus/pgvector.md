title: pgvector
source_url: https://github.com/pgvector/pgvector
topic: pgvector
---
pgvector é uma extensão open source para PostgreSQL que adiciona o tipo de dado vector e operadores de busca por similaridade. Permite armazenar embeddings gerados por modelos de linguagem ou de visão e recuperar os vizinhos mais próximos por distância (por exemplo, cosseno ou L2). É usada em pipelines RAG para persistir representações vetoriais no mesmo banco relacional da aplicação, combinando SQL tradicional com busca semântica aproximada (ANN). A extensão não substitui um modelo de embeddings: ela indexa e consulta vetores já calculados. Em sistemas experimentais, a ausência de artigo equivalente na Wikipédia em português motiva este documento complementar curado, com rastreio explícito da fonte oficial.
