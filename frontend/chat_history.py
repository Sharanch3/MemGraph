import streamlit as st


def render_chat_history() ->None:

    for message in st.session_state["chat_history"]:

        with st.chat_message(message["role"]):
            
            st.markdown(message["content"])

