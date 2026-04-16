from __future__ import annotations

import logging
import re
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from app.publishers.github_pr.branches import BranchManager
from app.publishers.github_pr.client import GitHubClient, GitHubClientProtocol
from app.publishers.github_pr.config import GitHubPublishingConfig
from app.publishers.github_pr.errors import GitHubPublishError, GitHubPublishErrorCode
from app.publishers.github_pr.files import FileCommitter
from app.publishers.github_pr.pull_requests import PullRequestManager
from app.publishers.github_pr.schemas import (
    PublishPullRequestRequest,
    PublishPullRequestResult,
    PublishStatus,
    normalize_branch_name,
)

PublishEventHook = Callable[[dict[str, Any]], None]

logger = logging.getLogger("fusekit.integrator.github_publish")


class GitHubPullRequestPublisher:
    def __init__(
        self,
        *,
        client: GitHubClientProtocol,
        config: GitHubPublishingConfig | None = None,
        event_hook: PublishEventHook | None = None,
        log: logging.Logger | None = None,
    ) -> None:
        self.client = client
        self.config = config or GitHubPublishingConfig.from_settings()
        self.event_hook = event_hook
        self.log = log or logger
        self.branches = BranchManager(client)
        self.files = FileCommitter(client)
        self.pull_requests = PullRequestManager(client)

    async def publish(
        self,
        payload: PublishPullRequestRequest | Mapping[str, Any],
    ) -> PublishPullRequestResult:
        request = _coerce_request(payload)
        target = self.config.resolve_repository(request)
        owner = target.owner
        repo = target.name
        base_branch = await self.branches.resolve_base_branch(
            owner=owner,
            repo=repo,
            requested_base_branch=target.base_branch,
        )
        metadata = _normalize_metadata(request.metadata, request.idempotency_key)
        title = request.title or _default_title(metadata)
        commit_message = request.commit_message or _default_commit_message(metadata)
        body = request.body or _default_body(metadata)
        branch_name = _resolve_branch_name(request, self.config, metadata, title)
        branch_name = normalize_branch_name(branch_name)
        draft = self.config.draft_by_default if request.draft is None else request.draft

        self._emit(
            "started",
            owner=owner,
            repo=repo,
            base_branch=base_branch,
            branch_name=branch_name,
            file_count=len(request.files),
        )

        branch = await self.branches.create_publish_branch(
            owner=owner,
            repo=repo,
            base_branch=base_branch,
            branch_name=branch_name,
            reuse_existing=request.reuse_existing_branch,
        )
        commit = await self.files.commit_files(
            owner=owner,
            repo=repo,
            branch=branch,
            files=request.files,
            commit_message=commit_message,
        )

        pr = None
        if commit.changed:
            pr = await self.pull_requests.ensure_pull_request(
                owner=owner,
                repo=repo,
                branch_name=branch_name,
                base_branch=base_branch,
                title=title,
                body=body,
                draft=draft,
                update_existing=request.update_existing_pr,
            )
            status = PublishStatus.CREATED if branch.created and not pr.existed else PublishStatus.UPDATED
        else:
            pr = None
            if request.update_existing_pr:
                pr = await self.pull_requests.find_open_pull_request(
                    owner=owner,
                    repo=repo,
                    branch_name=branch_name,
                    base_branch=base_branch,
                )
            status = PublishStatus.ALREADY_OPEN if pr else PublishStatus.NO_CHANGES

        result = PublishPullRequestResult(
            status=status,
            owner=owner,
            repo=repo,
            base_branch=base_branch,
            branch_name=branch_name,
            pr_url=pr.url if pr else None,
            pr_number=pr.number if pr else None,
            commit_sha=commit.commit_sha,
            files=[file.path for file in request.files],
            metadata=metadata,
        )

        self._emit(
            "completed",
            owner=owner,
            repo=repo,
            base_branch=base_branch,
            branch_name=branch_name,
            status=result.status.value,
            pr_url=result.pr_url,
            commit_sha=result.commit_sha,
        )
        return result

    def _emit(self, event: str, **payload: Any) -> None:
        event_payload = {"event": f"github_publish_{event}", **payload}
        self.log.info(
            "github_publish_%s owner=%s repo=%s branch=%s status=%s",
            event,
            payload.get("owner"),
            payload.get("repo"),
            payload.get("branch_name"),
            payload.get("status"),
        )
        if self.event_hook:
            self.event_hook(event_payload)


async def publish_via_pull_request(
    payload: PublishPullRequestRequest | Mapping[str, Any],
    *,
    client: GitHubClientProtocol | None = None,
    config: GitHubPublishingConfig | None = None,
    event_hook: PublishEventHook | None = None,
) -> PublishPullRequestResult:
    resolved_config = config or GitHubPublishingConfig.from_settings()
    if client is not None:
        publisher = GitHubPullRequestPublisher(
            client=client,
            config=resolved_config,
            event_hook=event_hook,
        )
        return await publisher.publish(payload)

    token = resolved_config.require_token()
    github_client = GitHubClient(
        token=token,
        api_base_url=resolved_config.api_base_url,
        user_agent=resolved_config.user_agent,
        timeout_seconds=resolved_config.timeout_seconds,
    )
    try:
        publisher = GitHubPullRequestPublisher(
            client=github_client,
            config=resolved_config,
            event_hook=event_hook,
        )
        return await publisher.publish(payload)
    finally:
        await github_client.aclose()


def _coerce_request(payload: PublishPullRequestRequest | Mapping[str, Any]) -> PublishPullRequestRequest:
    try:
        return PublishPullRequestRequest.model_validate(payload)
    except ValidationError as exc:
        raise GitHubPublishError(
            GitHubPublishErrorCode.INVALID_PAYLOAD,
            "GitHub publish payload is invalid.",
            details=exc.errors(),
        ) from exc


def _normalize_metadata(metadata: Mapping[str, Any], idempotency_key: str | None) -> dict[str, Any]:
    normalized = dict(metadata)
    key = idempotency_key or normalized.get("idempotency_key")
    if key:
        normalized["idempotency_key"] = str(key).strip()[:80]
    return normalized


def _resolve_branch_name(
    request: PublishPullRequestRequest,
    config: GitHubPublishingConfig,
    metadata: Mapping[str, Any],
    title: str,
) -> str:
    if request.branch_name:
        return request.branch_name

    prefix = request.branch_prefix or config.branch_prefix
    label = (
        metadata.get("tool_name")
        or metadata.get("kit_slug")
        or metadata.get("name")
        or title
        or "generated-files"
    )
    slug = _slugify(str(label), fallback="generated-files")[:48]
    idempotency_key = metadata.get("idempotency_key")
    if idempotency_key:
        suffix = _slugify(str(idempotency_key), fallback=uuid.uuid4().hex[:8])[:80]
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        suffix = f"{timestamp}-{uuid.uuid4().hex[:8]}"
    return f"{prefix}/{slug}-{suffix}"


def _default_title(metadata: Mapping[str, Any]) -> str:
    label = metadata.get("tool_name") or metadata.get("kit_slug") or metadata.get("name")
    if label:
        return f"Publish generated files for {label}"
    return "Publish generated files"


def _default_commit_message(metadata: Mapping[str, Any]) -> str:
    label = metadata.get("tool_name") or metadata.get("kit_slug") or metadata.get("name")
    if label:
        return f"Publish generated files for {label}"
    return "Publish generated files"


def _default_body(metadata: Mapping[str, Any]) -> str:
    source = metadata.get("source") or "FuseKit publishing automation"
    return (
        f"Automated draft PR created by {source}.\n\n"
        "Review the generated files before merging into the marketplace repository."
    )


def _slugify(value: str, *, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    slug = slug.strip("-._")
    return slug or fallback
