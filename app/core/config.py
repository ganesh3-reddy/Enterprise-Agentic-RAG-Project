from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    app_name:str = "Enterprise-IT-Agentic-Rag"
    app_env :str = "Developement"
    openai_api_key :str = ""
    groq_api_key :str = ""
    tavily_api_key:str =""
    pinecone_api_key:str=""
    pinecone_index_name :str="fde-it-support-rag"
    pinecone_namespace:str="company-it-kb"
    embedding_model:str="all-MiniLM-L6-v2"
    openai_model:str="openai/gpt-oss-120b"
    groq_model: str = "openai/gpt-oss-120b"
    top_k :int=4
    max_retries:int=1
    admin_api_key:str="change-me"
    audit_db_path:str=str(base_dir/"data"/"audit.db")
    upload_dir :str =str(base_dir/"uploads")
    sample_kb_dir:str=str(base_dir/"data"/"sample_kb")
    langfuse_api_key:str=""
    langfuse_secret_key:str=""
    langfuse_base_url:str="https://us.cloud.langfuse.com"


    model_config=SettingsConfigDict(env_file=str(base_dir/".env"),extra="ignore")

@lru_cache
def get_settings() ->Settings:
    return Settings()