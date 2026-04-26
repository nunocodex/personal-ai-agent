# Setup Guide

## Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/download) installed
- [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases) extracted (e.g. `C:\poppler-25.x\`)
- NVIDIA GPU with 8GB+ VRAM (recommended)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/NunoCodex/personal-ai-agent.git
cd personal-ai-agent
```

### 2. Create virtual environment

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
# Or use: .\start.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Pull Ollama models

```powershell
ollama pull qwen3:8b
ollama pull qwen3-vl:2b
ollama pull qwen3-embedding:0.6b
```

### 5. Configure environment

Copy `.env.example` to `.env` and set your Poppler path:

```
POPPLER_PATH=C:\poppler-25.x\Library\bin
```

### 6. Run

```powershell
# Drop documents in documents/inbox/ then:
python main.py ingest

# Ask questions:
python main.py query "What is my net salary for January 2024?"
```

## Upgrading Qdrant to Docker

Change one line in `core/qdrant_client.py`:

```python
# File-based (default)
client = QdrantClient(path=str(QDRANT_DIR))

# Docker
client = QdrantClient(host="localhost", port=6333)
```
