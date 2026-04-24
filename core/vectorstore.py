import chromadb
from chromadb.utils import embedding_functions
from core.config import (
    DATA_DIR,
    CHROMA_COLLECTION_NAME,
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_MODEL,
)


def get_collection():
    """
    Returns the ChromaDB collection with Ollama embeddings.
    Creates it if it doesn't exist yet.
    """
    client = chromadb.PersistentClient(path=str(DATA_DIR))

    embedding_fn = embedding_functions.OllamaEmbeddingFunction(
        url=f"{OLLAMA_BASE_URL}/api/embeddings",
        model_name=OLLAMA_EMBED_MODEL,
    )

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        embedding_function=embedding_fn,
    )

    return collection
