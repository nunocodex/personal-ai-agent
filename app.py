import streamlit as st
from pathlib import Path

# ─── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Personal AI Agent",
    page_icon="🤖",
    layout="wide",
)

# ─── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.title("🤖 Personal AI Agent")
    st.markdown("---")

    # Inbox status
    inbox = Path("documents/inbox")
    inbox_files = list(inbox.iterdir()) if inbox.exists() else []
    st.metric("📥 Inbox", f"{len(inbox_files)} files")

    # Memory status
    memory_file = Path("data/personal_memory.json")
    if memory_file.exists():
        import json
        memory = json.loads(memory_file.read_text(encoding="utf-8"))
        st.metric("🧠 Memory notes", len(memory.get("notes", [])))
    else:
        st.metric("🧠 Memory notes", 0)

    # Qdrant status
    try:
        from core.config import QDRANT_DIR
        db_size = sum(f.stat().st_size for f in QDRANT_DIR.rglob("*") if f.is_file())
        st.metric("📚 DB size", f"{db_size // 1024} KB")
    except Exception:
        st.metric("📚 DB size", "N/A")

    st.markdown("---")

    # Ingest button
    st.subheader("📥 Ingest Documents")
    if inbox_files:
        st.write(f"Files in inbox:")
        for f in inbox_files:
            st.write(f"  • {f.name}")
        if st.button("🚀 Process Inbox", use_container_width=True):
            with st.spinner("Processing documents..."):
                from crews.ingestor_crew import run as ingest_run
                for file_path in inbox_files:
                    try:
                        ingest_run(str(file_path).replace("\\", "/"))
                        st.success(f"✅ {file_path.name}")
                    except Exception as e:
                        st.error(f"❌ {file_path.name}: {e}")
            st.rerun()
    else:
        st.info("Inbox is empty.\nDrop files in documents/inbox/")

    st.markdown("---")

    # Memory section
    st.subheader("🧠 Save Memory")
    memory_input = st.text_area("What should I remember?", placeholder="Sono un senior PHP developer...")
    if st.button("💾 Save", use_container_width=True):
        if memory_input:
            with st.spinner("Saving..."):
                from crews.memory_crew import run as memory_run
                memory_run(memory_input)
            st.success("Saved!")
            st.rerun()

# ─── MAIN CHAT ────────────────────────────────────────────────
st.title("💬 Ask your documents")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask anything about your documents..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get answer
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                from crews.query_crew import run as query_run
                from crews.memory_crew import get_memory_context
                memory_context = get_memory_context()
                answer = query_run(prompt, memory_context)
                # Clean up CrewAI output artifacts
                if hasattr(answer, '__str__'):
                    answer = str(answer)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                error_msg = f"❌ Error: {e}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Clear chat button
if st.session_state.messages:
    if st.button("🗑️ Clear chat"):
        st.session_state.messages = []
        st.rerun()