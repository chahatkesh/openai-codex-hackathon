from __future__ import annotations

from typing import Any

import pytest

from app.publishers.github_pr import (
    AgentSkillsMarkdownRenderer,
    AgentSkillsMarkdownSource,
    GitHubPublishError,
    GitHubPublishErrorCode,
    GitHubPublishingConfig,
    PublishStatus,
    publish_via_pull_request,
)
from app.publishers.github_pr.schemas import PublishFile


class FakeGitHubClient:
    def __init__(self) -> None:
        self.refs = {"heads/main": "base-sha"}
        self.commits = {
            "base-sha": {"sha": "base-sha", "tree": {"sha": "base-tree"}},
        }
        self.pulls: list[dict[str, Any]] = []
        self.created_refs: list[dict[str, str]] = []
        self.created_blobs: list[PublishFile] = []
        self.created_trees: list[dict[str, Any]] = []
        self.created_commits: list[dict[str, Any]] = []
        self.updated_refs: list[dict[str, str]] = []
        self.created_pull_requests: list[dict[str, Any]] = []
        self.tree_sha = "tree-1"
        self.create_pr_error: GitHubPublishError | None = None
        self.update_ref_error: GitHubPublishError | None = None

    async def get_repository(self, owner: str, repo: str) -> dict[str, Any]:
        return {"default_branch": "main", "full_name": f"{owner}/{repo}"}

    async def get_ref(self, _owner: str, _repo: str, ref: str) -> dict[str, Any]:
        sha = self.refs[ref]
        return {"ref": f"refs/{ref}", "object": {"sha": sha}}

    async def create_ref(self, _owner: str, _repo: str, ref: str, sha: str) -> dict[str, Any]:
        normalized_ref = ref.removeprefix("refs/")
        if normalized_ref in self.refs:
            raise GitHubPublishError(
                GitHubPublishErrorCode.GITHUB_API_ERROR,
                "Reference already exists",
                status_code=422,
                details={"message": "Reference already exists"},
            )
        self.refs[normalized_ref] = sha
        self.created_refs.append({"ref": ref, "sha": sha})
        return {"ref": ref, "object": {"sha": sha}}

    async def get_commit(self, _owner: str, _repo: str, sha: str) -> dict[str, Any]:
        return self.commits[sha]

    async def create_blob(self, _owner: str, _repo: str, file: PublishFile) -> dict[str, Any]:
        self.created_blobs.append(file)
        return {"sha": f"blob-{len(self.created_blobs)}"}

    async def create_tree(
        self,
        _owner: str,
        _repo: str,
        *,
        base_tree: str,
        tree: list[dict[str, Any]],
    ) -> dict[str, Any]:
        self.created_trees.append({"base_tree": base_tree, "tree": tree})
        return {"sha": self.tree_sha}

    async def create_commit(
        self,
        _owner: str,
        _repo: str,
        *,
        message: str,
        tree_sha: str,
        parent_shas: list[str],
    ) -> dict[str, Any]:
        sha = f"commit-{len(self.created_commits) + 1}"
        self.created_commits.append(
            {"message": message, "tree_sha": tree_sha, "parent_shas": parent_shas, "sha": sha}
        )
        self.commits[sha] = {"sha": sha, "tree": {"sha": tree_sha}}
        return {"sha": sha}

    async def update_ref(self, _owner: str, _repo: str, ref: str, sha: str) -> dict[str, Any]:
        if self.update_ref_error:
            raise self.update_ref_error
        self.refs[ref] = sha
        self.updated_refs.append({"ref": ref, "sha": sha})
        return {"ref": f"refs/{ref}", "object": {"sha": sha}}

    async def create_pull_request(
        self,
        _owner: str,
        _repo: str,
        *,
        title: str,
        head: str,
        base: str,
        body: str | None,
        draft: bool,
    ) -> dict[str, Any]:
        if self.create_pr_error:
            raise self.create_pr_error
        payload = {
            "number": len(self.created_pull_requests) + 1,
            "html_url": f"https://github.test/fusekit/marketplace/pull/{len(self.created_pull_requests) + 1}",
            "draft": draft,
            "title": title,
            "head": head,
            "base": base,
            "body": body,
        }
        self.created_pull_requests.append(payload)
        return payload

    async def list_pull_requests(
        self,
        _owner: str,
        _repo: str,
        *,
        head: str,
        base: str,
        state: str = "open",
    ) -> list[dict[str, Any]]:
        return [
            pull
            for pull in self.pulls
            if pull.get("head") == head and pull.get("base") == base and pull.get("state", "open") == state
        ]


def _config() -> GitHubPublishingConfig:
    return GitHubPublishingConfig(
        token="test-token",
        default_owner="fusekit",
        default_repo="marketplace",
        branch_prefix="fusekit/publish",
    )


@pytest.mark.asyncio
async def test_publish_via_pull_request_creates_branch_commit_and_draft_pr():
    client = FakeGitHubClient()

    result = await publish_via_pull_request(
        {
            "files": [
                {"path": "kits/slack/agent.skills.md", "content": "# Slack"},
                {"path": "kits/slack/README.md", "content": "Slack toolkit"},
            ],
            "title": "Publish Slack kit",
            "body": "Generated Slack kit.",
            "commit_message": "Publish Slack kit",
            "metadata": {"tool_name": "slack"},
            "idempotency_key": "job-123",
        },
        client=client,
        config=_config(),
    )

    assert result.status == PublishStatus.CREATED
    assert result.branch_name == "fusekit/publish/slack-job-123"
    assert result.pr_url == "https://github.test/fusekit/marketplace/pull/1"
    assert result.commit_sha == "commit-1"
    assert result.files == ["kits/slack/agent.skills.md", "kits/slack/README.md"]
    assert client.created_refs == [
        {"ref": "refs/heads/fusekit/publish/slack-job-123", "sha": "base-sha"}
    ]
    assert [entry["path"] for entry in client.created_trees[0]["tree"]] == [
        "kits/slack/agent.skills.md",
        "kits/slack/README.md",
    ]
    assert client.created_pull_requests[0]["draft"] is True


@pytest.mark.asyncio
async def test_publish_rejects_invalid_payload():
    with pytest.raises(GitHubPublishError) as raised:
        await publish_via_pull_request(
            {
                "files": [{"path": "../agent.skills.md", "content": "# Nope"}],
                "metadata": {"tool_name": "bad"},
            },
            client=FakeGitHubClient(),
            config=_config(),
        )

    assert raised.value.code == GitHubPublishErrorCode.INVALID_PAYLOAD


@pytest.mark.asyncio
async def test_publish_rejects_direct_base_branch_writes():
    with pytest.raises(GitHubPublishError) as raised:
        await publish_via_pull_request(
            {
                "repo": {"base_branch": "main"},
                "branch_name": "main",
                "files": [{"path": "kits/slack/agent.skills.md", "content": "# Slack"}],
                "metadata": {"tool_name": "slack"},
            },
            client=FakeGitHubClient(),
            config=_config(),
        )

    assert raised.value.code == GitHubPublishErrorCode.INVALID_PAYLOAD


@pytest.mark.asyncio
async def test_publish_reuses_existing_branch_and_existing_pr_for_idempotent_retry():
    client = FakeGitHubClient()
    client.refs["heads/fusekit/publish/slack-job-123"] = "old-sha"
    client.commits["old-sha"] = {"sha": "old-sha", "tree": {"sha": "old-tree"}}
    client.pulls.append(
        {
            "number": 7,
            "html_url": "https://github.test/fusekit/marketplace/pull/7",
            "draft": True,
            "head": "fusekit:fusekit/publish/slack-job-123",
            "base": "main",
            "state": "open",
        }
    )

    result = await publish_via_pull_request(
        {
            "files": [{"path": "kits/slack/agent.skills.md", "content": "# Slack v2"}],
            "metadata": {"tool_name": "slack"},
            "idempotency_key": "job-123",
        },
        client=client,
        config=_config(),
    )

    assert result.status == PublishStatus.UPDATED
    assert result.pr_url == "https://github.test/fusekit/marketplace/pull/7"
    assert result.commit_sha == "commit-1"
    assert client.created_pull_requests == []
    assert client.created_trees[0]["base_tree"] == "old-tree"


@pytest.mark.asyncio
async def test_publish_maps_branch_update_conflict_to_file_conflict():
    client = FakeGitHubClient()
    client.update_ref_error = GitHubPublishError(
        GitHubPublishErrorCode.GITHUB_API_ERROR,
        "Update is not a fast-forward",
        status_code=409,
        details={"message": "Update is not a fast-forward"},
    )

    with pytest.raises(GitHubPublishError) as raised:
        await publish_via_pull_request(
            {
                "files": [{"path": "kits/slack/agent.skills.md", "content": "# Slack"}],
                "metadata": {"tool_name": "slack"},
                "idempotency_key": "job-123",
            },
            client=client,
            config=_config(),
        )

    assert raised.value.code == GitHubPublishErrorCode.FILE_CONFLICT


@pytest.mark.asyncio
async def test_publish_maps_pull_request_failure():
    client = FakeGitHubClient()
    client.create_pr_error = GitHubPublishError(
        GitHubPublishErrorCode.GITHUB_API_ERROR,
        "GitHub unavailable",
        status_code=500,
        details={"message": "GitHub unavailable"},
    )

    with pytest.raises(GitHubPublishError) as raised:
        await publish_via_pull_request(
            {
                "files": [{"path": "kits/slack/agent.skills.md", "content": "# Slack"}],
                "metadata": {"tool_name": "slack"},
                "idempotency_key": "job-123",
            },
            client=client,
            config=_config(),
        )

    assert raised.value.code == GitHubPublishErrorCode.PR_CREATION_FAILED


def test_agent_skills_renderer_builds_standard_marketplace_path():
    renderer = AgentSkillsMarkdownRenderer()

    files = renderer.render(AgentSkillsMarkdownSource(kit_slug="Slack API", content="# Slack"))

    assert len(files) == 1
    assert files[0].path == "kits/slack-api/agent.skills.md"
    assert files[0].content == "# Slack"
