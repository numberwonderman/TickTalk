"""Optional S3 upload for the original photo. Stubbed until we finalize
the AWS hosting decision in docs/BUILD_PLAN.md Milestone 5 -- storage is
not required for the triage flow itself to work, so this fails soft.
"""

import logging
import uuid

from app.core.config import settings

logger = logging.getLogger(__name__)


def store_image(image_bytes: bytes) -> str | None:
    """Returns the S3 key if stored, or None if S3 isn't configured.
    Never raises -- a storage failure must not block a triage result."""
    if not settings.s3_bucket:
        logger.info("TICKTALK_S3_BUCKET not set; skipping image storage")
        return None

    try:
        import boto3

        key = f"uploads/{uuid.uuid4()}.jpg"
        client = boto3.client("s3", region_name=settings.aws_region)
        client.put_object(Bucket=settings.s3_bucket, Key=key, Body=image_bytes)
        return key
    except Exception:
        logger.exception("Failed to store image in S3; continuing without it")
        return None
