import ollama
from core.config import OLLAMA_LLM_MODEL
from core.vectorstore import get_collection


SYSTEM_PROMPT = """You are a personal assistant with access to the user's documents.
Answer questions based strictly on the provided context.
If the answer is not in the context, say so clearly.
Always mention which document(s) the information comes from."""


def run(question: str, n_results: int = 5) -> str:
    """
    Query agent — answers questions using documents indexed in ChromaDB.

    Steps:
      1. Embeds the question and retrieves relevant chunks from ChromaDB
      2. Builds a prompt with the retrieved context
      3. Asks the LLM to answer based on the context
    """
    collection = get_collection()

    if collection.count() == 0:
        return "⚠️  No documents indexed yet. Run 'python main.py ingest' first."

    # 1. Retrieve relevant chunks
    results = collection.query(
        query_texts=[question],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas"],
    )

    chunks    = results["documents"][0]
    metadatas = results["metadatas"][0]

    if not chunks:
        return "⚠️  No relevant documents found for your question."

    # 2. Build context block
    context_parts = []
    for chunk, meta in zip(chunks, metadatas):
        source = meta.get("filename", "unknown")
        context_parts.append(f"[Source: {source}]\n{chunk}")

    context = "\n\n---\n\n".join(context_parts)

    # 3. Build prompt and ask the LLM
    prompt = f"""{SYSTEM_PROMPT}

Context from documents:
{context}

Question: {question}

Answer:"""

    response = ollama.generate(
        model=OLLAMA_LLM_MODEL,
        prompt=prompt,
        options={"temperature": 0.2},
    )

    return response["response"].strip()