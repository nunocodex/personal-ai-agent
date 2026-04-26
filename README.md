# 🤖 personal-ai-agent

> A local-first personal AI agent that classifies, indexes and queries
> your documents privately — zero cloud, zero API costs.

Built with **CrewAI**, **Qdrant**, and **Ollama**.
Runs entirely on consumer hardware. Your data never leaves your machine.

---

## ✨ Features

- 📄 **Document ingestion** — PDF (including scanned/complex layouts), DOCX, MD, TXT, CSV
- 👁️ **Vision extraction** — reads complex PDFs (payslips, invoices) using local vision model
- 🗂️ **Auto-classification** — LLM assigns category freely, no hardcoded mapping
- 🔍 **Semantic search** — ask questions in natural language, get answers with sources
- 🔒 **100% local** — Ollama + Qdrant, no internet required after setup
- 🧩 **Extensible** — add new agents, document types, and categories easily

---

## 🏗️ Architecture

```
documents/inbox/
      ↓
[Ingestor Crew]
  load → classify → index → move
      ↓
[Qdrant Vector DB]
      ↓
[Query Crew]
  search → answer
      ↓
  your answer (with sources)
```

---

## 🛠️ Stack

| Component       | Tool                           |
| --------------- | ------------------------------ |
| Agent framework | CrewAI                         |
| LLM             | Qwen3 8B via Ollama            |
| Vision model    | Qwen3-VL 2B via Ollama         |
| Embeddings      | Qwen3-Embedding 0.6B           |
| Vector DB       | Qdrant (file-based, local)     |
| PDF extraction  | PDFMiner + pdfplumber + vision |

---

## ⚙️ Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- NVIDIA GPU with 8GB+ VRAM (recommended)
- [Poppler](https://github.com/oschwartz10612/poppler-windows/releases) for Windows PDF rendering

---

## 🚀 Setup

See [docs/setup.md](docs/setup.md) for full installation instructions.

---

## 📁 Project Structure

```
personal-ai-agent/
├── crews/              # CrewAI agents
│   ├── ingestor_crew.py
│   └── query_crew.py
├── tools/              # Shared utilities
│   ├── pdf_loader.py
│   ├── doc_classifier.py
│   └── qdrant_tool.py
├── core/               # Config and shared components
│   ├── config.py
│   └── qdrant_client.py
├── documents/          # Your documents (gitignored)
│   └── inbox/          # Drop documents here to process
├── data/               # Qdrant database (gitignored)
├── main.py             # Entry point
└── requirements.txt
```

---

## 🗺️ Roadmap

See [docs/roadmap.md](docs/roadmap.md)

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 License

MIT License — see [LICENSE](LICENSE)

---

## 👤 Author

**NunoCodex** — Senior PHP Developer transitioning to AI engineering.

[GitHub](https://github.com/NunoCodex)
