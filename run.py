
from app.rag.vectorstore import get_embedding
from app.core.config import get_settings

embedding = get_embedding()

vector = embedding.embed_query("What is Agentic RAG?")
from app.rag.vectorstore import get_embedding_dimensions
print("Actual dimension:", len(vector))
print("Configured dimension:", get_embedding_dimensions(
    get_settings().embedding_model
))

print(
    get_embedding_dimensions(
        "sentence-transformers/all-MiniLM-L6-v2"
    )
)