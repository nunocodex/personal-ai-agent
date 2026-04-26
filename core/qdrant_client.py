from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from core.config import QDRANT_DIR, QDRANT_COLLECTION, EMBEDDING_SIZE


def get_qdrant_client() -> QdrantClient:
    """
    Returns a file-based Qdrant client.
    To switch to Docker: change path= to host="localhost", port=6333
    """
    client = QdrantClient(path=str(QDRANT_DIR))
    return client


def get_or_create_collection(client: QdrantClient):
    """Creates the collection if it doesn't exist."""
    existing = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=EMBEDDING_SIZE,
                distance=Distance.COSINE,
            ),
        )
    return client.get_collection(QDRANT_COLLECTION)