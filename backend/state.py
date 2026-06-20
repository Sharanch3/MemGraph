from typing import Annotated, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages




class ChatState(TypedDict):

    user_id: str

    messages: Annotated[List[BaseMessage], add_messages]

    summary: str | None

    kept_messages: List[BaseMessage]



