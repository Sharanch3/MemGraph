import streamlit as st
from backend.stm_graph import chatbot
from backend.db_helper import retrieve_all_threads
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from backend.utils import (
    generate_thread_id,
    reset_chat,
    add_thread,
    load_conversation,
    display_name
)



#PAGE CONFIG
st.set_page_config(
    page_title= "Stateful Chatbot",
    page_icon="🤖",
    layout= "centered"
)


#TO PERSIST IN SESSION STATE
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = retrieve_all_threads()

add_thread(st.session_state["thread_id"])




#SIDEBAR UI
st.sidebar.title(body= "🤖 Stateful-bot", width= "content", text_alignment= "center")
st.write(" ")

if st.sidebar.button(label= "New Chat", type= "primary", icon= "📝", icon_position= "right", use_container_width= False, width= "stretch"):
    reset_chat()

st.sidebar.divider()
st.sidebar.subheader(body= "Recents", width= "stretch", text_alignment= "justify")

#load chat-threads
for thread_id in st.session_state["chat_threads"][::-1]:

    name_thread = display_name(thread_id= thread_id)

    #highlight active thread
    if thread_id == st.session_state["thread_id"]:
        label = f"▶ {name_thread}"   
    else:
        label = name_thread    
    
    if st.sidebar.button(label= name_thread, key= thread_id, use_container_width= True):

        st.session_state["thread_id"] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = "user"
            
            elif isinstance(msg, AIMessage):
                role = "assistant"
            
            else:
                continue

            #Also skip empty AI messages
            if not msg.content:
                continue
            
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state["chat_history"] = temp_messages
            


#LOAD CHAT-HISTORY
for message in st.session_state["chat_history"]:
    with st.chat_message(message['role']):
        st.markdown(message['content'])



#MAIN UI
CONFIG = {"configurable": {"thread_id": st.session_state["thread_id"]}}
user_input = st.chat_input(placeholder="Ask me anything...")

if user_input:

    #USER's MESSAGE
    st.session_state["chat_history"].append({"role":'user', "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    

    #ASSISTANT's MESSAGE
    with st.chat_message("assistant"):
        status_holder = {"box": None}

        def ai_only_stream():
            
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config= CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")

                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using '{tool_name}' ...", expanded= True
                        )

                    else:
                        status_holder["box"].update(
                            label = f"🔧 Using '{tool_name}' ...", state= "running", expanded= True
                        )

                if isinstance(message_chunk, AIMessage) and message_chunk.content:

                    yield message_chunk.content
        
        ai_message = st.write_stream(ai_only_stream())

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label = "✅ Tool Finished", state = "complete", expanded = False
            )

    
    st.session_state["chat_history"].append({"role": 'assistant', "content": ai_message})