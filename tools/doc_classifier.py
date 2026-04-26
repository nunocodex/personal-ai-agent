import json
import re
from datetime import date
from pathlib import Path

import ollama

from core.config import OLLAMA_LLM_MODEL, METADATA_EXTRACTION_PROMPT


def extract_metadata(file_path: Path, content: str) -> dict:
    """
    Uses the LLM to extract metadata from document content.
    The LLM decides category freely — no hardcoded mapping.
    Returns a flat dict ready for Qdrant payload storage.
    """
    sample = " ".join(content.split()[:500])
    prompt = METADATA_EXTRACTION_PROMPT.format(content=sample)

    response = ollama.generate(
        model=OLLAMA_LLM_MODEL,
        prompt=prompt,
        options={"temperature": 0},
    )

    raw = response["response"].strip()

    # Parse JSON — handle extra text around it
    metadata = {}
    try:
        metadata = json.loads(raw)
    except json.JSONDecodeError:
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            metadata = json.loads(raw[start:end])
        except (ValueError, json.JSONDecodeError):
            print(f"   ⚠️  Could not parse metadata, using defaults.")

    # Safe defaults
    metadata.setdefault("category", "personal")
    metadata.setdefault("subcategory", None)
    metadata.setdefault("document_type", None)
    metadata.setdefault("language", None)
    metadata.setdefault("date", None)
    metadata.setdefault("summary", None)
    metadata.setdefault("key_entities", [])
    metadata.setdefault("topics", [])

    # Normalize category
    metadata["category"] = str(metadata["category"]).lower().replace(" ", "_")

    # Qdrant payload: lists → comma-separated strings
    if isinstance(metadata["key_entities"], list):
        metadata["key_entities"] = ", ".join(metadata["key_entities"])
    if isinstance(metadata["topics"], list):
        metadata["topics"] = ", ".join(metadata["topics"])

    # Technical metadata
    metadata["filename"] = file_path.name
    metadata["file_type"] = file_path.suffix.lower()
    metadata["ingested_at"] = date.today().isoformat()

    return metadata


def get_dest_folder(documents_dir: Path, category: str) -> Path:
    """Returns destination folder, creating it if needed."""
    folder = documents_dir / category
    folder.mkdir(parents=True, exist_ok=True)
    return folder