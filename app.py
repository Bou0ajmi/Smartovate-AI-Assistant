import streamlit as st
import traceback

from src.agent.get_agent import get_agent
from src.memory.thread_store import create_thread, get_thread, list_threads, get_messages, append_message, touch_thread

st.set_page_config(page_title="Smartovate Assistant", page_icon="🤖")

agent = get_agent()

# ---------------------------------------------------------------------------
# Fixed user identity for local testing (replace with real auth later)
# ---------------------------------------------------------------------------
USER_ID = "Test_User"
# ---------------------------------------------------------------------------
# Session state for current thread + history
# ---------------------------------------------------------------------------
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "history" not in st.session_state:
    st.session_state.history = []

if "pending_input" not in st.session_state:
    st.session_state.pending_input = None

# ---------------------------------------------------------------------------
# Sidebar: new chat, thread list
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header(f"👤 {USER_ID}")
    st.divider()

    if st.button("🆕 New conversation", use_container_width=True):
        st.session_state.thread_id = None
        st.session_state.history = []
        st.session_state.pending_input = None
        st.rerun()

    st.divider()
    st.subheader("Your conversations")

    threads = list_threads(USER_ID)
    if not threads:
        st.caption("No conversations yet.")
    else:
        for t in threads:
            label = t.get("title", "Untitled")[:40]
            is_active = t["thread_id"] == st.session_state.thread_id
            button_label = f"➡️ {label}" if is_active else label
            if st.button(button_label, key=f"thread_{t['thread_id']}", use_container_width=True):
                st.session_state.thread_id = t["thread_id"]
                st.session_state.history = get_messages(USER_ID, t["thread_id"])
                st.session_state.pending_input = None
                st.rerun()

# ---------------------------------------------------------------------------
# Main area: logo, title, chat
# ---------------------------------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("images/logo.png", width=200)

st.title("💬 Smartovate Assistant")
st.caption("Ask me anything about Smartovate — our services, Subul, leadership, partnerships, and more.")

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

SUGGESTED_QUESTIONS = [
    "What does Smartovate do?",
    "Tell me about Subul",
    "What internship opportunities does Smartovate offer?",
    "Who leads Smartovate?",
    "What certifications does Smartovate have?",
    "What partnerships has Smartovate built?",
]

if not st.session_state.history:
    st.markdown("**Try asking:**")
    cols = st.columns(2)
    for i, question in enumerate(SUGGESTED_QUESTIONS):
        with cols[i % 2]:
            if st.button(question, key=f"suggestion_{i}", use_container_width=True):
                st.session_state.pending_input = question
                st.rerun()

# ---------------------------------------------------------------------------
# Handle new input
# ---------------------------------------------------------------------------
user_input = st.chat_input("Ask me something...")

if st.session_state.pending_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None

if user_input:
    try:
        if not st.session_state.thread_id:
            st.session_state.thread_id = create_thread(USER_ID, title=user_input[:50])
        else:
            thread = get_thread(USER_ID, st.session_state.thread_id)
            if thread is None:
                st.error("This conversation could not be found.")
                st.stop()
    except Exception as e:
        traceback.print_exc()
        st.error(f"⚠️ Could not resolve conversation: {e}")
        st.stop()

    st.session_state.history.append({"role": "user", "content": user_input})
    append_message(USER_ID, st.session_state.thread_id, "user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("Thinking...")
        response = ""
        try:
            for chunk in agent.stream(user_input, thread_id=st.session_state.thread_id):
                response += chunk
                placeholder.markdown(response + "▌")
            placeholder.markdown(response)
        except Exception as e:
            traceback.print_exc()
            response = f"⚠️ Something went wrong: {e}"
            placeholder.markdown(response)

    st.session_state.history.append({"role": "assistant", "content": response})
    append_message(USER_ID, st.session_state.thread_id, "assistant", response)

    st.rerun()