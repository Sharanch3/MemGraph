import uuid
import streamlit as st
from typing import List
from backend.graph import chatbot, checkpointer
from backend.base_model import base_model
from langchain_core.messages import HumanMessage, BaseMessage




def generate_thread_id() ->str:
    """Generate a unique thread ID"""

    thread_id = str(uuid.uuid4())

    return thread_id




def reset_chat() ->None:
    """
    Reset the current chat and create a new thread & add 
    it to the chat-threads
    
    """

    thread_id = generate_thread_id()

    st.session_state["thread_id"] = thread_id

    add_threads(thread_id= thread_id)

    st.session_state["chat_history"] = []




def add_threads(thread_id: str) ->None:
    "Add the current thread_id to the chat-threads"

    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)





def load_conversation(thread_id: str) ->List[BaseMessage]:
    """Load conversation history from a specific thread"""

    
    state = chatbot.get_state(
        config= {'configurable': {'thread_id': thread_id}}
    )

    return state.values.get("messages", [])




def display_name(thread_id) ->str:
    """
    Get a display name for a thread based on the first 
    human message.
    
    """

    messages = load_conversation(thread_id)

    # Find the first human message
    for msg in messages:
        is_human = isinstance(msg, HumanMessage)

        if is_human and msg.content:
            content = msg.content.strip()
            # Get first 20 characters and add ellipsis
            if len(content) > 10:
                 return content[:20] + "..."
            else:
                return content
     
    #Fallback if no human message found
    return "New Session"




#FOR STM
def retrieve_all_threads() ->List[str]:
    
    all_threads = set()

    for checkpoint in checkpointer.list(config = None):
        all_threads.add(checkpoint.config['configurable']['thread_id'])

    
    return list(all_threads)