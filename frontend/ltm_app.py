import uuid
import streamlit as st
from langchain_core.messages import (
    HumanMessage,
    AIMessage,
    ToolMessage,
)
from backend.ltm_graph import chatbot
from backend.db_helper import retrieve_all_threads
from backend.utils import (
    generate_thread_id,
    reset_chat,
    add_thread,
    load_conversation,
    display_name,
)


# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Stateful Chatbot",
    page_icon="🤖",
    layout="centered",
)


# ──────────────────────────────────────────────
# INITIALIZATION
# ──────────────────────────────────────────────

def initialize_user() -> None:
    """
    Create or restore a stable user identity.
    """

    if "user_id" in st.session_state:
        return

    if "uid" in st.query_params:
        user_id = st.query_params["uid"]
    else:
        user_id = str(uuid.uuid4())
        st.query_params["uid"] = user_id

    st.session_state["user_id"] = user_id


def initialize_session() -> None:
    """
    Initialize Streamlit session state.
    """

    st.session_state.setdefault(
        "chat_history",
        []
    )

    st.session_state.setdefault(
        "thread_id",
        generate_thread_id()
    )

    if "chat_threads" not in st.session_state:
        st.session_state["chat_threads"] = (
            retrieve_all_threads()
        )


# Run startup initialization

initialize_user()
initialize_session()

add_thread(
    st.session_state["thread_id"]
)


# ──────────────────────────────────────────────
# THREAD MANAGEMENT
# ──────────────────────────────────────────────

def switch_thread(thread_id: str) -> None:
    """
    Load a conversation into the UI.
    """

    st.session_state["thread_id"] = thread_id

    messages = load_conversation(thread_id)

    history = []

    for msg in messages:

        if isinstance(msg, HumanMessage):
            role = "user"

        elif isinstance(msg, AIMessage):
            role = "assistant"

        else:
            continue

        if not msg.content:
            continue

        history.append(
            {
                "role": role,
                "content": msg.content,
            }
        )

    st.session_state["chat_history"] = history


# ──────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────

def render_sidebar() -> None:

    st.sidebar.title("🤖 Stateful Bot")

    st.sidebar.caption(
        f"User: `{st.session_state['user_id'][:8]}...`"
    )

    if st.sidebar.button(
        "New Chat",
        icon="📝",
        type="primary",
        use_container_width=True,
    ):
        reset_chat()

    st.sidebar.divider()

    st.sidebar.subheader("Recent Chats")

    for thread_id in reversed(
        st.session_state["chat_threads"]
    ):

        label = display_name(thread_id)

        if thread_id == st.session_state["thread_id"]:
            label = f"▶ {label}"

        if st.sidebar.button(
            label,
            key=thread_id,
            use_container_width=True,
        ):
            switch_thread(thread_id)


# ──────────────────────────────────────────────
# CHAT HISTORY
# ──────────────────────────────────────────────

def render_chat_history() -> None:

    for message in st.session_state["chat_history"]:

        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )


# ──────────────────────────────────────────────
# CHATBOT STREAMING
# ──────────────────────────────────────────────

def stream_response(user_input: str):

    config = {
        "configurable": {
            "thread_id": st.session_state["thread_id"],
            "user_id": st.session_state["user_id"],
        }
    }

    status_box = None

    for chunk, metadata in chatbot.stream(
        {
            "messages": [
                HumanMessage(
                    content=user_input
                )
            ],
            "user_id": st.session_state["user_id"],
        },
        config=config,
        stream_mode="messages",
    ):

        if isinstance(chunk, ToolMessage):

            tool_name = getattr(
                chunk,
                "name",
                "tool"
            )

            if status_box is None:

                status_box = st.status(
                    f"🔧 Using '{tool_name}'...",
                    expanded=True,
                )

            else:

                status_box.update(
                    label=f"🔧 Using '{tool_name}'...",
                    state="running",
                )

        if (
            isinstance(chunk, AIMessage)
            and chunk.content
        ):
            yield chunk.content

    if status_box is not None:

        status_box.update(
            label="✅ Tool Finished",
            state="complete",
            expanded=False,
        )


# ──────────────────────────────────────────────
# MAIN UI
# ──────────────────────────────────────────────

render_sidebar()

render_chat_history()

user_input = st.chat_input(
    "Ask me anything..."
)

if user_input:

    # Display user message

    st.session_state["chat_history"].append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):
        st.write(user_input)

    # Stream assistant response

    with st.chat_message("assistant"):

        assistant_response = st.write_stream(
            stream_response(user_input)
        )

    # Save assistant response

    st.session_state["chat_history"].append(
        {
            "role": "assistant",
            "content": assistant_response,
        }
    )