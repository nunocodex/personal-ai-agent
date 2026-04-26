from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from tools.qdrant_tool import search


# ─── TOOLS ────────────────────────────────────────────────────

@tool("search_documents")
def search_documents_tool(query: str) -> str:
    """Searches indexed documents in Qdrant using semantic search. Returns relevant text chunks."""
    results = search(query, n_results=5)
    if not results:
        return "No relevant documents found."

    parts = []
    for r in results:
        source = r.get("filename", "unknown")
        text = r.get("text", "")
        parts.append(f"[Source: {source}]\n{text}")

    return "\n\n---\n\n".join(parts)


# ─── AGENT ────────────────────────────────────────────────────

def build_query_crew(question: str) -> Crew:
    agent = Agent(
        role="Personal Document Assistant",
        goal="Answer questions accurately using only the content found in the user's indexed documents.",
        backstory="""You are a precise personal assistant with access to the user's documents.
You always search before answering. You never invent information.
If the answer is not in the documents, you say so clearly and mention which documents you checked.""",
        tools=[search_documents_tool],
        llm="ollama/qwen3:8b",
        verbose=True,
    )

    task = Task(
        description=f"""Answer the following question using the user's documents:

Question: {question}

Steps:
1. Search the documents using search_documents tool
2. Analyze the results carefully
3. Provide a clear, accurate answer based only on what you found
4. Always cite which document(s) the information comes from""",
        expected_output="A clear answer to the question with document sources cited.",
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )


def run(question: str) -> str:
    crew = build_query_crew(question)
    result = crew.kickoff()
    return str(result)