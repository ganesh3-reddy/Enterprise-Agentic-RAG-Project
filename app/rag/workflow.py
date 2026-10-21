from app.rag.vectorstore import get_retriever
from app.rag.state import Agentstate,RouteDecision,EvidanceGrade
from app.core.config import get_settings
import logging
import time
from typing import Literal
from langchain_groq import ChatGroq
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph,START,END
import os

logger = logging.getLogger(__name__)
settings = get_settings()
retriever = get_retriever()
_llm = None
_websearch = None

def llm():
    global _llm
    if _llm is None:
        if not settings.groq_api_key:
            raise ValueError("Groq API key is not provided")
        _llm = ChatGroq(api_key=settings.groq_api_key,model=settings.groq_model,temperature=0.2)
    return _llm

def websearch():
    global _websearch
    if _websearch is None:
        if not settings.tavily_api_key:
            raise ValueError("Tavily API key is not provided")
        os.environ["TAVILY_API_KEY"] = settings.tavily_api_key
        _websearch = TavilySearch(api_key=settings.tavily_api_key,max_results=5,topic="general",include_raw_content=False,include_answers=True,include_snippets=True)
    return _websearch
llm=llm()
websearch=websearch()
llm_router = llm.with_structured_output(RouteDecision,method="json_mode")
def route_decission(state :Agentstate):
    """Routes the decision based on the user query"""
    question = state["question"]
    decision = llm_router.invoke(f"""
You are a query routing assistant.

Your task is to classify the user's question into
exactly one of two categories:

1. kb:
   - Questions requiring knowledge base retrieval.
   - Questions about AI, RAG, Agentic RAG, and
     information stored in enterprise documents.

2. direct:
   - Greetings.
   - General conversations.
   - Questions that do not require knowledge retrieval.

IMPORTANT:
- The route value MUST be either "kb" or "direct".
- Never return "retrive_kb" or "direct_answer".
- Return only a valid JSON object.
- Do not include markdown or explanations.

Valid output examples:

{{"route": "kb"}}

{{"route": "direct"}}

User question:
{question}
""")
    print("The decision is ",decision.route)
    return {"current_question":question,
            "source_used":decision.route}

def route_after_decision(state:Agentstate):
    """Route the pipeline based on the decision"""
    source=state["source_used"]
    print("Routing based on the input....")
    if source == "kb":
        return "retrive_kb"
    else:
        return "direct_answer"

def fallback_llm(state:Agentstate):
    """LLM will give the direct answer for the question"""
    question = state["current_question"]
    response = llm.invoke(f"""
You are a helpful assistant!
Give response for the particular user question in a polite and professional way
Don't give the more text to the user just try to give in single line!
Question:
{question}
""")
    print("Generating answer to the question directly")
    return {"answer":response.text}

def retrive_docs(state:Agentstate):
    """"Retrieve the revelavent info based on the question"""
    question = state["current_question"]
    kb_docs = retriever.invoke(question)
    print("Retrieved the docs from the KB....")
    return {"kb_docs":kb_docs}
llm_with_grade =llm.with_structured_output(EvidanceGrade,method="json_mode")
def llm_grade_source(state:Agentstate):
    """LLM will grade the source"""
    question = state["current_question"]
    kb_docs = state["kb_docs"]
    result=llm_with_grade.invoke(f"""
You are the evaluator and need to evaluate the source
based on the retrieved docs is enough to answer the question
Analyze the retrieved docs and decide whether
        to retrieve information is sufficient to generate answer.

        Return your decision as a valid JSON object.

        Required JSON format:
        {{"grade": "good"}}
        {{"grade":"weak"}}
Question : {question}
Retrieved_docs : {kb_docs}""")
    print("grading started based on kb.....")
    return {"kb_grade":result.grade}

def route_after_kbgrade(state :Agentstate):
    """Router the path after the grade"""
    grade= state["kb_grade"]
    print("Routing started based on the grade....")
    if grade == "good":
        return "generate_answer"
    else:
        return "web_search"
def web_search(state: Agentstate):
    question= state["current_question"]
    result= websearch.invoke({"query":question})
    print("Searching in the web....")
    return {"web_results":str(result),
            "source_used":"web"}
def llm_grade_websource(state:Agentstate):
    """LLM will grade the source"""
    question = state["current_question"]
    kb_docs = state["kb_docs"]
    web_results=state["web_results"]
    print("Grading based on the web source")
    result=llm_with_grade.invoke(f"""
You are the evaluator and need to evaluate the source
based on the retrieved docs is enough to answer the question
Analyze the retrieved docs and decide whether
        to retrieve information is sufficient to generate answer.

        Return your decision as a valid JSON object.

        Required JSON format:
        {{"grade": "good"}}
        {{"grade":"weak"}}
Question : {question}
Retrieved_docs : {kb_docs} and web_result {web_results} here we have added the webseach information so please check and grade accordingly""")
    return {"web_grade":result.grade}
def route_after_webgrade(state: Agentstate):

    grade = state["web_grade"]
    print("routing started based on grading....")

    if grade == "good":
        return "generate"

    elif state.get("retry_count", 0) < 2:
        return "query"

    else:
        return "no_evidence"
def query_rewrite(state :Agentstate):
    """LLM will take the query and re- write it to make it clear """
    question = state["current_question"]
    result=llm.invoke(f"""
You are a senior query re-writer!
Please rewrite the below query so that we will get the better context
the question is : {question}
""")
    print("query_rewrite is started....")
    return {
    "current_question": result.content,
    "retry_count": state.get("retry_count", 0) + 1,
    "web_results": ""
}
def generate_answer(state:Agentstate):
    """LLM will generate the final answer"""
    question = state["current_question"]
    docs=state["kb_docs"]
    web_result = state.get("web_results","")
    result = llm.invoke(f"""
You are senior technical engineer and AI Engineer
so please answer the question based on the relevant docs and the question 
Please yes No i don't have answer when you don't have enough context to answer the question
Question {question}
retrieved_docs {docs},{web_result}
""")
    print("Generating the final answer")
    return {"answer":result.text}
def no_evidence(state: Agentstate):
    return {
        "answer": "I couldn't find enough relevant information to answer."
    }

builder = StateGraph(Agentstate)

## adding nodes
builder.add_node("route_decission",route_decission)
builder.add_node("retrive_docs",retrive_docs)
builder.add_node("web_search",web_search)
builder.add_node("llm_grade_source",llm_grade_source)
builder.add_node("llm_grade_websource",llm_grade_websource)
builder.add_node("fallback_llm",fallback_llm)
builder.add_node("generate_answer",generate_answer)
builder.add_node("query_rewrite",query_rewrite)
builder.add_node("no_evidence", no_evidence)



builder.add_edge(START,"route_decission")
builder.add_conditional_edges(
    "route_decission",
    route_after_decision,
    {
        "retrive_kb":"retrive_docs",
        "direct_answer":"fallback_llm"
    }
)
builder.add_edge("retrive_docs","llm_grade_source")
builder.add_conditional_edges(
    "llm_grade_source",
    route_after_kbgrade,
    {
        "generate_answer":"generate_answer",
        "web_search":"web_search"
    }
)
builder.add_edge("web_search","llm_grade_websource")
builder.add_conditional_edges(
    "llm_grade_websource",
    route_after_webgrade,
    {
        "generate":"generate_answer",
        "query":"query_rewrite",
        "no_evidence": "no_evidence"
    }
)
builder.add_edge("query_rewrite","retrive_docs")
builder.add_edge("generate_answer",END)
builder.add_edge("fallback_llm",END)
builder.add_edge("no_evidence", END)

graph= builder.compile()
from pathlib import Path
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parents[2]
load_dotenv(base_dir / ".env")
from langfuse.langchain import CallbackHandler
from langfuse import get_client
handler = CallbackHandler()
lanfuse=get_client()

config={"callbacks":[handler]}

def ask_agent(question:str,config=None):
    initial_state :Agentstate = {
        "question": question,
        "current_question":question,
        "kd_docs":[],
        "web_results":"",
        "kb_grade" : [],
        "web_grade": "",
        "answer":"",
        "source_used":"",
        "retry_count":0,
        
    }

    result = graph.invoke(initial_state,config=config)

    print("="*90)
    print(f'Question : {question}')
    print("="*90)
    print(f'source used : {result['source_used']}')
    print("="*90)
    print(f'result : {result["answer"]}')

    return result

