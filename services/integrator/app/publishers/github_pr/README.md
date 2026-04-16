# GitHub PR Publisher

Reusable internal module for publishing generated files to a GitHub repository through draft pull requests.

```python
from app.publishers.github_pr import publish_via_pull_request


result = await publish_via_pull_request(
    {
        "repo": {"owner": "fusekit", "name": "marketplace", "base_branch": "main"},
        "files": [
            {
                "path": "kits/slack/agent.skills.md",
                "content": generated_agent_skills_markdown,
            }
        ],
        "title": "Publish Slack kit",
        "commit_message": "Publish Slack kit",
        "metadata": {"tool_name": "slack"},
        "idempotency_key": str(job.id),
    }
)
```

Key guarantees:

- Creates a branch from the base/default branch.
- Writes all files in one commit.
- Opens a draft PR by default.
- Does not write directly to the base branch.
- Supports idempotent retries with `idempotency_key`.
- Returns branch name, PR URL, commit SHA, files, metadata, and status.

Full developer documentation: `docs/github-pr-publishing.md`.
