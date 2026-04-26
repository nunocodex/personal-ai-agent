import json
from datetime import date
from pathlib import Path

from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from core.config import BASE_DIR
from tools.qdrant_tool import search

MEMORY_FILE = BASE_DIR / "data" / "personal_memory.json"


def _load_memory() -> dict:
    if MEMORY_FILE.exists():
        return json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    return {"notes": [], "extracted": {}, "updated_at": None}


def _save_memory(memory: dict):
    MEMORY_FILE.parent.mkdir(exist_ok=True)
    memory["updated_at"] = date.today().isoformat()
    MEMORY_FILE.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")


@tool("save_memory")
def save_memory_tool(key: str, value: str) -> str:
    """Saves a personal information note to memory. Use key as category (e.g. 'work', 'preference', 'fact') and value as the information to store."""
    memory = _load_memory()
    memory["notes"].append({
        "key": key,
        "value": value,
        "saved_at": date.today().isoformat(),
    })
    _save_memory(memory)
    return f"Saved: [{key}] {value}"


@tool("extract_from_documents")
def extract_from_documents_tool(query: str) -> str:
    """Searches indexed documents to extract personal information matching the query."""
    results = search(query, n_results=5)
    if not results:
        return "No relevant information found in documents."
    parts = []
    for r in results:
        source = r.get("filename", "unknown")
        text = r.get("text", "")[:300]
        parts.append(f"[{source}]\n{text}")
    return "\n\n---\n\n".join(parts)


@tool("read_memory")
def read_memory_tool(query: str) -> str:
    """Reads current personal memory and returns information relevant to the query."""
    memory = _load_memory()
    if not memory["notes"] and not memory["extracted"]:
        return "Memory is empty."

    parts = []
    query_lower = query.lower()

    for note in memory["notes"]:
        if query_lower in note["key"].lower() or query_lower in note["value"].lower():
            parts.append(f"[{note['key']}] {note['value']}")

    for k, v in memory.get("extracted", {}).items():
        if query_lower in k.lower() or query_lower in str(v).lower():
            parts.append(f"[extracted:{k}] {v}")

    return "\n".join(parts) if parts else "No matching information found in memory."


def get_memory_context() -> str:
    """Returns full memory as context string to inject into query crew."""
    memory = _load_memory()
    if not memory["notes"] and not memory["extracted"]:
        return ""

    parts = ["=== Personal Memory ==="]
    for note in memory["notes"]:
        parts.append(f"[{note['key']}] {note['value']}")
    for k, v in memory.get("extracted", {}).items():
        parts.append(f"[{k}] {v}")

    return "\n".join(parts)


def build_memory_crew(instruction: str) -> Crew:
    agent = Agent(
        role="Personal Memory Manager",
        goal="Manage the user's personal memory by saving notes and extracting information from documents.",
        backstory="You are a precise personal assistant. When asked to remember something, you save it. When asked to extract info from documents, you search and save results.",
        tools=[save_memory_tool, extract_from_documents_tool, read_memory_tool],
        llm="ollama/qwen3:8b",
        verbose=True,
    )

    task = Task(
        description=f"""Handle this memory instruction: {instruction}

- If saving something: use save_memory tool
- If extracting from documents: use extract_from_documents then save_memory
- If reading memory: use read_memory tool
- Always confirm what was done.""",
        expected_output="Confirmation of the memory operation performed.",
        agent=agent,
    )

    return Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)


def run(instruction: str) -> str:
    crew = build_memory_crew(instruction)
    return str(crew.kickoff())