import json
import logging
import boto3
from botocore.exceptions import ClientError
from config.settings import settings

logger = logging.getLogger(__name__)

_s3_client = None


def _get_s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.aws_access_key_id or None,
            aws_secret_access_key=settings.aws_secret_access_key or None,
            region_name=settings.aws_region,
        )
    return _s3_client


def upload_transcript(call_id: str, payload: dict) -> str:
    """Upload raw transcript JSON to S3. Returns the S3 key."""
    key = f"transcripts/{call_id}.json"
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    try:
        _get_s3().put_object(
            Bucket=settings.s3_bucket,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        logger.info("Uploaded transcript to s3://%s/%s", settings.s3_bucket, key)
    except ClientError as exc:
        logger.error("S3 upload failed for %s: %s", call_id, exc)
        raise
    return key


def get_presigned_url(key: str, expires_in: int = 3600) -> str:
    return _get_s3().generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.s3_bucket, "Key": key},
        ExpiresIn=expires_in,
    )
