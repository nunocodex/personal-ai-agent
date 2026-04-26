import base64
import json
import re
import time
import urllib.request
from pathlib import Path

import fitz
import pymupdf4llm
import pdfplumber
from pdfminer.high_level import extract_pages
from pdfminer.layout import LAParams, LTTextBox
from langchain_core.documents import Document

from core.config import (
    POPPLER_PATH,
    OLLAMA_BASE_URL,
    OLLAMA_VISION_MODEL,
    VISION_EXTRACTION_PROMPT,
    BASE_DIR,
)

VISION_PAGE_DELAY = 2
VISION_MAX_RETRIES = 3
VISION_TIMEOUT = 180
VISION_DPI = 150


def _is_scanned(file_path: Path) -> bool:
    doc = fitz.open(str(file_path))
    total = "".join(p.get_text() for p in doc)
    count = doc.page_count
    doc.close()
    return len(total.strip()) / max(count, 1) < 50


def _has_tables(file_path: Path) -> bool:
    doc = fitz.open(str(file_path))
    for page in doc:
        if page.find_tables().tables:
            doc.close()
            return True
    doc.close()
    return False


def _has_spaced_text(text: str) -> bool:
    words = text.split()
    if not words:
        return False
    single = sum(1 for w in words[:100] if len(w) == 1)
    return single / min(len(words), 100) > 0.3


def _normalize(text: str) -> str:
    return "\n".join(
        re.sub(r'\s+', ' ', line).strip()
        for line in text.splitlines()
        if re.sub(r'\s+', ' ', line).strip()
    )


def _img_to_b64(img_path: Path) -> str:
    with open(str(img_path), "rb") as f:
        return base64.b64encode(f.read()).decode()


def _call_vision_b64(img_b64: str, label: str) -> str:
    payload = json.dumps({
        "model": OLLAMA_VISION_MODEL,
        "prompt": VISION_EXTRACTION_PROMPT,
        "images": [img_b64],
        "stream": False,
    }).encode()

    for attempt in range(1, VISION_MAX_RETRIES + 1):
        try:
            print(f"   👁️  {label} (attempt {attempt})...")
            req = urllib.request.Request(
                f"{OLLAMA_BASE_URL}/api/generate",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=VISION_TIMEOUT) as resp:
                text = json.loads(resp.read().decode()).get("response", "").strip()
                if text:
                    return text
                print(f"   ⚠️  Empty response, retrying...")
        except Exception as e:
            print(f"   ⚠️  {label} attempt {attempt} failed: {e}")
            if attempt < VISION_MAX_RETRIES:
                time.sleep(VISION_PAGE_DELAY * attempt * 2)

    return ""


def _extract_vision(file_path: Path) -> list:
    """
    Extracts each PDF page via vision model.
    Each page is split into 3 sections (top/middle/bottom) to stay within
    the model's image size limits. Results are merged into one Document per page.
    """
    try:
        from pdf2image import convert_from_path
    except ImportError:
        raise ImportError("Run: pip install pdf2image")

    print(f"   👁️  Vision extraction ({OLLAMA_VISION_MODEL}) — 3-section split...")

    kwargs = {"dpi": VISION_DPI}
    if POPPLER_PATH:
        kwargs["poppler_path"] = POPPLER_PATH

    pages_img = convert_from_path(str(file_path), **kwargs)
    img_dir = BASE_DIR / "data"
    img_dir.mkdir(exist_ok=True)

    documents = []
    total = len(pages_img)

    for i, page_img in enumerate(pages_img):
        w, h = page_img.width, page_img.height
        page_texts = []

        sections = [
            ("top",    (0, 0,           w, h // 3)),
            ("middle", (0, h // 3,      w, (h * 2) // 3)),
            ("bottom", (0, (h * 2) // 3, w, h)),
        ]

        for section, box in sections:
            crop = page_img.crop(box)
            img_path = img_dir / f"_vision_p{i}_{section}.jpg"
            crop.save(str(img_path), "JPEG")
            img_b64 = _img_to_b64(img_path)
            img_path.unlink(missing_ok=True)

            text = _call_vision_b64(img_b64, f"Page {i + 1}/{total} {section}")
            if text:
                page_texts.append(text)

            time.sleep(VISION_PAGE_DELAY)

        if page_texts:
            merged = "\n\n".join(page_texts)
            documents.append(Document(
                page_content=merged,
                metadata={
                    "source": str(file_path),
                    "page": i + 1,
                    "extraction": "vision",
                    "page_as_chunk": True,
                },
            ))

        if i < total - 1:
            time.sleep(VISION_PAGE_DELAY)

    return documents


def _extract_layout(file_path: Path) -> list:
    print(f"   🔍 Layout analysis (PDFMiner)...")
    laparams = LAParams(char_margin=2.0, line_margin=0.5, word_margin=0.1, all_texts=True)
    documents = []

    for page_num, page_layout in enumerate(extract_pages(str(file_path), laparams=laparams)):
        elements = []
        for el in page_layout:
            if isinstance(el, LTTextBox):
                text = el.get_text().strip()
                if text:
                    elements.append((round(-el.y1, 0), round(el.x0, 0), text))
        if not elements:
            continue

        elements.sort(key=lambda e: (e[0], e[1]))
        rows, current_row, current_y = [], [], None
        for y, x, text in elements:
            if current_y is None or abs(y - current_y) <= 8:
                current_row.append((x, text))
                current_y = y
            else:
                rows.append(sorted(current_row))
                current_row, current_y = [(x, text)], y
        if current_row:
            rows.append(sorted(current_row))

        lines = [re.sub(r'\s+', ' ', " | ".join(t for _, t in row)).strip() for row in rows]
        page_text = "\n".join(l for l in lines if l)
        if page_text:
            documents.append(Document(
                page_content=page_text,
                metadata={"source": str(file_path), "page": page_num + 1, "extraction": "layout"},
            ))

    return documents


def load_pdf(file_path: Path) -> list:
    """
    Intelligent PDF loader:
    1. Scanned         → vision (3-section split)
    2. Tables + spaced → vision (3-section split)
    3. Tables          → pdfplumber
    4. Plain text      → pymupdf4llm
    """
    if _is_scanned(file_path):
        print(f"   ⚠️  Scanned PDF → vision...")
        return _extract_vision(file_path)

    if _has_tables(file_path):
        with pdfplumber.open(str(file_path)) as pdf:
            first = pdf.pages[0].extract_text() or ""

        if _has_spaced_text(first):
            print(f"   📊 Tables + encoding issue → vision...")
            return _extract_vision(file_path)

        print(f"   📊 Tables → pdfplumber...")
        pages = []
        with pdfplumber.open(str(file_path)) as pdf:
            for i, page in enumerate(pdf.pages):
                parts = []
                if t := page.extract_text():
                    parts.append(_normalize(t))
                for table in page.extract_tables() or []:
                    if table:
                        parts.append("\n".join(" | ".join(c or "" for c in row) for row in table))
                if parts:
                    pages.append(Document(
                        page_content="\n\n".join(parts),
                        metadata={"source": str(file_path), "page": i + 1},
                    ))
        return pages

    print(f"   📄 Plain text → pymupdf4llm...")
    md = pymupdf4llm.to_markdown(str(file_path))
    if _has_spaced_text(md):
        print(f"   ⚠️  Encoding issue → vision...")
        return _extract_vision(file_path)
    return [Document(page_content=_normalize(md), metadata={"source": str(file_path)})]