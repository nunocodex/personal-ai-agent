from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# ─── PATHS ────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent.parent
DOCUMENTS_DIR = BASE_DIR / "documents"
INBOX_DIR     = DOCUMENTS_DIR / "inbox"
DATA_DIR      = BASE_DIR / "data"
QDRANT_DIR    = DATA_DIR / "qdrant"

# ─── OLLAMA ───────────────────────────────────────────────────
OLLAMA_BASE_URL     = "http://localhost:11434"
OLLAMA_LLM_MODEL    = "qwen3:8b"
OLLAMA_EMBED_MODEL  = "qwen3-embedding:0.6b"
OLLAMA_VISION_MODEL = "qwen3-vl:2b"

# ─── QDRANT ───────────────────────────────────────────────────
QDRANT_COLLECTION   = "personal_documents"
EMBEDDING_SIZE      = 1024

# ─── POPPLER (PDF rendering) ──────────────────────────────────
POPPLER_PATH = os.getenv("POPPLER_PATH", None)

# ─── CHUNKING ─────────────────────────────────────────────────
# mxbai-embed-large max context is 512 tokens
CHUNK_STRATEGIES = {
    "default":    {"chunk_size": 400, "chunk_overlap": 80},
    "finance":    {"chunk_size": 400, "chunk_overlap": 80},
    "legal":      {"chunk_size": 400, "chunk_overlap": 80},
    "health":     {"chunk_size": 400, "chunk_overlap": 80},
    "work":       {"chunk_size": 400, "chunk_overlap": 80},
}

def get_chunk_strategy(category: str) -> dict:
    return CHUNK_STRATEGIES.get(category.lower(), CHUNK_STRATEGIES["default"])

# ─── PROMPTS ──────────────────────────────────────────────────
METADATA_EXTRACTION_PROMPT = """You are a document analyst. Analyze the document content and extract metadata.

Return ONLY a valid JSON object (no extra text, no markdown):
{{
  "category": "<main domain, e.g. legal, work, health, finance, personal, education>",
  "subcategory": "<specific type, e.g. invoice, contract, payslip, tax_return>",
  "document_type": "<e.g. letter, report, receipt>",
  "language": "<ISO 639-1 code, e.g. it, en>",
  "date": "<YYYY-MM-DD or null>",
  "summary": "<1-2 sentence summary>",
  "key_entities": ["<people, companies, organizations>"],
  "topics": ["<main topics or keywords>"]
}}

Document content (first 500 words):
{content}"""

VISION_EXTRACTION_PROMPT = """This is a page from an Italian payslip (busta paga).
Extract ALL visible text and numeric values. Pay special attention to:
- Employee name and fiscal code
- Month and year
- All monetary values with their labels (retribuzione lorda, netto a pagare, INPS, IRPEF, etc.)
- All table rows with amounts

Format as structured label: value pairs. Be thorough - include every number you see."""