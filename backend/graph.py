import os
from typing import Final
from backend.state import ChatState
from backend.tools import tool_node
from langgraph.prebuilt import tools_condition
from langgraph.store.postgres import PostgresStore
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from backend.nodes import (
    summary_node,
    cleanup_node,
    chat_node,
    memory_write_node,
    should_summarize

)




#CONNECTION STRING
DB_URI: Final[str] = os.getenv("DATABASE_URI")



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
        "__end__" : "memory_write"
    }

)
graph.add_edge("tools", "chat")
graph.add_edge("memory_write", END)


#Checkpointer -> Stores graph state associated with thread_id, each thread has separate checkpoints.
checkpointer_cm = PostgresSaver.from_conn_string(conn_string= DB_URI)

checkpointer = checkpointer_cm.__enter__()
checkpointer.setup()


#Store -> Stores long-term memories associated with user_id, shared across all chat sessions.
store_cm = PostgresStore.from_conn_string(conn_string= DB_URI)

store = store_cm.__enter__()
store.setup()


chatbot = graph.compile(
    checkpointer= checkpointer,
    store= store
)

