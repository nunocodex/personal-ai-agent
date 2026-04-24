# 🤖 personal-ai-agent

> A local-first personal AI agent that classifies, indexes and queries
> your documents privately — zero cloud, zero API costs.

Built with **Ollama**, **ChromaDB**, and **LangChain**.
Runs entirely on consumer hardware with no internet connection required.

---

## ✨ Features

- 📄 **Document ingestion** — supports PDF, DOCX, MD, TXT, CSV, XLSX
- 🗂️ **Auto-classification** — automatically organizes documents by category
- 🔍 **Semantic search** — ask questions about your documents in natural language
- 🔒 **100% local** — your data never leaves your machine
- 🧩 **Extensible** — easily add new agents and document types

---

## 🏗️ Architecture

```
documents/inbox/  →  [Ingestor Agent]  →  ChromaDB (vector store)
                                                ↓
                          [Query Agent]  ←  your question
                                                ↓
                                          LLM (Ollama)  →  answer
```

---

## 🛠️ Stack

| Component      | Tool                  |
|----------------|-----------------------|
| LLM            | Qwen3 8B via Ollama   |
| Embeddings     | nomic-embed-text      |
| Vector DB      | ChromaDB              |
| Orchestration  | LangChain + Python    |

---

## ⚙️ Requirements

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- NVIDIA GPU with 8GB+ VRAM (recommended) or CPU-only (slower)
- 8GB+ RAM

---

## 🚀 Setup

See [docs/setup.md](docs/setup.md) for full installation instructions.

---

## 📁 Project Structure

```
personal-ai-agent/
├── agents/         # One file per agent
├── tools/          # Shared utilities (loaders, classifier)
├── core/           # Config and shared components
├── docs/           # Project documentation
├── main.py         # Entry point
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