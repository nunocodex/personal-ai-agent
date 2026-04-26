# Architecture

## Overview

personal-ai-agent uses a CrewAI multi-agent architecture with local LLMs via Ollama and Qdrant as vector store.

## Ingestion Pipeline

```
inbox/ → load_pdf() → classify() → index_chunks() → move()
```

### PDF Loader strategies (in priority order)

| Condition                | Strategy                       |
| ------------------------ | ------------------------------ |
| Scanned PDF              | Vision model (3-section split) |
| Tables + encoding issues | Vision model (3-section split) |
| Tables (clean)           | pdfplumber                     |
| Plain text               | pymupdf4llm                    |

The 3-section split (top/middle/bottom) is used because `qwen3-vl:2b` has image size limits that prevent processing a full page at once.

### Classification

The LLM classifies documents freely — no hardcoded categories. A document about healthcare gets `health`, a payslip gets `finance`. New categories create new folders automatically.

### Chunking

Each vision-extracted page is stored as a single chunk (no splitting) to preserve label-value relationships. Text-based documents use `RecursiveCharacterTextSplitter` with category-aware chunk sizes.

## Query Pipeline

```
question → embed → Qdrant search → LLM answer with sources
```

## Models

| Role          | Model                | VRAM            |
| ------------- | -------------------- | --------------- |
| LLM reasoning | qwen3:8b             | ~5GB (100% GPU) |
| Vision OCR    | qwen3-vl:2b          | ~2GB (100% GPU) |
| Embeddings    | qwen3-embedding:0.6b | minimal         |
