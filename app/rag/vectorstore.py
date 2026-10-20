from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone,ServerlessSpec
from app.core.config import get_settings

index_name = get_settings().pinecone_index_name
namespace = get_settings().pinecone_namespace
pc = Pinecone(api_key=get_settings().pinecone_api_key)

_embedding=None
_vectorstore=None

Embedding_dimensions ={
    "text-embedding-3-small":1536,
    "text-embedding-3-large":3072,
    "sentence-transformers/all-minilm-l6-v2":384,
}

def get_embedding_dimensions(model_name: str):

    name = (model_name or get_settings().embedding_model or "").strip().lower()

    if not name:
        raise ValueError("Embedding model name is not provided")

    if name in Embedding_dimensions:
        return Embedding_dimensions[name]

    raise ValueError(f"Unsupported embedding model: {model_name}")

def get_embedding():
    global _embedding
    if _embedding is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _embedding = HuggingFaceEmbeddings(model_name=get_settings().embedding_model,encode_kwargs={"normalize_embeddings":True})
    return _embedding
import time
settings = get_settings()
def ensure_index():
    if not settings.pinecone_api_key:
        raise ValueError("Pinecone API key is not provided")
    desired_dimensions = get_embedding_dimensions(get_settings().embedding_model)
    pc = Pinecone(api_key=get_settings().pinecone_api_key)
    names = [x["name"] for x in pc.list_indexes()]

    if settings.pinecone_index_name in names:
        index_info = pc.describe_index(settings.pinecone_index_name)
        current_dimensions = getattr(index_info,"dimension",None)
        

        if current_dimensions is not None and current_dimensions != desired_dimensions:
            pc.delete_index(settings.pinecone_index_name)
            while settings.pinecone_index_name in [x["name"] for x in pc.list_indexes()]:
                time.sleep(1)

    if settings.pinecone_index_name not in [x["name"] for x in pc.list_indexes()]:
        pc.create_index(settings.pinecone_index_name,dimension=desired_dimensions,metric="cosine",spec=ServerlessSpec(cloud="aws",region="us-east-1"))
        while not pc.describe_index(settings.pinecone_index_name).status["ready"]:
            time.sleep(1)
    return pc.describe_index(settings.pinecone_index_name)

def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        index = ensure_index()
        _vectorstore = PineconeVectorStore(index_name=settings.pinecone_index_name,embedding=get_embedding(),namespace=get_settings().pinecone_namespace,pinecone_api_key=get_settings().pinecone_api_key)
    return _vectorstore


def get_retriever():
    vectorstore = get_vectorstore()
    return vectorstore.as_retriever(search_kwargs={"k":get_settings().top_k})

def add_documents(documents):
    vectorstore = get_vectorstore()
    return vectorstore.add_documents(documents)



       
        



