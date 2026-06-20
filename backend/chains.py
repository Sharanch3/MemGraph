from backend.schemas import MemoryFacts
from backend.base_model import base_model
from langchain_core.prompts import ChatPromptTemplate




prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Extract structured memory facts from the user message.\n"
        "Return a list of key-value facts where keys are in snake_case."
    ),
    ("human", "{input}")
])


memory_extractor = prompt | base_model.with_structured_output(schema= MemoryFacts)
