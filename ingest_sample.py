from app.core.config import get_settings

settings=get_settings()

from app.services.ingestion import chunk_documents,load_file
from app.rag.vectorstore import add_documents

from pathlib import Path

documents = load_file(Path("data/sample_kb/sample.pdf"))

chunks = chunk_documents(documents)

print(f"Loaded {len(documents)} documents and split into {len(chunks)} chunks.")
print(chunks[0].page_content[:500])


add_documents(chunks)
