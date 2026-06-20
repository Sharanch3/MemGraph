import streamlit as st
from backend.graph import chatbot
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage


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