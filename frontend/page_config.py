import streamlit as st



def page_config() ->None:

    st.set_page_config(
        page_title= "MemGraph",
        page_icon= "🤖",
        layout= "centered"
    )

    st.title("🤖 MemGraph")
    st.markdown("> **Your Stateful Agentic AI Assistant**")