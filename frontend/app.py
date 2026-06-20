import streamlit as st
from frontend.stream import stream_response
from frontend.page_config import page_config
from frontend.side_bar import render_sidebar
from frontend.chat_history import render_chat_history
from frontend.session_state import initialize_session_state



def main():
    
    page_config()

    initialize_session_state()
    
    render_sidebar()
    
    render_chat_history()

    

    user_input = st.chat_input("Ask me anything...")

    if user_input:

        #Display User Input
        with st.chat_message("user"):
            st.write(user_input)
        
        #Persist Human Input
        st.session_state["chat_history"].append({
            "role": "user",
            "content": user_input
        })    
        
        #Display AI Response
        with st.chat_message("assistant"):
            ai_response = st.write_stream(
            stream_response(user_input)
        )


        #Persist AI Response
        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": ai_response
        })

        



if __name__ == "__main__":
    main()

