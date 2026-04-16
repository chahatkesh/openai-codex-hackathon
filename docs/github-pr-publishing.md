# GitHub PR Publishing

## Purpose

The GitHub PR publishing module is an internal FuseKit capability for safely publishing generated marketplace files into a GitHub-backed repository. It is designed for generated `agent.skills.md` kits, but it is intentionally generic: callers provide one or more repository files and the module creates a branch, commits all files together, and opens a draft pull request.

The module does not write directly to `main` or any configured base branch.

## Location

Implementation lives in:

`services/integrator/app/publishers/github_pr/`

The integrator owns this module because the repository architecture assigns discovery, codegen, test/fix, and publish stages to `services/integrator`.

## High-Level Architecture

- `client.py`: async GitHub REST client using `httpx`.
- `config.py`: config object and environment-backed defaults.
- `schemas.py`: Pydantic request, file, repository, and result models.
- `errors.py`: typed errors with stable error codes.
- `branches.py`: default branch resolution and publish branch creation.
- `files.py`: blob, tree, commit, and ref-update operations for multi-file commits.
- `pull_requests.py`: draft pull request creation and existing PR lookup.
- `renderers.py`: file renderer protocol plus `AgentSkillsMarkdownRenderer`.
- `service.py`: high-level orchestration and public `publish_via_pull_request(...)` function.

## Data Flow

1. Caller passes a payload with repository target, files, PR text, commit text, and metadata.
2. Payload is validated and file paths are normalized.
3. Repository owner/name/base branch are resolved from payload first, then config.
4. The base branch SHA and tree SHA are loaded from GitHub.
5. A publish branch is created from the base branch.
6. Each file is uploaded as a Git blob.
7. A single Git tree is created with all file changes.
8. A single commit is created and the publish branch ref is updated without force.
9. A draft PR is opened against the base branch.
10. A structured result is returned with branch name, PR URL, commit SHA, files, and status.

## Public API

```python
async def publish_via_pull_request(
    payload: PublishPullRequestRequest | Mapping[str, Any],
    *,
    client: GitHubClientProtocol | None = None,
    config: GitHubPublishingConfig | None = None,
    event_hook: Callable[[dict[str, Any]], None] | None = None,
) -> PublishPullRequestResult:
    ...
```

Primary payload shape:

```python
{
    "repo": {
        "owner": "fusekit",
        "name": "marketplace",
        "base_branch": "main",
    },
    "files": [
        {
            "path": "kits/slack/agent.skills.md",
            "content": "# Slack\n...",
        }
    ],
    "title": "Publish Slack kit",
    "body": "Generated Slack agent skills kit.",
    "commit_message": "Publish Slack kit",
    "metadata": {
        "tool_name": "slack",
        "source": "integrator",
    },
    "idempotency_key": "integration-job-uuid",
}
```

Result shape:

```python
{
    "status": "created",
    "owner": "fusekit",
    "repo": "marketplace",
    "base_branch": "main",
    "branch_name": "fusekit/publish/slack-integration-job-uuid",
    "pr_url": "https://github.com/fusekit/marketplace/pull/123",
    "pr_number": 123,
    "commit_sha": "abc123...",
    "files": ["kits/slack/agent.skills.md"],
    "metadata": {"tool_name": "slack", "source": "integrator"},
}
```

Possible statuses:

- `created`: new branch/commit/PR created.
- `updated`: existing branch or existing PR was reused and updated.
- `already_open`: no file changes were needed and an open PR already exists.
- `no_changes`: no file changes were needed and no PR was opened.

## Example Usage

```python
from app.publishers.github_pr import publish_via_pull_request


result = await publish_via_pull_request(
    {
        "repo": {"owner": "fusekit", "name": "marketplace", "base_branch": "main"},
        "files": [
            {
                "path": "kits/resend/agent.skills.md",
                "content": generated_agent_skills_markdown,
            },
            {
                "path": "kits/resend/README.md",
                "content": generated_readme,
            },
        ],
        "title": "Publish Resend kit",
        "body": "Generated kit from the FuseKit integration pipeline.",
        "commit_message": "Publish Resend kit",
        "metadata": {"tool_name": "resend", "source": "integrator"},
        "idempotency_key": str(job.id),
    }
)

print(result.pr_url)
```

## Agent Skills Renderer Example

Use the renderer when another stage has domain data rather than repository files:

```python
from app.publishers.github_pr import (
    AgentSkillsMarkdownRenderer,
    AgentSkillsMarkdownSource,
    publish_via_pull_request,
)


renderer = AgentSkillsMarkdownRenderer(root_path="kits")
files = renderer.render(
    AgentSkillsMarkdownSource(
        kit_slug="resend",
        content=generated_agent_skills_markdown,
    )
)

result = await publish_via_pull_request(
    {
        "files": files,
        "title": "Publish Resend kit",
        "metadata": {"tool_name": "resend"},
        "idempotency_key": str(job.id),
    }
)
```

## Configuration

Callers can pass `GitHubPublishingConfig` explicitly, or rely on environment-backed settings from `services/integrator/app/config.py`.

```python
from app.publishers.github_pr import GitHubPublishingConfig, publish_via_pull_request


config = GitHubPublishingConfig(
    token="...",
    default_owner="fusekit",
    default_repo="marketplace",
    default_base_branch="main",
    branch_prefix="fusekit/publish",
    draft_by_default=True,
)

result = await publish_via_pull_request(payload, config=config)
```

## Environment Variables

- `GITHUB_TOKEN`: GitHub token with repository contents and pull request permissions.
- `GITHUB_API_BASE_URL`: optional, defaults to `https://api.github.com`.
- `GITHUB_DEFAULT_OWNER`: optional default repository owner.
- `GITHUB_DEFAULT_REPO`: optional default repository name.
- `GITHUB_DEFAULT_BASE_BRANCH`: optional default base branch. If omitted, GitHub repository `default_branch` is used.
- `GITHUB_BRANCH_PREFIX`: optional, defaults to `fusekit/publish`.
- `GITHUB_DRAFT_PRS`: optional boolean, defaults to `true`.

Recommended GitHub App/token permissions:

- Contents: read/write.
- Pull requests: read/write.
- Metadata: read.

## Error Handling

All module-raised failures use `GitHubPublishError` with a stable `code`.

- `INVALID_PAYLOAD`: malformed request, unsafe path, duplicate file path, invalid branch name, or attempt to publish to the base branch.
- `CONFIGURATION_ERROR`: missing repository owner/name or missing token when no client is injected.
- `AUTH_FAILED`: GitHub returned 401 or 403.
- `BRANCH_CREATION_FAILED`: base branch resolution or publish branch creation failed.
- `FILE_CONFLICT`: branch ref update was rejected, usually because the branch head changed during publishing.
- `PR_CREATION_FAILED`: pull request creation failed or GitHub returned an unexpected PR payload.
- `GITHUB_API_ERROR`: lower-level GitHub API or transport failure.

Example:

```python
from app.publishers.github_pr import GitHubPublishError


try:
    result = await publish_via_pull_request(payload)
except GitHubPublishError as exc:
    logger.warning("github_publish_failed extra=%s", exc.to_dict())
    raise
```

## Idempotency

Pass `idempotency_key` for retryable jobs. The generated branch name includes this key, so a retry for the same integration job targets the same branch. By default:

- `reuse_existing_branch=True`
- `update_existing_pr=True`

If the branch already exists, the module reuses it instead of creating another branch. If an open PR already exists for that branch/base pair, it returns that PR rather than opening a duplicate.

## Extension Points

### New File Renderers

Implement the `FileRenderer` protocol:

```python
from collections.abc import Sequence
from typing import Any

from app.publishers.github_pr import FileRenderer, PublishFile


class OpenApiRenderer(FileRenderer):
    def render(self, source: Any) -> Sequence[PublishFile]:
        return [
            PublishFile(
                path=f"openapi/{source.slug}/openapi.yaml",
                content=source.yaml,
            )
        ]
```

Then pass rendered files into `publish_via_pull_request(...)`.

### Custom GitHub Client

Tests and future workers can inject any object implementing `GitHubClientProtocol`. This is useful for dry runs, integration tests, GitHub Enterprise adapters, or queue workers that own connection lifecycle.

### Observability Hook

Pass `event_hook` to receive simple event dictionaries for publish start and completion:

```python
events = []
result = await publish_via_pull_request(payload, event_hook=events.append)
```

The module also logs through `fusekit.integrator.github_publish`.

## Why PR-Based Publishing

Generated marketplace files should be reviewed before they become canonical. Draft PR publishing gives FuseKit:

- No direct writes to `main`.
- Human review and CI before merge.
- A clear audit trail for generated content.
- Safe retries through deterministic branch names.
- A natural place to discuss generated kit quality, docs, and security concerns.
