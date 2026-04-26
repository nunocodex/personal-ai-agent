import shutil
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from core.config import DOCUMENTS_DIR, INBOX_DIR, get_chunk_strategy
from tools.pdf_loader import load_pdf
from tools.doc_classifier import extract_metadata, get_dest_folder
from tools.qdrant_tool import index_chunks


# ─── TOOLS ────────────────────────────────────────────────────

@tool("load_document")
def load_document_tool(file_path: str) -> str:
    """Loads a document from disk and returns its text content."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        docs = load_pdf(path)
    else:
        from langchain_community.document_loaders import (
            UnstructuredMarkdownLoader, TextLoader,
            CSVLoader, UnstructuredWordDocumentLoader,
        )
        loaders = {
            ".md": UnstructuredMarkdownLoader,
            ".txt": TextLoader,
            ".csv": CSVLoader,
            ".docx": UnstructuredWordDocumentLoader,
        }
        if ext not in loaders:
            return f"ERROR: Unsupported format {ext}"
        docs = loaders[ext](str(path)).load()

    return " ".join(d.page_content for d in docs)


@tool("classify_document")
def classify_document_tool(file_path: str, content: str) -> str:
    """Extracts metadata from document content using LLM. Returns JSON string."""
    import json
    metadata = extract_metadata(Path(file_path), content)
    return json.dumps(metadata)


@tool("index_document")
def index_document_tool(file_path: str, content: str, metadata_json: str) -> str:
    """Splits content into chunks and indexes them into Qdrant."""
    import json
    metadata = json.loads(metadata_json)
    category = metadata.get("category", "personal")
    strategy = get_chunk_strategy(category)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=strategy["chunk_size"],
        chunk_overlap=strategy["chunk_overlap"],
    )
    chunks = splitter.split_text(content)
    # Filter low-quality chunks
    good_chunks = [c for c in chunks if len(c.split()) >= 5]

    count = index_chunks(good_chunks, metadata, Path(file_path).stem)
    return f"Indexed {count} chunks for {Path(file_path).name}"


@tool("move_document")
def move_document_tool(file_path: str, metadata_json: str) -> str:
    """Moves document to the correct category folder."""
    import json
    metadata = json.loads(metadata_json)
    category = metadata.get("category", "personal")
    src = Path(file_path)
    dest_folder = get_dest_folder(DOCUMENTS_DIR, category)
    dest = dest_folder / src.name
    if dest.exists():
        dest = dest_folder / f"{src.stem}_1{src.suffix}"
    shutil.move(str(src), str(dest))
    return f"Moved {src.name} → documents/{category}/"


# ─── AGENT ────────────────────────────────────────────────────

def build_ingestor_crew(file_path: str) -> Crew:
    agent = Agent(
        role="Document Ingestor",
        goal="Process a document: load it, extract metadata, index it in Qdrant, and move it to the correct folder.",
        backstory="You are a precise document processing agent. You follow steps in order and never skip one.",
        tools=[load_document_tool, classify_document_tool, index_document_tool, move_document_tool],
        llm=f"ollama/qwen3:8b",
        verbose=True,
    )

    task = Task(
        description=f"""Process the document at: {file_path}

Steps (in order):
1. Load the document using load_document tool
2. Classify it using classify_document tool (pass file_path and content)
3. Index it using index_document tool (pass file_path, content, and metadata JSON)
4. Move it using move_document tool (pass file_path and metadata JSON)

Report the category, summary, and number of chunks indexed.""",
        expected_output="Document processed successfully with category, summary, and chunk count.",
        agent=agent,
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )


def run(file_path: str):
    crew = build_ingestor_crew(file_path)
    return crew.kickoff()