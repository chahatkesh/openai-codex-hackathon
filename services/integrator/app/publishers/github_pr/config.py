from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.config import settings as app_settings
from app.publishers.github_pr.errors import GitHubPublishError, GitHubPublishErrorCode
from app.publishers.github_pr.schemas import PublishPullRequestRequest, ResolvedRepository, normalize_branch_name


class GitHubPublishingConfig(BaseModel):
    token: str = ""
    api_base_url: str = "https://api.github.com"
    default_owner: str | None = None
    default_repo: str | None = None
    default_base_branch: str | None = None
    branch_prefix: str = "fusekit/publish"
    draft_by_default: bool = True
    user_agent: str = "FuseKit-Integrator/0.1"
    timeout_seconds: float = Field(default=30.0, gt=0)

    @field_validator("default_owner", "default_repo", "default_base_branch", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @field_validator("api_base_url")
    @classmethod
    def normalize_api_base_url(cls, value: str) -> str:
        value = value.strip().rstrip("/")
        return value or "https://api.github.com"

    @field_validator("branch_prefix", "default_base_branch")
    @classmethod
    def validate_branch_parts(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return normalize_branch_name(value)

    @classmethod
    def from_settings(cls) -> "GitHubPublishingConfig":
        return cls(
            token=app_settings.github_token,
            api_base_url=app_settings.github_api_base_url,
            default_owner=app_settings.github_default_owner,
            default_repo=app_settings.github_default_repo,
            default_base_branch=app_settings.github_default_base_branch,
            branch_prefix=app_settings.github_branch_prefix,
            draft_by_default=app_settings.github_draft_prs,
        )

    def require_token(self) -> str:
        if not self.token.strip():
            raise GitHubPublishError(
                GitHubPublishErrorCode.CONFIGURATION_ERROR,
                "GitHub publishing requires GITHUB_TOKEN or an injected GitHub client.",
            )
        return self.token.strip()

    def resolve_repository(self, request: PublishPullRequestRequest) -> ResolvedRepository:
        repo = request.repo
        owner = repo.owner if repo and repo.owner else self.default_owner
        name = repo.name if repo and repo.name else self.default_repo
        base_branch = (
            request.base_branch
            or (repo.base_branch if repo and repo.base_branch else None)
            or self.default_base_branch
        )

        if not owner or not name:
            raise GitHubPublishError(
                GitHubPublishErrorCode.CONFIGURATION_ERROR,
                "GitHub repository owner and name must be provided by payload or configuration.",
            )

        return ResolvedRepository(owner=owner, name=name, base_branch=base_branch)
