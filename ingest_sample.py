from app.core.config import get_settings
from app.services.ingestion import load_file,chunk_documents
from pathlib import Path
from app.rag.vectorstore import add_documents

settings = get_settings()

folder = Path(settings.sample_kb_dir)

files = [f for f in folder.iterdir() if f.is_file()]

all_documents = []

for file in files:
    all_documents.extend(load_file(file))
chunked_documents = chunk_documents(all_documents)
ids = add_documents(chunked_documents)
print(f"Added {len(ids)} documents to the vector store.")


