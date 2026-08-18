import boto3
from botocore.client import Config
import structlog
from app.core.config import settings

logger = structlog.get_logger()

def get_s3_client():
    # Use standard boto3 client pointing to MinIO
    client = boto3.client(
        's3',
        endpoint_url=f"http://{settings.MINIO_ENDPOINT}" if not settings.MINIO_SECURE else f"https://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
        region_name='us-east-1', # Default for MinIO
        use_ssl=settings.MINIO_SECURE
    )
    return client

def ensure_bucket_exists(bucket_name: str):
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket_name)
    except Exception as e:
        # Bucket does not exist or we don't have permission
        error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
        if error_code == '404':
            logger.info("creating_s3_bucket", bucket_name=bucket_name)
            s3.create_bucket(Bucket=bucket_name)
        else:
            logger.error("s3_bucket_check_failed", error=str(e), bucket_name=bucket_name)
            raise e
