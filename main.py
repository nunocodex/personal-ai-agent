import sys
from agents import ingestor


def print_help():
    print("""
personal-ai-agent — available commands:

  python main.py ingest     Process documents in inbox/
  python main.py help       Show this help message
""")


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == "ingest":
        print("🚀 Starting ingestion agent...\n")
        ingestor.run()

    elif command == "help":
        print_help()

    else:
        print(f"❌ Unknown command: '{command}'")
        print_help()


if __name__ == "__main__":
    main()