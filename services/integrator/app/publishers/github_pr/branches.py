from __future__ import annotations

from typing import Any

from app.publishers.github_pr.client import GitHubClientProtocol
from app.publishers.github_pr.errors import GitHubPublishError, GitHubPublishErrorCode
from app.publishers.github_pr.schemas import BranchState, normalize_branch_name


class BranchManager:
    def __init__(self, client: GitHubClientProtocol) -> None:
        self.client = client

    async def resolve_base_branch(
        self,
        *,
        owner: str,
        repo: str,
        requested_base_branch: str | None,
    ) -> str:
        if requested_base_branch:
            return normalize_branch_name(requested_base_branch)

        repository = await self.client.get_repository(owner, repo)
        default_branch = str(repository.get("default_branch") or "").strip()
        if not default_branch:
            raise GitHubPublishError(
                GitHubPublishErrorCode.BRANCH_CREATION_FAILED,
                "Could not resolve repository default branch from GitHub.",
                details={"owner": owner, "repo": repo},
            )
        return normalize_branch_name(default_branch)

    async def get_branch_head(self, *, owner: str, repo: str, branch: str) -> BranchState:
        try:
            ref = await self.client.get_ref(owner, repo, f"heads/{branch}")
            commit_sha = str(ref["object"]["sha"])
            commit = await self.client.get_commit(owner, repo, commit_sha)
            tree_sha = str(commit["tree"]["sha"])
        except GitHubPublishError:
            raise
        except (KeyError, TypeError) as exc:
            raise GitHubPublishError(
                GitHubPublishErrorCode.GITHUB_API_ERROR,
                "GitHub returned an unexpected branch or commit payload.",
                details={"owner": owner, "repo": repo, "branch": branch},
            ) from exc

        return BranchState(name=branch, commit_sha=commit_sha, tree_sha=tree_sha, created=False)

    async def create_publish_branch(
        self,
        *,
        owner: str,
        repo: str,
        base_branch: str,
        branch_name: str,
        reuse_existing: bool,
    ) -> BranchState:
        base_branch = normalize_branch_name(base_branch)
        branch_name = normalize_branch_name(branch_name)
        if branch_name == base_branch:
            raise GitHubPublishError(
                GitHubPublishErrorCode.INVALID_PAYLOAD,
                "Publish branch must be different from the base branch.",
                details={"branch": branch_name, "base_branch": base_branch},
            )

        try:
            base_state = await self.get_branch_head(owner=owner, repo=repo, branch=base_branch)
            await self.client.create_ref(
                owner,
                repo,
                ref=f"refs/heads/{branch_name}",
                sha=base_state.commit_sha,
            )
            return BranchState(
                name=branch_name,
                commit_sha=base_state.commit_sha,
                tree_sha=base_state.tree_sha,
                created=True,
            )
        except GitHubPublishError as exc:
            if _is_reference_exists(exc) and reuse_existing:
                return await self.get_branch_head(owner=owner, repo=repo, branch=branch_name)
            if exc.code == GitHubPublishErrorCode.AUTH_FAILED:
                raise
            if exc.code == GitHubPublishErrorCode.INVALID_PAYLOAD:
                raise
            raise GitHubPublishError(
                GitHubPublishErrorCode.BRANCH_CREATION_FAILED,
                f"Failed to create publish branch '{branch_name}'.",
                status_code=exc.status_code,
                details=exc.details,
            ) from exc


def _is_reference_exists(exc: GitHubPublishError) -> bool:
    if exc.status_code != 422:
        return False
    haystack = _details_text(exc.details).lower()
    return "reference already exists" in haystack or "already exists" in haystack


def _details_text(details: Any) -> str:
    if details is None:
        return ""
    if isinstance(details, dict):
        parts = [str(details.get("message", ""))]
        for error in details.get("errors", []) or []:
            parts.append(str(error))
        return " ".join(parts)
    return str(details)
