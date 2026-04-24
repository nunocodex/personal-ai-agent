import shutil
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter

from core.config import (
    INBOX_DIR,
    DOCUMENTS_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
)
from core.vectorstore import get_collection
from tools.loaders import load_document
from tools.classifier import extract_metadata, get_document_folder


def run():
    """
    Ingestion agent — processes all documents in the inbox folder.

    For each document:
      1. Loads the content
      2. Asks the LLM to extract all metadata (category, summary, entities, etc.)
      3. Splits the content into chunks
      4. Indexes chunks + metadata into ChromaDB
      5. Moves the file to the correct category folder (auto-created if needed)
    """
    collection = get_collection()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )

    files = [f for f in INBOX_DIR.iterdir() if f.is_file()]

    if not files:
        print("📭 No documents found in inbox.")
        return

    print(f"📥 Found {len(files)} document(s) to process.\n")

    for file_path in files:
        print(f"📄 Processing: {file_path.name}")

        # 1. Load document
        try:
            documents = load_document(file_path)
        except ValueError as e:
            print(f"   ⏭️  Skipped: {e}\n")
            continue
        except Exception as e:
            print(f"   ❌ Load error: {e}\n")
            continue

        # 2. Extract full text for metadata extraction
        full_text = " ".join([doc.page_content for doc in documents])

        if not full_text.strip():
            print(f"   ⚠️  Empty content, skipping.\n")
            continue

        # 3. Extract metadata via LLM
        print(f"   🤖 Extracting metadata...")
        try:
            metadata = extract_metadata(file_path, full_text)
        except Exception as e:
            print(f"   ❌ Metadata extraction error: {e}\n")
            continue

        category = metadata["category"]
        print(f"   📁 Category: {category}")
        print(f"   📝 Summary: {metadata.get('summary', 'N/A')}")
        print(f"   🏷️  Topics: {metadata.get('topics', 'N/A')}")

        # 4. Split into chunks and index into ChromaDB
        chunks = splitter.split_documents(documents)
        print(f"   ✂️  Split into {len(chunks)} chunk(s)")

        try:
            for i, chunk in enumerate(chunks):
                chunk_id = f"{file_path.stem}_{i}"
                chunk_metadata = {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
                collection.upsert(
                    ids=[chunk_id],
                    documents=[chunk.page_content],
                    metadatas=[chunk_metadata],
                )
        except Exception as e:
            print(f"   ❌ Indexing error: {e}\n")
            continue

        # 5. Move file to category folder (auto-created if needed)
        dest_folder = get_document_folder(DOCUMENTS_DIR, category)
        dest_path   = dest_folder / file_path.name

        # Handle duplicate filenames
        if dest_path.exists():
            stem   = file_path.stem
            suffix = file_path.suffix
            dest_path = dest_folder / f"{stem}_1{suffix}"

        shutil.move(str(file_path), str(dest_path))
        print(f"   ✅ Moved to: documents/{category}/\n")

    print("✨ Ingestion complete!")