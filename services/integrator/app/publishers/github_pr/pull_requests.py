from __future__ import annotations

from typing import Any

from app.publishers.github_pr.client import GitHubClientProtocol
from app.publishers.github_pr.errors import GitHubPublishError, GitHubPublishErrorCode
from app.publishers.github_pr.schemas import PullRequestResult


class PullRequestManager:
    def __init__(self, client: GitHubClientProtocol) -> None:
        self.client = client

    async def find_open_pull_request(
        self,
        *,
        owner: str,
        repo: str,
        branch_name: str,
        base_branch: str,
    ) -> PullRequestResult | None:
        pulls = await self.client.list_pull_requests(
            owner,
            repo,
            head=f"{owner}:{branch_name}",
            base=base_branch,
            state="open",
        )
        if not pulls:
            return None
        return _to_pull_request_result(pulls[0], existed=True)

    async def ensure_pull_request(
        self,
        *,
        owner: str,
        repo: str,
        branch_name: str,
        base_branch: str,
        title: str,
        body: str | None,
        draft: bool,
        update_existing: bool,
    ) -> PullRequestResult:
        if update_existing:
            existing = await self.find_open_pull_request(
                owner=owner,
                repo=repo,
                branch_name=branch_name,
                base_branch=base_branch,
            )
            if existing is not None:
                return existing

        try:
            payload = await self.client.create_pull_request(
                owner,
                repo,
                title=title,
                head=branch_name,
                base=base_branch,
                body=body,
                draft=draft,
            )
            return _to_pull_request_result(payload, existed=False)
        except GitHubPublishError as exc:
            if exc.status_code == 422 and update_existing:
                existing = await self.find_open_pull_request(
                    owner=owner,
                    repo=repo,
                    branch_name=branch_name,
                    base_branch=base_branch,
                )
                if existing is not None:
                    return existing
            if exc.code == GitHubPublishErrorCode.AUTH_FAILED:
                raise
            raise GitHubPublishError(
                GitHubPublishErrorCode.PR_CREATION_FAILED,
                f"Failed to create draft pull request for branch '{branch_name}'.",
                status_code=exc.status_code,
                details=exc.details,
            ) from exc


def _to_pull_request_result(payload: dict[str, Any], *, existed: bool) -> PullRequestResult:
    try:
        return PullRequestResult(
            number=int(payload["number"]),
            url=str(payload["html_url"]),
            draft=bool(payload.get("draft", False)),
            existed=existed,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise GitHubPublishError(
            GitHubPublishErrorCode.PR_CREATION_FAILED,
            "GitHub returned an unexpected pull request payload.",
            details={"payload": payload},
        ) from exc
