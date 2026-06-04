import os
from backend.base_model import model
from backend.state import ChatState
from langgraph.graph import StateGraph, START, END
from backend.tools import model_with_tools, tools
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore
from langchain_core.messages import SystemMessage, HumanMessage,RemoveMessage
from langchain_core.messages.utils import trim_messages, count_tokens_approximately
from backend.schemas import memory_extractor
from backend.db_helper import _namespace, load_memories
from langgraph.store.postgres import PostgresStore
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
        [HumanMessage(content= prompt)]
    )


    return {
        "summary": response.content,
        "kept_messages": kept

    }



def cleanup_node(state: ChatState):
    """
    Remove messages that were just summarized, keeping 
    only what fits the budget.
    
    """

    messages = state["messages"]

    kept = state["kept_messages"]

    if len(messages) == len(kept):

        return {}
    
    messages_to_remove = [
        RemoveMessage(id= msg.id)
        for msg in messages[: len(messages) - len(kept)]
    ]

    return {"messages": messages_to_remove}



def memory_write_node(state: ChatState, config: RunnableConfig, *, store: BaseStore):

    recent = trim_messages(
        messages=state["messages"],
        max_tokens=1000,
        token_counter=count_tokens_approximately,
        strategy="last"
    )

    conversation = "\n".join(
        f"{m.type}: {m.content}"
        for m in recent
        if isinstance(m, HumanMessage)
    )

    facts = memory_extractor.invoke(
        [HumanMessage(
            content=f"""
             Extract durable user facts worth remembering across future conversations.

            Store only:
            - Name
            - Profession
            - Goals
            - Projects
            - Interests
            - Preferences

            Ignore temporary requests and one-time tasks.

            Conversation:
            {conversation}
            """
        )]
    )

    ns = _namespace(state["user_id"])

    for fact in facts.facts:
        if not fact.key or not fact.value:
            continue

        existing = store.get(ns, fact.key)

        # existing.value is a dict like {"value": "..."}
        existing_val = existing.value.get("value") if existing else None

        if existing_val != fact.value:
            store.put(
                namespace=ns,
                key=fact.key,
                value={"value": fact.value}   # ✅ must be a dict
            )

    return {}



def chat_node(state: ChatState, config: RunnableConfig, * , store: BaseStore):
    """
    Build the prompt from:
    - System instructions
    - Long-term memory
    - Conversation summary
    - Recent messages

    Then invoke the model and append the response.
    """

    messages = state["messages"]

    summary = state.get("summary", "")

    user_id = state["user_id"]

    recent_messages = trim_messages(
        messages=messages,
        max_tokens=RECENT_MESSAGE_TOKENS,
        token_counter=count_tokens_approximately,
        strategy="last",
    )

    prompt = [
        SystemMessage(
            content=(
                "You are a helpful assistant. "
                "Answer clearly and concisely."
            )
        )
    ]

    # Inject long-term memory
    memory_context = load_memories(store, user_id)

    if memory_context:
        prompt.append(
            SystemMessage(content=memory_context)
        )

    # Inject conversation summary
    if summary:
        prompt.append(
            SystemMessage(
                content=f"Conversation Summary:\n\n{summary}"
            )
        )

    # Inject recent conversation
    prompt.extend(recent_messages)

    response = model_with_tools.invoke(prompt)

    return {
        "messages": [response]
    }



tool_node = ToolNode(tools= tools)




#GRAPH
graph = StateGraph(state_schema= ChatState)

graph.add_node("summary", summary_node)
graph.add_node("cleanup", cleanup_node)
graph.add_node("chat", chat_node)
graph.add_node("tools", tool_node)
graph.add_node("memory_write", memory_write_node)

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
graph.add_conditional_edges(
    "chat",
    tools_condition,
    {
        "tools": "tools",
        "__end__": "memory_write"
    }
)
graph.add_edge("tools", "chat")
graph.add_edge("memory_write", END)


# Checkpointer
checkpointer_cm = PostgresSaver.from_conn_string(DB_URI)

checkpointer = checkpointer_cm.__enter__()
checkpointer.setup()


# Long-term memory Store
store_cm = PostgresStore.from_conn_string(DB_URI)

store = store_cm.__enter__()
store.setup()


# Compile graph
chatbot = graph.compile(
    checkpointer=checkpointer,
    store=store
)



if __name__ == "__main__":
    with open("graph.png", "wb") as f:
        f.write(chatbot.get_graph().draw_png())
    print("graph.png saved.")