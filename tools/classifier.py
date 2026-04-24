import json
from datetime import date
from pathlib import Path

import ollama

from core.config import OLLAMA_LLM_MODEL, METADATA_EXTRACTION_PROMPT


def extract_metadata(file_path: Path, content: str) -> dict:
    """
    Uses the LLM to extract all available metadata from a document.
    The LLM decides the category freely — no hardcoded mapping.

    Returns a metadata dict ready to be stored in ChromaDB.
    Falls back to safe defaults if the LLM response cannot be parsed.
    """
    sample = " ".join(content.split()[:500])
    prompt = METADATA_EXTRACTION_PROMPT.format(content=sample)

    response = ollama.generate(
        model=OLLAMA_LLM_MODEL,
        prompt=prompt,
        options={"temperature": 0},  # deterministic output
    )

    raw = response["response"].strip()

    # Parse JSON response
    try:
        metadata = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON block if the model added extra text
        try:
            start = raw.index("{")
            end   = raw.rindex("}") + 1
            metadata = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            print(f"   ⚠️  Could not parse LLM response, using defaults.")
            metadata = {}

    # Ensure all expected fields exist with safe defaults
    metadata.setdefault("category",      "personal")
    metadata.setdefault("subcategory",   None)
    metadata.setdefault("document_type", None)
    metadata.setdefault("language",      None)
    metadata.setdefault("date",          None)
    metadata.setdefault("summary",       None)
    metadata.setdefault("key_entities",  [])
    metadata.setdefault("topics",        [])

    # Normalize category: lowercase, no spaces
    metadata["category"] = str(metadata["category"]).lower().replace(" ", "_")

    # ChromaDB requires metadata values to be str, int, float, or bool.
    # Convert lists to comma-separated strings.
    if isinstance(metadata["key_entities"], list):
        metadata["key_entities"] = ", ".join(metadata["key_entities"])
    if isinstance(metadata["topics"], list):
        metadata["topics"] = ", ".join(metadata["topics"])

    # Add technical metadata
    metadata["filename"]    = file_path.name
    metadata["file_type"]   = file_path.suffix.lower()
    metadata["ingested_at"] = date.today().isoformat()

    return metadata


def get_document_folder(base_dir: Path, category: str) -> Path:
    """
    Returns the destination folder for a document based on its category.
    Creates the folder automatically if it does not exist.
    """
    folder = base_dir / category
    folder.mkdir(parents=True, exist_ok=True)
    return folder