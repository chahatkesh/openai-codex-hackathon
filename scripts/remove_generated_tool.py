"""Remove one or more FuseKit capabilities and their local artifacts for clean retesting."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import delete, or_, select, update

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "services" / "platform"))

from app.db import async_session  # noqa: E402
from app.models import IntegrationJob, ToolDefinition  # noqa: E402
from app.services.artifact_store import (  # noqa: E402
    LOCAL_DYNAMIC_TOOLS_DIR,
    artifact_key_for_manifest,
    artifact_key_for_module,
    local_manifest_path,
    local_module_path,
)
from app.config import settings  # noqa: E402


def _delete_local_artifacts(tool_name: str) -> list[str]:
    removed: list[str] = []
    for path in (local_module_path(tool_name), local_manifest_path(tool_name)):
        if path.exists():
            path.unlink()
            removed.append(str(path))
    if LOCAL_DYNAMIC_TOOLS_DIR.exists():
        manifests_dir = LOCAL_DYNAMIC_TOOLS_DIR / "manifests"
        if manifests_dir.exists() and not any(manifests_dir.iterdir()):
            manifests_dir.rmdir()
        if not any(LOCAL_DYNAMIC_TOOLS_DIR.iterdir()):
            LOCAL_DYNAMIC_TOOLS_DIR.rmdir()
    return removed


def _delete_s3_artifacts(tool_name: str) -> list[str]:
    if settings.artifact_backend != "s3":
        return []
    try:
        import boto3

        client = boto3.client(
            "s3",
            endpoint_url=settings.artifact_s3_endpoint_url,
            aws_access_key_id=settings.artifact_s3_access_key,
            aws_secret_access_key=settings.artifact_s3_secret_key,
            region_name=settings.artifact_s3_region,
        )
        keys = [artifact_key_for_module(tool_name), artifact_key_for_manifest(tool_name)]
        client.delete_objects(
            Bucket=settings.artifact_bucket,
            Delete={"Objects": [{"Key": key} for key in keys], "Quiet": True},
        )
        return keys
    except Exception:
        return []


async def remove_generated_tool(tool_name: str) -> None:
    async with async_session() as session:
        result = await session.execute(
            select(ToolDefinition).where(ToolDefinition.name == tool_name)
        )
        tool = result.scalar_one_or_none()
        tool_id = tool.id if tool is not None else None

        if tool_id is not None:
            await session.execute(
                update(IntegrationJob)
                .where(IntegrationJob.resulting_tool_id == tool_id)
                .values(resulting_tool_id=None)
            )

        await session.execute(
            delete(IntegrationJob).where(
                or_(
                    IntegrationJob.requested_tool_name == tool_name,
                    IntegrationJob.resulting_tool_id == tool_id,
                )
            )
        )

        if tool is not None:
            await session.delete(tool)

        await session.commit()

    removed_local = _delete_local_artifacts(tool_name)
    removed_s3 = _delete_s3_artifacts(tool_name)

    print(f"Removed tool definition and integration jobs for: {tool_name}")
    if removed_local:
        print("Removed local artifacts:")
        for item in removed_local:
            print(f"  - {item}")
    if removed_s3:
        print("Removed artifact keys:")
        for item in removed_s3:
            print(f"  - {item}")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/remove_generated_tool.py <tool_name> [<tool_name> ...]")
        return 1

    async def _run() -> None:
        for tool_name in sys.argv[1:]:
            await remove_generated_tool(tool_name)

    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
