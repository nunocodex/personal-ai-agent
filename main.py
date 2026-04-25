import sys
from agents import ingestor, query


def print_help():
    print("""
personal-ai-agent — available commands:

  python main.py ingest          Process documents in inbox/
  python main.py query "<question>"  Ask a question about your documents
  python main.py help            Show this help message

Examples:
  python main.py query "What is my total income in 2023?"
  python main.py query "What technologies are listed in my CV?"
""")


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()

    if command == "ingest":
        print("🚀 Starting ingestion agent...\n")
        ingestor.run()

    elif command == "query":
        if len(sys.argv) < 3:
            print("❌ Please provide a question.")
            print('   Example: python main.py query "What is my total income?"')
            return
        question = sys.argv[2]
        print(f"🔍 Question: {question}\n")
        answer = query.run(question)
        print(f"💬 Answer:\n{answer}")

    elif command == "help":
        print_help()

    else:
        print(f"❌ Unknown command: '{command}'")
        print_help()


if __name__ == "__main__":
    main()