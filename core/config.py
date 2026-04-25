from pathlib import Path

# ─── PATHS ────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
INBOX_DIR     = DOCUMENTS_DIR / "inbox"
DATA_DIR      = BASE_DIR / "data"

# ─── OLLAMA ───────────────────────────────────────────────────
OLLAMA_BASE_URL    = "http://localhost:11434"
OLLAMA_LLM_MODEL   = "qwen3:8b"
OLLAMA_EMBED_MODEL = "nomic-embed-text"
OLLAMA_VISION_MODEL = "llama3.2-vision:11b"

# ─── CHROMADB ─────────────────────────────────────────────────
CHROMA_COLLECTION_NAME = "personal_documents"

# ─── SUPPORTED FILE FORMATS ───────────────────────────────────
# To add a new format: add the extension here and its loader in tools/loaders.py
SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".md", ".txt", ".csv", ".xlsx"]

# ─── ADAPTIVE CHUNKING STRATEGIES ─────────────────────────────
CHUNK_STRATEGIES = {
    "default": {
        "chunk_size": 500,
        "chunk_overlap": 50,
    },
    "finance": {
        "chunk_size": 1500,
        "chunk_overlap": 150,
    },
    "legal": {
        "chunk_size": 1500,
        "chunk_overlap": 150,
    },
    "tax": {
        "chunk_size": 1500,
        "chunk_overlap": 150,
    },
    "accounting": {
        "chunk_size": 1500,
        "chunk_overlap": 150,
    },
    "health": {
        "chunk_size": 1000,
        "chunk_overlap": 100,
    },
    "medical": {
        "chunk_size": 1000,
        "chunk_overlap": 100,
    },
}


def get_chunk_strategy(category: str) -> dict:
    """
    Returns the chunking strategy for a given category.
    Falls back to 'default' if the category is not explicitly mapped.
    """
    return CHUNK_STRATEGIES.get(category.lower(), CHUNK_STRATEGIES["default"])


# ─── METADATA EXTRACTION PROMPT ───────────────────────────────
METADATA_EXTRACTION_PROMPT = """You are a document analyst. Analyze the document content below and extract all available metadata.

Return ONLY a valid JSON object with this structure (no extra text, no markdown):
{{
  "category": "<main domain, e.g. legal, work, health, finance, personal, education>",
  "subcategory": "<specific type, e.g. invoice, contract, prescription, tax_return>",
  "document_type": "<describe the document format, e.g. letter, report, receipt>",
  "language": "<ISO 639-1 code, e.g. it, en, fr>",
  "date": "<most relevant date found in the document, format YYYY-MM-DD, or null if not found>",
  "summary": "<1-2 sentence summary of the document content>",
  "key_entities": ["<list of people, companies, organizations, or institutions mentioned>"],
  "topics": ["<list of main topics or keywords>"]
}}

Rules:
- Be specific and accurate.
- If a field cannot be determined, use null.
- key_entities and topics must be arrays, even if empty.
- Reply with valid JSON only.

Document content (first 500 words):
{content}"""

# ─── VISION EXTRACTION PROMPT ─────────────────────────────────
VISION_EXTRACTION_PROMPT = """This is a page from a document. Extract ALL visible text and data you can see.
Include: names, dates, monetary values, labels, table contents, and any other information.
Format the output as clean, structured text. Be thorough and accurate."""