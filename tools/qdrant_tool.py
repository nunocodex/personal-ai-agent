from typing import Optional
import ollama
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue, FilterSelector
from core.config import OLLAMA_EMBED_MODEL, QDRANT_COLLECTION
from core.qdrant_client import get_qdrant_client, get_or_create_collection


def get_embedding(text: str) -> list:
    """Generates an embedding vector for the given text."""
    response = ollama.embeddings(model=OLLAMA_EMBED_MODEL, prompt=text)
    return response["embedding"]


def index_chunks(chunks: list, metadata: dict, file_stem: str) -> int:
    """
    Indexes text chunks into Qdrant with metadata payload.
    Returns the number of chunks indexed.
    """
    client = get_qdrant_client()
    get_or_create_collection(client)

    points = []
    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)
        point_id = abs(hash(f"{file_stem}_{i}")) % (2**63)
        points.append(PointStruct(
            id=point_id,
            vector=embedding,
            payload={
                **metadata,
                "text": chunk,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
        ))

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    return len(points)


def search(query: str, n_results: int = 5, category: Optional[str] = None) -> list:
    """
    Semantic search in Qdrant.
    Optionally filter by category.
    Returns list of payload dicts with text and metadata.
    """
    client = get_qdrant_client()
    embedding = get_embedding(query)

    query_filter = None
    if category:
        query_filter = Filter(
            must=[FieldCondition(key="category", match=MatchValue(value=category))]
        )

    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=embedding,
        limit=n_results,
        query_filter=query_filter,
        with_payload=True,
    ).points

    return [hit.payload for hit in results]


def delete_by_filename(filename: str) -> str:
    """Deletes all chunks for a given filename."""
    client = get_qdrant_client()
    result = client.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="filename", match=MatchValue(value=filename))]
            )
        )
    )
    return str(result.status)