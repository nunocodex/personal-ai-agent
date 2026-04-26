from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from tools.qdrant_tool import search
from tools.aggregator_tool import aggregate_by_filename, format_aggregated


@tool("search_documents")
def search_documents_tool(query: str) -> str:
    """Searches indexed documents using semantic search. Returns relevant text chunks with sources."""
    results = search(query, n_results=5)
    if not results:
        return "No relevant documents found."
    parts = []
    for r in results:
        source = r.get("filename", "unknown")
        text = r.get("text", "")
        parts.append(f"[Source: {source}]\n{text}")
    return "\n\n---\n\n".join(parts)


@tool("aggregate_documents")
def aggregate_documents_tool(query: str) -> str:
    """
    Searches ALL indexed documents and groups results by filename.
    Use this for aggregation questions like totals, comparisons across multiple documents,
    or when you need to summarize information from many files at once.
    Examples: total annual salary, all payslips for a year, expenses across months.
    """
    grouped = aggregate_by_filename(query, n_results=20)
    return format_aggregated(grouped)


def build_query_crew(question: str, memory_context: str = "") -> Crew:
    memory_section = f"""
Personal memory context (use this to answer questions about the user):
{memory_context}

""" if memory_context else ""

    agent = Agent(
        role="Personal Document Assistant",
        goal="Answer questions accurately using the user's personal memory and indexed documents.",
        backstory=f"""You are a precise personal assistant with access to the user's documents and personal memory.
{memory_section}When answering:
- First check if personal memory answers the question
- For single-document questions: use search_documents
- For aggregation questions (totals, comparisons, multiple files): use aggregate_documents
- Always cite your source (memory or document filename)
- Never invent information""",
        tools=[search_documents_tool, aggregate_documents_tool],
        llm="ollama/qwen3:8b",
        verbose=True,
    )

    task = Task(
        description=f"""Answer this question: {question}

Steps:
1. Check if personal memory already answers the question
2. Choose the right tool: search_documents for specific queries, aggregate_documents for totals/comparisons
3. Provide a clear answer with source cited""",
        expected_output="A clear answer with source cited.",
        agent=agent,
    )

    return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)


def run(question: str, memory_context: str = "") -> str:
    crew = build_query_crew(question, memory_context)
    return str(crew.kickoff())