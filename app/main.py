from pathlib import Path
from fastapi import FastAPI,Request
from app.api.routes import router
from app.core.config import get_settings
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.core.logging import configure_logging
from app.services.audit import initialize_audit_db

base_dir1 = Path(__file__).resolve().parent.parent
base_dir1 = Path(__file__).resolve().parent.parent

print("MAIN FILE:", Path(__file__).resolve())
print("PROJECT ROOT:", base_dir1)
print("STATIC PATH:", base_dir1 / "static")
print("STATIC EXISTS:", (base_dir1 / "static").is_dir())
print("TEMPLATES EXISTS:", (base_dir1 / "templates").is_dir())

configure_logging()
initialize_audit_db()
settings = get_settings()

app = FastAPI(title=settings.app_name,description="Enterprise IT Agentic RAG",version="1.0.0")
app.include_router(router)
app.mount("/static",StaticFiles(directory=base_dir1/"static"),name="static")
templates = Jinja2Templates(directory=base_dir1/"templates")

@app.get("/",response_class=HTMLResponse)
def home(request:Request):
    return templates.TemplateResponse(request=request,
        name="index.html",
        context={"app_name": settings.app_name}
    )