import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings


def retrieve_context(vector_store, query: str) -> list[str]:
    """
    Retrieves the most relevant document chunks for a given query.

    Args:
        vector_store: Qdrant vector store from ingest_documents().
                      If None (no docs uploaded), returns empty list.
        query:        The query string to search against.

    Returns:
        List of strings — the page_content of each retrieved chunk,
        ordered by relevance. Empty list if no vector store is available.
    """
    if vector_store is None:
        return []

    results = vector_store.similarity_search(
        query=query,
        k=settings.rag_top_k,
    )

    return [doc.page_content for doc in results]


def retrieve_context_with_scores(vector_store, query: str) -> list[dict]:
    """
    Retrieves chunks with relevance scores for debugging and confidence gauges.

    Returns:
        List of dicts with keys:
            - content:    str — chunk text
            - score:      float — cosine similarity score (0-1)
            - source:     str — source filename from metadata
    """
    if vector_store is None:
        return []

    results = vector_store.similarity_search_with_score(
        query=query,
        k=settings.rag_top_k,
    )

    return [
        {
            "content": doc.page_content,
            "score":   round(float(score), 4),
            "source":  doc.metadata.get("source_file", "unknown"),
        }
        for doc, score in results
    ]


def build_context_block(vector_store, query: str) -> str:
    """
    Retrieves context and formats it as a single string block
    ready to inject into an LLM prompt.

    Returns:
        Formatted string with each chunk separated by a divider.
        Empty string if no vector store or no results.
    """
    chunks = retrieve_context(vector_store, query)

    if not chunks:
        return ""

    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[Document {i}]\n{chunk.strip()}")

    return "\n\n---\n\n".join(parts)