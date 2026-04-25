import base64
import json
import os
import urllib.request
from pathlib import Path

import fitz  # PyMuPDF
import pymupdf4llm
import pdfplumber
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    UnstructuredMarkdownLoader,
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
)

from core.config import (
    SUPPORTED_EXTENSIONS,
    OLLAMA_BASE_URL,
    OLLAMA_VISION_MODEL,
    VISION_EXTRACTION_PROMPT,
    BASE_DIR,
)

# ─── LOAD .env ────────────────────────────────────────────────
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for line in _env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

POPPLER_PATH = os.getenv("POPPLER_PATH", None)


# ─── PDF HELPERS ──────────────────────────────────────────────

def _is_scanned_pdf(file_path: Path) -> bool:
    doc = fitz.open(str(file_path))
    total_text = "".join(page.get_text() for page in doc)
    page_count = doc.page_count
    doc.close()
    return len(total_text.strip()) / max(page_count, 1) < 50


def _has_tables(file_path: Path) -> bool:
    doc = fitz.open(str(file_path))
    for page in doc:
        if page.find_tables().tables:
            doc.close()
            return True
    doc.close()
    return False


def _has_spaced_text(text: str) -> bool:
    """Detects encoding issues like 'S V I L A P P S'."""
    words = text.split()
    if not words:
        return False
    single_chars = sum(1 for w in words[:100] if len(w) == 1)
    return single_chars / min(len(words), 100) > 0.3


def _vision_extract_page(file_path: Path, page_number: int = 1) -> str:
    """
    Extracts text from a single PDF page using the vision model.
    page_number is 1-based.
    """
    from pdf2image import convert_from_path

    convert_kwargs = {"dpi": 200, "first_page": page_number, "last_page": page_number}
    if POPPLER_PATH:
        convert_kwargs["poppler_path"] = POPPLER_PATH

    pages = convert_from_path(str(file_path), **convert_kwargs)
    if not pages:
        return ""

    img_path = BASE_DIR / "data" / "_vision_temp.jpg"
    pages[0].save(str(img_path), "JPEG")

    with open(str(img_path), "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()

    payload = json.dumps({
        "model": OLLAMA_VISION_MODEL,
        "prompt": VISION_EXTRACTION_PROMPT,
        "images": [img_b64],
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    img_path.unlink(missing_ok=True)
    return result.get("response", "").strip()


def _load_pdf(file_path: Path) -> list:
    """
    Intelligent PDF loader:
    1. Scanned PDF       → vision on all pages (future: OCR)
    2. Tables detected   → pdfplumber; if encoding issue on page 1 → vision for page 1 + pdfplumber for rest
    3. Plain text PDF    → pymupdf4llm; if encoding issue → vision for page 1 + rest as-is
    """
    if _is_scanned_pdf(file_path):
        print(f"   ⚠️  Scanned PDF — vision extraction (page 1 only)...")
        text = _vision_extract_page(file_path, 1)
        return [Document(page_content=text, metadata={"source": str(file_path), "page": 1, "extraction": "vision"})] if text else []

    if _has_tables(file_path):
        print(f"   📊 Tables detected, using pdfplumber...")
        documents = []
        with pdfplumber.open(str(file_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                text_parts = []
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                for table in page.extract_tables() or []:
                    if table:
                        rows = [" | ".join(cell or "" for cell in row) for row in table]
                        text_parts.append("\n".join(rows))

                content = "\n\n".join(text_parts)

                # First page with encoding issues → vision
                if i == 0 and _has_spaced_text(content):
                    print(f"   ⚠️  Encoding issue on page 1, using vision...")
                    vision_text = _vision_extract_page(file_path, 1)
                    if vision_text:
                        documents.append(Document(
                            page_content=vision_text,
                            metadata={"source": str(file_path), "page": 1, "extraction": "vision"},
                        ))
                elif content:
                    documents.append(Document(
                        page_content=content,
                        metadata={"source": str(file_path), "page": i + 1},
                    ))
        return documents

    print(f"   📄 Text-based PDF, using pymupdf4llm...")
    markdown = pymupdf4llm.to_markdown(str(file_path))
    if _has_spaced_text(markdown):
        print(f"   ⚠️  Encoding issue detected, using vision for page 1...")
        vision_text = _vision_extract_page(file_path, 1)
        return [Document(page_content=vision_text, metadata={"source": str(file_path), "page": 1, "extraction": "vision"})] if vision_text else []
    return [Document(page_content=markdown, metadata={"source": str(file_path)})]


# ─── LOADER MAP ───────────────────────────────────────────────
# TODO: loader registration to be managed by an agent with user approval
#       for new formats (see project roadmap).

LOADER_MAP = {
    ".pdf":  _load_pdf,
    ".docx": UnstructuredWordDocumentLoader,
    ".md":   UnstructuredMarkdownLoader,
    ".txt":  TextLoader,
    ".csv":  CSVLoader,
}


def load_document(file_path: Path) -> list:
    """
    Loads a document from disk and returns a list of LangChain Document objects.
    Category is decided by the LLM in classifier.py, not here.
    """
    ext = file_path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: {ext}")
    if ext not in LOADER_MAP:
        raise ValueError(f"No loader available for format: {ext}")

    loader = LOADER_MAP[ext]
    if ext == ".pdf":
        return loader(file_path)
    return loader(str(file_path)).load()