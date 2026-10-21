from pathlib import Path
from fastapi import APIRouter,UploadFile,File,HTTPException,Header
from app.core.config import get_settings
from app.rag.workflow import ask_agent,config
from pydantic import BaseModel,Field
from app.rag.vectorstore import add_documents
from app.services.ingestion import load_file,chunk_documents,Supported
from app.services.audit import write_audit_log
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/api",tags=["RAG API"])
settings = get_settings()

class chatRequest(BaseModel):
    question:str = Field(min_length=2,max_length=1000,description="User query to ask the RAG agent")
    thread_id: str | None = None

@router.post("/chat")
def chat(payload: chatRequest):
    try:
        response = ask_agent(payload.question,config=config)

        write_audit_log(
            user_query=payload.question,
            source_used=response.get("source_used", ""),
            answer=response.get("answer", ""),
            web_grade=response.get("web_grade", ""),
            retry_count=response.get("retry_count", 0)
        )

        return {
            "answer": response.get("answer", ""),
            "source_used": response.get("source_used", ""),
            "kb_grade": response.get("kb_grade", ""),
            "web_grade": response.get("web_grade", ""),
            "retry_count": response.get("retry_count", 0)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        ) from e

@router.post("/upload")
async def upload_file(file:UploadFile=File(...),x_admin_key:str=Header(...)):
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(status_code=403,detail="Invalid admin key")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in Supported:
        raise HTTPException(status_code=400,detail=f"Unsupported file format {suffix}")
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True,exist_ok=True)
    dest = upload_path / Path(file.filename).name
    dest.write_bytes(await file.read())
    docs = await run_in_threadpool(load_file, dest)
    chunked_docs =await run_in_threadpool(chunk_documents, docs)
    ids = await run_in_threadpool(add_documents, chunked_docs)
    return {"message":f"Successfully uploaded and added {len(ids)} documents to the vector store."}
    
