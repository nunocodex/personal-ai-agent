from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredMarkdownLoader,
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
)
from core.config import SUPPORTED_EXTENSIONS


# ─── LOADER MAP ───────────────────────────────────────────────
# Maps file extension to its LangChain loader class.
# To add a new format:
#   1. Import the loader above
#   2. Add the extension here
#   3. Add the extension in core/config.py SUPPORTED_EXTENSIONS

LOADER_MAP = {
    ".pdf":  PyPDFLoader,
    ".docx": UnstructuredWordDocumentLoader,
    ".md":   UnstructuredMarkdownLoader,
    ".txt":  TextLoader,
    ".csv":  CSVLoader,
}


def load_document(file_path: Path) -> list:
    """
    Loads a document from disk and returns a list of LangChain Document objects.
    Raises ValueError if the file format is not supported.
    Category is no longer determined here — the LLM decides it in classifier.py.
    """
    ext = file_path.suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file format: {ext}")

    if ext not in LOADER_MAP:
        raise ValueError(f"No loader available for format: {ext}")

    loader = LOADER_MAP[ext](str(file_path))
    return loader.load()