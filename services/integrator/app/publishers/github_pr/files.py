from __future__ import annotations

from collections.abc import Sequence

from app.publishers.github_pr.client import GitHubClientProtocol
from app.publishers.github_pr.errors import GitHubPublishError, GitHubPublishErrorCode
from app.publishers.github_pr.schemas import BranchState, CommitResult, PublishFile


class FileCommitter:
    def __init__(self, client: GitHubClientProtocol) -> None:
        self.client = client

    async def commit_files(
        self,
        *,
        owner: str,
        repo: str,
        branch: BranchState,
        files: Sequence[PublishFile],
        commit_message: str,
    ) -> CommitResult:
        tree_entries: list[dict[str, str]] = []
        for file in files:
            blob = await self.client.create_blob(owner, repo, file)
            try:
                blob_sha = str(blob["sha"])
            except (KeyError, TypeError) as exc:
                raise GitHubPublishError(
                    GitHubPublishErrorCode.GITHUB_API_ERROR,
                    "GitHub returned an unexpected blob payload.",
                    details={"path": file.path, "payload": blob},
                ) from exc

            tree_entries.append(
                {
                    "path": file.path,
                    "mode": file.mode,
                    "type": "blob",
                    "sha": blob_sha,
                }
            )

        tree = await self.client.create_tree(
            owner,
            repo,
            base_tree=branch.tree_sha,
            tree=tree_entries,
        )
        try:
            tree_sha = str(tree["sha"])
        except (KeyError, TypeError) as exc:
            raise GitHubPublishError(
                GitHubPublishErrorCode.GITHUB_API_ERROR,
                "GitHub returned an unexpected tree payload.",
                details={"payload": tree},
            ) from exc

        if tree_sha == branch.tree_sha:
            return CommitResult(commit_sha=branch.commit_sha, tree_sha=tree_sha, changed=False)

        commit = await self.client.create_commit(
            owner,
            repo,
            message=commit_message,
            tree_sha=tree_sha,
            parent_shas=[branch.commit_sha],
        )
        try:
            commit_sha = str(commit["sha"])
        except (KeyError, TypeError) as exc:
            raise GitHubPublishError(
                GitHubPublishErrorCode.GITHUB_API_ERROR,
                "GitHub returned an unexpected commit payload.",
                details={"payload": commit},
            ) from exc

        try:
            await self.client.update_ref(owner, repo, f"heads/{branch.name}", commit_sha)
        except GitHubPublishError as exc:
            if exc.status_code in (409, 422):
                raise GitHubPublishError(
                    GitHubPublishErrorCode.FILE_CONFLICT,
                    "Branch head changed while publishing files; retry with a fresh branch or idempotency key.",
                    status_code=exc.status_code,
                    details=exc.details,
                ) from exc
            raise

        return CommitResult(commit_sha=commit_sha, tree_sha=tree_sha, changed=True)
