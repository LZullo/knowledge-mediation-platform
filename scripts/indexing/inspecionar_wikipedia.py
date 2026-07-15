"""
Inspeção do corpus técnico da Wikipédia (lista controlada de tópicos).
"""

import logging

from app.dados.wikipedia_loader import WIKI_TOPICS, fetch_wikipedia_corpus

logging.basicConfig(level=logging.INFO)

CONTENT_SNIPPET_LEN = 400


def main() -> None:
    pages, skipped = fetch_wikipedia_corpus(WIKI_TOPICS)
    print(f"\nTópicos solicitados: {len(WIKI_TOPICS)}")
    print(f"Páginas obtidas: {len(pages)} | Ignoradas: {skipped}\n")

    for i, page in enumerate(pages, start=1):
        print(f"\n--- {i}/{len(pages)} ---")
        print(f"Tópico: {page.topic}")
        print(f"Título: {page.title}")
        print(f"URL: {page.source_url}")
        print(f"Tamanho: {len(page.content)} caracteres")
        snippet = page.content[:CONTENT_SNIPPET_LEN]
        if len(page.content) > CONTENT_SNIPPET_LEN:
            snippet += "..."
        print(f"Trecho: {snippet}")
        print("=" * 40)


if __name__ == "__main__":
    main()
