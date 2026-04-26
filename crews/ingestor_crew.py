import json
import shutil
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool

from core.config import DOCUMENTS_DIR, get_chunk_strategy
from tools.pdf_loader import load_pdf
from tools.doc_classifier import extract_metadata, get_dest_folder
from tools.qdrant_tool import index_chunks


@tool("process_document")
def process_document_tool(file_path: str) -> str:
    """
    Processes a document through the full pipeline:
    load → classify → index → move.
    Returns a summary of what was done.
    """
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: File not found: {file_path}"

    # 1. Load
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

    if not docs:
        return f"ERROR: Could not extract content from {path.name}"

    page_as_chunk = any(d.metadata.get("page_as_chunk") for d in docs)
    full_content = " ".join(d.page_content for d in docs)

    # 2. Classify
    metadata = extract_metadata(path, full_content)
    category = metadata.get("category", "personal")
    print(f"   📁 Category: {category}")
    print(f"   📝 Summary: {metadata.get('summary', 'N/A')}")

    # 3. Index
    if page_as_chunk:
        chunks = [d.page_content for d in docs if d.page_content.strip()]
        print(f"   📄 {len(chunks)} pages as individual chunks")
    else:
        strategy = get_chunk_strategy(category)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=strategy["chunk_size"],
            chunk_overlap=strategy["chunk_overlap"],
        )
        chunks = [c for c in splitter.split_text(full_content) if len(c.split()) >= 5]

    count = index_chunks(chunks, metadata, path.stem)
    print(f"   ✂️  Indexed {count} chunks")

    # 4. Move
    dest_folder = get_dest_folder(DOCUMENTS_DIR, category)
    dest = dest_folder / path.name
    if dest.exists():
        dest = dest_folder / f"{path.stem}_1{path.suffix}"
    shutil.move(str(path), str(dest))
    print(f"   ✅ Moved to documents/{category}/")

    return json.dumps({
        "status": "success",
        "filename": path.name,
        "category": category,
        "summary": metadata.get("summary", ""),
        "chunks_indexed": count,
        "destination": f"documents/{category}/",
    })


def build_ingestor_crew(file_path: str) -> Crew:
    agent = Agent(
        role="Document Ingestor",
        goal="Process documents into the personal knowledge base.",
        backstory="You process documents by calling process_document once per file.",
        tools=[process_document_tool],
        llm="ollama/qwen3:8b",
        verbose=True,
    )

    task = Task(
        description=f'Process this document: {file_path}\nCall process_document with file_path="{file_path}"',
        expected_output="JSON with status, category, summary, chunks_indexed, destination.",
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