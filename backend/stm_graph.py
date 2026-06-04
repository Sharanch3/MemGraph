import os
from backend.base_model import model
from backend.state import ChatState
from langgraph.graph import StateGraph, START
from backend.tools import model_with_tools, tools
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage,RemoveMessage
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from dotenv import load_dotenv
load_dotenv()



#Connection string
DB_URI = os.getenv("DATABASE_URI")

#Threshold that triggers summarization
MAX_HISTORY_TOKEN = 6000

#Token budget passed to the LLM in chat_node
RECENT_MESSAGE_TOKENS = 2000



#Router Function
def should_summarize(state: ChatState):
    """ 
    Routes to summarization when the conversation exceeds the token limit; otherwise continues normal chat flow.
    
    """

    messages = state["messages"]

    kept = trim_messages(
        messages= messages,
        max_tokens= MAX_HISTORY_TOKEN,
        token_counter= count_tokens_approximately,
        strategy= "last"

    )

    return "summarize" if len(kept) < len(messages) else "chat"



#NODES
def summary_node(state: ChatState):
    """ 
    Summarizes trimmed conversation history or updates 
    the running summary if it exists.
    
    """

    messages = state["messages"]

    existing_summary = state.get("summary", "")

    kept = trim_messages(
        messages= messages,
        max_tokens= MAX_HISTORY_TOKEN,
        token_counter= count_tokens_approximately,
        strategy= "last"
    )

    old_messages = messages[: len(messages) - len(kept)]

    if not old_messages:
        
        return {}

    conversation = "\n".join(
        f"{msg.type}: {msg.content}"
        for msg in old_messages if hasattr(msg, "content")
    )

    prompt = f"""
                Current Summary:

                {existing_summary}

                Extend the summary using the conversation below.

                Conversation:

                {conversation}

                Return only the updated summary.
            """
    
    response = model.invoke(
        HumanMessage(content= prompt)
    )


    return {"summary": response.content}



def cleanup_node(state: ChatState):
    """
    Remove messages that were just summarized, keeping 
    only what fits the budget.
    
    """

    messages = state["messages"]

    kept = trim_messages(
        messages= messages,
        max_tokens= MAX_HISTORY_TOKEN,
        token_counter= count_tokens_approximately,
        strategy= "last"
    ) 

    if len(messages) == len(kept):

        return {}
    
    messages_to_remove = [
        RemoveMessage(id= msg.id)
        for msg in messages[: len(messages) - len(kept)]
    ]

    return {"messages": messages_to_remove}



def chat_node(state: ChatState):
    """
    Build the model prompt from the conversation summary and recent
    message history, invoke the LLM, and append the response to state.
    
    """

    messages = state["messages"]

    summary = state.get("summary", "")

    recent_messages = trim_messages(
        messages= messages,
        max_tokens= RECENT_MESSAGE_TOKENS,
        token_counter= count_tokens_approximately,
        strategy= "last"
    )

    prompt = [
        SystemMessage(
            content = "You are a helpful assistant. Answer clearly and concisely. When a conversation summary is provided, use it as background context."
        )
    ]

    if summary:
        #inject summary memory
        prompt.append(SystemMessage(content= f"Consersation summary-\n\n{summary}"))


    prompt.extend(recent_messages)

    response = model_with_tools.invoke(prompt)

    return {"messages": [response]}



tool_node = ToolNode(tools= tools)



#GRAPH
graph = StateGraph(state_schema= ChatState)

graph.add_node("summary", summary_node)
graph.add_node("cleanup", cleanup_node)
graph.add_node("chat", chat_node)
graph.add_node("tools", tool_node)

graph.add_conditional_edges(
    START,
    should_summarize,
    {
        "summarize": "summary",
        "chat": "chat"
    }

)
graph.add_edge("summary", "cleanup")
graph.add_edge("cleanup", "chat")
graph.add_conditional_edges("chat", tools_condition)
graph.add_edge("tools", "chat")

checkpointer_cm = PostgresSaver.from_conn_string(conn_string= DB_URI)

checkpointer = checkpointer_cm.__enter__()
checkpointer.setup()

chatbot = graph.compile(checkpointer= checkpointer)



if __name__ == "__main__":
    with open("graph.png", "wb") as f:
        f.write(chatbot.get_graph().draw_png())
    print("graph.png saved.")