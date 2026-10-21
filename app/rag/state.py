from typing import List,Literal,Optional
from typing_extensions import TypedDict
from pydantic import BaseModel,Field
from langchain_core.documents import Document

class RouteDecision(BaseModel):
    """The llm will decide and route between kb and direct"""
    route : Literal["kb","direct"] = Field(description="use knoweldge for questions which require else use direct for greetings and conversation")
class EvidanceGrade(BaseModel):
    """LLm will check the retrived docs is enough to answer the question or not ,if it is not sufficient gives weak else good"""
    grade : Literal["good","weak"] = Field(description="Based on the retrieved docs llm will grade weak or good")
class Agentstate(TypedDict,total=False):
    question: str 
    current_question:str 
    kb_docs:list[Document]
    web_results:str 
    kb_grade : str
    web_grade: str
    answer:str
    source_used:str
    retry_count:int
    trace :list[str]
    citations : list[str]
    