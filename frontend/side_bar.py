import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from frontend.utils import (
    reset_chat,
    load_conversation,
    display_name
    
)



def render_sidebar():

    with st.sidebar:

        st.caption(
            f"USER: `{st.session_state["user_id"][:5]}...`"
        )

        if st.button(label= "**`➕` New Chat**", use_container_width= True, type= "secondary", width= "stretch"):
            reset_chat()

        st.divider()



        st.markdown("**`💬` Recents**") 
        for thread_id in st.session_state["chat_threads"][::-1]:

            name_thread = display_name(thread_id= thread_id)
            
            if st.button(label= name_thread, key = thread_id, use_container_width= True, type= "primary" if st.session_state["thread_id"] == thread_id else "secondary"):

                #update the thread_id -> current chat
                st.session_state["thread_id"] = thread_id

                messages = load_conversation(thread_id= thread_id)

                temp_message = []

                for msg in messages:

                    if isinstance(msg, HumanMessage):
                        role = "user"

                    elif isinstance(msg, AIMessage):
                        role = "assistant"
                    
                    #Skip empty AI messages
                    elif not msg.content:
                         continue
                    
                    else:
                        continue 

                    temp_message.append({"role": role, "content": msg.content})
                    
                    
                    
                st.session_state["chat_history"] = temp_message
                
                st.rerun()







                
        
        
        