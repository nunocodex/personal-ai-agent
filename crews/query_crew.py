from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from tools.qdrant_tool import search


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


def build_query_crew(question: str, memory_context: str = "") -> Crew:
    memory_section = f"""
Personal memory context (use this to answer questions about the user):
{memory_context}

""" if memory_context else ""

    agent = Agent(
        role="Personal Document Assistant",
        goal="Answer questions accurately using the user's personal memory and indexed documents.",
        backstory=f"""You are a precise personal assistant with access to the user's documents and personal memory.
{memory_section}When answering, first check if the personal memory already contains the answer.
If not, search the documents. Always cite your source (memory or document name).
Never invent information.""",
        tools=[search_documents_tool],
        llm="ollama/qwen3:8b",
        verbose=True,
    )

    task = Task(
        description=f"""Answer this question: {question}

Steps:
1. Check if personal memory (in your backstory) already answers the question
2. If not, search documents using search_documents tool
3. Provide a clear answer with source (memory or document filename)""",
        expected_output="A clear answer with source cited.",
        agent=agent,
    )

    return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)


def run(question: str, memory_context: str = "") -> str:
    crew = build_query_crew(question, memory_context)
    return str(crew.kickoff())