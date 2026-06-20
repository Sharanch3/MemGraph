import uuid
import streamlit as st
from frontend.utils import generate_thread_id, add_threads, retrieve_all_threads


def initialize_session_state():
    

    if "user_id" not in st.session_state:

        if "uid" in st.query_params:
            user_id = st.query_params["uid"]
        
        else:
            user_id = str(uuid.uuid4())
            st.query_params["uid"] = user_id
        
        st.session_state["user_id"] = user_id



    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    

    if "chat_threads" not in st.session_state:
        st.session_state["chat_threads"] = retrieve_all_threads()

    

    if "thread_id" not in st.session_state:
        
        thread_id = generate_thread_id()

        st.session_state["thread_id"] = thread_id

        add_threads(thread_id= thread_id)
    

    


