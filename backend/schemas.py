from typing import List
from pydantic import BaseModel, Field




class MemoryFact(BaseModel):

    key: str = Field(description= "memory key in snake case")
    value: str = Field(description= "memory value")




class MemoryFacts(BaseModel):

    facts: List[MemoryFact]