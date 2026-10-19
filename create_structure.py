from pathlib import Path

root = Path(".")

folders = ["app/api",
           "app/core",
           "app/rag",
           "app/services",
           "data",
           "templates",
           "statis",
           "uploads",
           "tests"]

files = ["app/main.py",
         "requirements.txt",
         "ingest_sample.py",
         "run.py",
         ".env"]

for folder in folders:
    (root/folder).mkdir(parents=True,exist_ok=True)
for file in files:
    (root/file).touch(exist_ok=True)

print("Successfully created!")