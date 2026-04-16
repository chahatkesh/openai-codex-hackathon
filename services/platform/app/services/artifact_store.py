from __future__ import annotations

from pathlib import Path
from typing import Any

from app.config import settings


LOCAL_DYNAMIC_TOOLS_DIR = Path("/tmp/fusekit_dynamic_tools")
LOCAL_MANIFESTS_DIR = LOCAL_DYNAMIC_TOOLS_DIR / "manifests"


def artifact_key_for_module(tool_name: str) -> str:
    return f"dynamic-tools/{tool_name}.py"


def artifact_key_for_manifest(tool_name: str) -> str:
    return f"manifests/{tool_name}.json"


def artifact_uri_for_key(key: str) -> str:
    return f"s3://{settings.artifact_bucket}/{key}"


def local_module_path(tool_name: str) -> Path:
    return LOCAL_DYNAMIC_TOOLS_DIR / f"{tool_name}.py"


def local_manifest_path(tool_name: str) -> Path:
    return LOCAL_MANIFESTS_DIR / f"{tool_name}.json"


def artifact_metadata(tool_name: str) -> dict[str, Any]:
    module_key = artifact_key_for_module(tool_name)
    manifest_key = artifact_key_for_manifest(tool_name)
    return {
        "backend": settings.artifact_backend,
        "bucket": settings.artifact_bucket,
        "preferred_source": "s3" if settings.artifact_backend == "s3" else "local",
        "runtime_module": {
            "local_path": str(local_module_path(tool_name)),
            "artifact_key": module_key,
            "artifact_uri": artifact_uri_for_key(module_key),
        },
        "manifest": {
            "local_path": str(local_manifest_path(tool_name)),
            "artifact_key": manifest_key,
            "artifact_uri": artifact_uri_for_key(manifest_key),
        },
    }


def _build_s3_client():
    import boto3

    return boto3.client(
        "s3",
        endpoint_url=settings.artifact_s3_endpoint_url,
        aws_access_key_id=settings.artifact_s3_access_key,
        aws_secret_access_key=settings.artifact_s3_secret_key,
        region_name=settings.artifact_s3_region,
    )


def download_text(key: str) -> str | None:
    if settings.artifact_backend != "s3":
        return None
    try:
        client = _build_s3_client()
        obj = client.get_object(Bucket=settings.artifact_bucket, Key=key)
        return obj["Body"].read().decode("utf-8")
    except Exception:
        return None


def download_file(key: str, destination: Path) -> Path | None:
    if settings.artifact_backend != "s3":
        return None
    try:
        client = _build_s3_client()
        destination.parent.mkdir(parents=True, exist_ok=True)
        client.download_file(settings.artifact_bucket, key, str(destination))
        return destination
    except Exception:
        return None
