
from pathlib import Path
import boto3

# 1. Create AWS session using local credentials
session = boto3.Session(
    profile_name="rag-s3-developer",
    region_name="ap-southeast-2"
)

# 2. Create S3 client
s3 = session.client("s3")

bucket_name = "enterprise-rag-docs-587787861821"

# 3. Find uploaded documents
response = s3.list_objects_v2(
    Bucket=bucket_name,
    Prefix="uploads/"
)

objects = [
    obj["Key"]
    for obj in response.get("Contents", [])
    if not obj["Key"].endswith("/")
]

if not objects:
    raise RuntimeError("No documents found in uploads/")

# 4. Select the first document
object_key = objects[0]

# 5. Create a local download folder
download_dir = Path("downloads")
download_dir.mkdir(exist_ok=True)

# 6. Download the document
local_path = download_dir / Path(object_key).name

s3.download_file(
    bucket_name,
    object_key,
    str(local_path)
)

print("Downloaded:", object_key)
print("Saved to:", local_path.resolve())
