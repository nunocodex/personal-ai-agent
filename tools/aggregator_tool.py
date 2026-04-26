from tools.qdrant_tool import search


def aggregate_by_filename(query: str, n_results: int = 20) -> dict:
    """
    Searches documents and groups results by filename.
    Returns a dict: {filename: [text_chunks]}
    """
    results = search(query, n_results=n_results)
    grouped = {}
    for r in results:
        filename = r.get("filename", "unknown")
        text = r.get("text", "")
        if filename not in grouped:
            grouped[filename] = []
        grouped[filename].append(text)
    return grouped


def format_aggregated(grouped: dict) -> str:
    """Formats grouped results as a readable string for the LLM."""
    if not grouped:
        return "No relevant documents found."
    parts = []
    for filename, chunks in grouped.items():
        combined = "\n".join(chunks[:3])  # max 3 chunks per file
        parts.append(f"=== {filename} ===\n{combined}")
    return "\n\n".join(parts)