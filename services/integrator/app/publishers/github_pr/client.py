from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

import httpx

from app.publishers.github_pr.errors import GitHubPublishError, GitHubPublishErrorCode
from app.publishers.github_pr.schemas import PublishFile


class GitHubClientProtocol(Protocol):
    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        ...

    async def get_ref(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        ...

    async def create_ref(self, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        ...

    async def get_commit(self, owner: str, repo: str, sha: str) -> dict[str, Any]:
        ...

    async def create_blob(self, owner: str, repo: str, file: PublishFile) -> dict[str, Any]:
        ...

    async def create_tree(
        self,
        owner: str,
        repo: str,
        *,
        base_tree: str,
        tree: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        ...

    async def create_commit(
        self,
        owner: str,
        repo: str,
        *,
        message: str,
        tree_sha: str,
        parent_shas: Sequence[str],
    ) -> dict[str, Any]:
        ...

    async def update_ref(self, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        ...

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        *,
        title: str,
        head: str,
        base: str,
        body: str | None,
        draft: bool,
    ) -> dict[str, Any]:
        ...

    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        *,
        head: str,
        base: str,
        state: str = "open",
    ) -> list[dict[str, Any]]:
        ...


class GitHubClient:
    """Small async GitHub REST client scoped to PR publishing operations."""

    def __init__(
        self,
        *,
        token: str,
        api_base_url: str = "https://api.github.com",
        user_agent: str = "FuseKit-Integrator/0.1",
        timeout_seconds: float = 30.0,
    ) -> None:
        self._client = httpx.AsyncClient(
            base_url=api_base_url.rstrip("/"),
            timeout=timeout_seconds,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": user_agent,
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

    async def __aenter__(self) -> "GitHubClient":
        return self

    async def __aexit__(self, _exc_type, _exc, _tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        return await self._request("GET", f"/repos/{owner}/{repo}")

    async def get_ref(self, owner: str, repo: str, ref: str) -> dict[str, Any]:
        return await self._request("GET", f"/repos/{owner}/{repo}/git/ref/{ref}")

    async def create_ref(self, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/refs",
            json={"ref": ref, "sha": sha},
        )

    async def get_commit(self, owner: str, repo: str, sha: str) -> dict[str, Any]:
        return await self._request("GET", f"/repos/{owner}/{repo}/git/commits/{sha}")

    async def create_blob(self, owner: str, repo: str, file: PublishFile) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/blobs",
            json={"content": file.content, "encoding": file.encoding},
        )

    async def create_tree(
        self,
        owner: str,
        repo: str,
        *,
        base_tree: str,
        tree: Sequence[dict[str, Any]],
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/trees",
            json={"base_tree": base_tree, "tree": list(tree)},
        )

    async def create_commit(
        self,
        owner: str,
        repo: str,
        *,
        message: str,
        tree_sha: str,
        parent_shas: Sequence[str],
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/git/commits",
            json={"message": message, "tree": tree_sha, "parents": list(parent_shas)},
        )

    async def update_ref(self, owner: str, repo: str, ref: str, sha: str) -> dict[str, Any]:
        return await self._request(
            "PATCH",
            f"/repos/{owner}/{repo}/git/refs/{ref}",
            json={"sha": sha, "force": False},
        )

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        *,
        title: str,
        head: str,
        base: str,
        body: str | None,
        draft: bool,
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            f"/repos/{owner}/{repo}/pulls",
            json={"title": title, "head": head, "base": base, "body": body or "", "draft": draft},
        )

    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        *,
        head: str,
        base: str,
        state: str = "open",
    ) -> list[dict[str, Any]]:
        payload = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/pulls",
            params={"head": head, "base": base, "state": state},
        )
        if isinstance(payload, list):
            return payload
        return []

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        try:
            response = await self._client.request(method, path, json=json, params=params)
        except httpx.HTTPError as exc:
            raise GitHubPublishError(
                GitHubPublishErrorCode.GITHUB_API_ERROR,
                f"GitHub API request failed: {exc}",
                details={"method": method, "path": path},
            ) from exc

        if 200 <= response.status_code < 300:
            if response.content:
                return response.json()
            return {}

        details = _response_details(response)
        if response.status_code in (401, 403):
            raise GitHubPublishError(
                GitHubPublishErrorCode.AUTH_FAILED,
                "GitHub authentication or authorization failed.",
                status_code=response.status_code,
                details=details,
            )

        raise GitHubPublishError(
            GitHubPublishErrorCode.GITHUB_API_ERROR,
            _response_message(details),
            status_code=response.status_code,
            details=details,
        )


def _response_details(response: httpx.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return {"message": response.text[:500]}


def _response_message(details: Any) -> str:
    if isinstance(details, dict):
        message = details.get("message")
        if message:
            return str(message)
    return "GitHub API request failed."
