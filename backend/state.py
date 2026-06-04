from langchain_core.messages import BaseMessage
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages



class ChatState(TypedDict):

    messages: Annotated[List[BaseMessage], add_messages]

    summary: str

    kept_messages: List[BaseMessage]

    user_id: str
