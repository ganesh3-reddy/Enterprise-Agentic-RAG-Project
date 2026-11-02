from pathlib import Path
from fastapi import APIRouter,UploadFile,File,HTTPException,Header
from app.core.config import get_settings
from app.rag.workflow import ask_agent,config
from pydantic import BaseModel,Field
from app.rag.vectorstore import add_documents
from app.services.ingestion import load_file,chunk_documents,Supported
from app.services.audit import write_audit_log
from starlette.concurrency import run_in_threadpool
from app.services.s3_storage import upload_document_to_s3
from uuid import uuid4
from app.services.audit_postgres import write_postgres_audit

router = APIRouter(prefix="/api",tags=["RAG API"])
settings = get_settings()

class chatRequest(BaseModel):
    question:str = Field(min_length=2,max_length=1000,description="User query to ask the RAG agent")
    thread_id: str | None = None

@router.post("/chat")
def chat(payload: chatRequest):
    try:
        response = ask_agent(payload.question,config=config)

        write_postgres_audit(
            user_query=payload.question,
            source_used=response.get("source_used", ""),
            answer=response.get("answer", ""),
            status="success" if response.get("answer") else "failure",
            retries=response.get("retry_count", 0)
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
async def upload_file(
    file: UploadFile = File(...),
    x_admin_key: str = Header(...)
):
    # 1. Validate admin API key
    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=403,
            detail="Invalid admin key"
        )

    # 2. Validate file format
    original_name = Path(file.filename).name
    suffix = Path(original_name).suffix.lower()

    if suffix not in Supported:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format {suffix}"
        )

    # 3. Create upload directory
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    # 4. Generate unique filename
    unique_name = f"{uuid4().hex}_{original_name}"

    # 5. Save uploaded file locally ONCE
    dest = upload_path / unique_name
    dest.write_bytes(await file.read())

    # 6. Upload original document to S3
    s3_key = f"uploads/{unique_name}"
    s3_uri = await run_in_threadpool(
        upload_document_to_s3,
        dest,
        s3_key
    )

    # 7. Load and process document
    docs = await run_in_threadpool(load_file, dest)

    # 8. Attach S3 URI to document metadata
    for doc in docs:
        doc.metadata["s3_uri"] = s3_uri

    # 9. Chunk documents
    chunked_docs = await run_in_threadpool(
        chunk_documents,
        docs
    )

    # 10. Insert embeddings into Pinecone
    ids = await run_in_threadpool(
        add_documents,
        chunked_docs
    )

    # 11. Return response
    return {
        "message": "Document uploaded and indexed successfully",
        "filename": original_name,
        "s3_uri": s3_uri,
        "chunks_indexed": len(ids)
    }

