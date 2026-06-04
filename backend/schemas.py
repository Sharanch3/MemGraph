from typing import List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from backend.base_model import model



class MemoryFact(BaseModel):
    key: str = Field(description="memory key in snake case")
    value: str = Field(description="memory value")


class MemoryFacts(BaseModel):
    facts: List[MemoryFact]



prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Extract structured memory facts from the user message.\n"
        "Return a list of key-value facts where keys are in snake_case."
    ),
    ("human", "{input}")
])


memory_extractor = prompt | model.with_structured_output(
    MemoryFacts  
)