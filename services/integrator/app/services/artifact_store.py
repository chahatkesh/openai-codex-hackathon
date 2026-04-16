from __future__ import annotations

from app.config import settings


def artifact_key_for_module(tool_name: str) -> str:
    return f"dynamic-tools/{tool_name}.py"


def artifact_key_for_manifest(tool_name: str) -> str:
    return f"manifests/{tool_name}.json"


def artifact_uri_for_key(key: str) -> str:
    return f"s3://{settings.artifact_bucket}/{key}"


def _build_s3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.artifact_s3_endpoint_url,
        aws_access_key_id=settings.artifact_s3_access_key,
        aws_secret_access_key=settings.artifact_s3_secret_key,
        region_name=settings.artifact_s3_region,
    )


def ensure_bucket() -> None:
    if settings.artifact_backend != "s3":
        return
    client = _build_s3_client()
    try:
        client.head_bucket(Bucket=settings.artifact_bucket)
    except Exception:
        client.create_bucket(Bucket=settings.artifact_bucket)


def upload_text(key: str, body: str, content_type: str) -> str | None:
    if settings.artifact_backend != "s3":
        return None
    try:
        ensure_bucket()
        client = _build_s3_client()
        client.put_object(
            Bucket=settings.artifact_bucket,
            Key=key,
            Body=body.encode("utf-8"),
            ContentType=content_type,
        )
        return artifact_uri_for_key(key)
    except Exception:
        return None
