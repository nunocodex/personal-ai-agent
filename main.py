import sys
from core.config import INBOX_DIR


def print_help():
    print("""
personal-ai-agent — commands:

  python main.py ingest                    Process documents in inbox/
  python main.py query "<question>"        Ask a question about your documents
  python main.py remember "<instruction>"  Save or extract personal memory
  python main.py memory                    Show current memory
  python main.py help                      Show this help
""")


def run_ingest():
    from crews.ingestor_crew import run as ingest_run
    files = [f for f in INBOX_DIR.iterdir() if f.is_file()]
    if not files:
        print("📭 No documents found in inbox.")
        return
    print(f"📥 Found {len(files)} document(s) to process.\n")
    for file_path in files:
        print(f"📄 Processing: {file_path.name}")
        try:
            ingest_run(str(file_path).replace("\\", "/"))
        except Exception as e:
            print(f"❌ Failed: {file_path.name} — {e}")
    print("\n✨ Ingestion complete!")


def run_query(question: str):
    from crews.query_crew import run as query_run
    from crews.memory_crew import get_memory_context
    memory_context = get_memory_context()
    print(f"🔍 Question: {question}\n")
    result = query_run(question, memory_context)
    print(f"\n💬 Answer:\n{result}")


def run_remember(instruction: str):
    from crews.memory_crew import run as memory_run
    print(f"🧠 Memory instruction: {instruction}\n")
    result = memory_run(instruction)
    print(f"\n✅ Done:\n{result}")


def show_memory():
    from crews.memory_crew import _load_memory
    memory = _load_memory()
    if not memory["notes"] and not memory.get("extracted"):
        print("🧠 Memory is empty.")
        return
    print("🧠 Current memory:\n")
    for note in memory["notes"]:
        print(f"  [{note['key']}] {note['value']}")
    for k, v in memory.get("extracted", {}).items():
        print(f"  [extracted:{k}] {v}")


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == "ingest":
        run_ingest()
    elif command == "query":
        if len(sys.argv) < 3:
            print('❌ Provide a question: python main.py query "your question"')
            return
        run_query(sys.argv[2])
    elif command == "remember":
        if len(sys.argv) < 3:
            print('❌ Provide an instruction: python main.py remember "I am a PHP developer"')
            return
        run_remember(sys.argv[2])
    elif command == "memory":
        show_memory()
    elif command == "help":
        print_help()
    else:
        print(f"❌ Unknown command: '{command}'")
        print_help()


if __name__ == "__main__":
    main()