import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from tools.exceptions import RAGIngestionError


def ingest_documents(file_sources: list, embeddings) -> Optional[object]:
    """
    Loads, chunks, and embeds uploaded supporting documents into a
    Qdrant in-memory vector store scoped to the current session.

    Args:
        file_sources: List of file paths (str or Path).
                      Supports PDF and plain text files.
        embeddings:   LangChain embeddings instance from embedding_factory.

    Returns:
        A Qdrant vector store instance ready for similarity search.
        Returns None if no documents were successfully ingested.

    Raises:
        RAGIngestionError: If a document cannot be loaded or embedded.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_qdrant import QdrantVectorStore
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    all_chunks = []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    for source in file_sources:
        try:
            docs = _load_document(source)
            chunks = splitter.split_documents(docs)
            all_chunks.extend(chunks)
        except RAGIngestionError:
            raise
        except Exception as e:
            filename = getattr(source, "name", str(source))
            raise RAGIngestionError(filename=filename, detail=str(e))

    if not all_chunks:
        return None

    # Qdrant in-memory — no server, no Docker, discards on session close
    client = QdrantClient(":memory:")
    collection_name = "session_documents"

    try:
        sample_vector = embeddings.embed_query("test")
        vector_size = len(sample_vector)
    except Exception as e:
        raise RAGIngestionError(
            filename="embeddings",
            detail=f"Embedding model unavailable: {str(e)}"
        )

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    vector_store.add_documents(all_chunks)
    return vector_store


def _load_document(source) -> list:
    """
    Loads a single document from a file path.
    Supports PDF and plain text.
    """
    filename = getattr(source, "name", str(source))
    suffix = Path(filename).suffix.lower()

    if suffix == ".pdf":
        return _load_pdf(source, filename)
    elif suffix in (".txt", ".md"):
        return _load_text(source, filename)
    else:
        return _load_text(source, filename)


def _load_pdf(source, filename: str) -> list:
    """Loads a PDF using PyPDFLoader. Handles both file paths and file-like objects."""
    try:
        from langchain_community.document_loaders import PyPDFLoader
        import tempfile
        import os

        if hasattr(source, "read"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(source.read())
                tmp_path = tmp.name
            try:
                loader = PyPDFLoader(tmp_path)
                docs = loader.load()
            finally:
                os.unlink(tmp_path)
        else:
            loader = PyPDFLoader(str(source))
            docs = loader.load()

        for doc in docs:
            doc.metadata["source_file"] = filename
        return docs

    except Exception as e:
        raise RAGIngestionError(filename=filename, detail=str(e))


def _load_text(source, filename: str) -> list:
    """Loads a plain text or markdown document."""
    try:
        from langchain_core.documents import Document

        if hasattr(source, "read"):
            content = source.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
        else:
            content = Path(source).read_text(encoding="utf-8", errors="ignore")

        return [Document(
            page_content=content,
            metadata={"source_file": filename},
        )]

    except Exception as e:
        raise RAGIngestionError(filename=filename, detail=str(e))