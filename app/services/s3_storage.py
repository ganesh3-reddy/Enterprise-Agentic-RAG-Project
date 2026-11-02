
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from requests import session
from app.core.config import get_settings
settings = get_settings()

S3_BUCKET = settings.s3_bucket_name
AWS_REGION = settings.aws_region

def upload_document_to_s3(
    local_file_path: Path,
    object_key: str
) -> str:
    """
    Upload a local document to S3.

    Returns the S3 URI after successful upload.
    """
    session = boto3.Session(
    profile_name=settings.aws_profile or None,
    region_name=AWS_REGION
)

    s3 = session.client("s3")

    try:
        s3.upload_file(
            Filename=str(local_file_path),
            Bucket=S3_BUCKET,
            Key=object_key,
        )
    except ClientError:
        # Don't expose internal AWS error details to API clients.
        raise

    return f"s3://{S3_BUCKET}/{object_key}"
