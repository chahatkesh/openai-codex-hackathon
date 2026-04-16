from __future__ import annotations

import re
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


_CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")
_REPO_PART = re.compile(r"^[A-Za-z0-9_.-]+$")
_UNSAFE_BRANCH_CHARS = re.compile(r"[\s~^:?*\[\\]")


class RepositoryRef(BaseModel):
    owner: str | None = None
    name: str | None = None
    base_branch: str | None = None

    @field_validator("owner", "name")
    @classmethod
    def validate_repo_part(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            return None
        if not _REPO_PART.match(value):
            raise ValueError("repository owner and name may only contain letters, numbers, '.', '_', or '-'")
        return value

    @field_validator("base_branch")
    @classmethod
    def validate_base_branch(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return normalize_branch_name(value)


class PublishFile(BaseModel):
    path: str
    content: str
    encoding: Literal["utf-8", "base64"] = "utf-8"
    mode: Literal["100644", "100755"] = "100644"

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        path = value.replace("\\", "/").strip()
        path = re.sub(r"/+", "/", path)
        if not path:
            raise ValueError("file path is required")
        if path.startswith("/") or path.endswith("/"):
            raise ValueError("file path must be relative and point to a file")
        if _CONTROL_CHARS.search(path):
            raise ValueError("file path contains control characters")
        parts = path.split("/")
        if any(part in ("", ".", "..") for part in parts):
            raise ValueError("file path cannot contain empty, '.', or '..' segments")
        return path


class PublishStatus(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    ALREADY_OPEN = "already_open"
    NO_CHANGES = "no_changes"


class PublishPullRequestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    repo: RepositoryRef | None = None
    files: list[PublishFile] = Field(min_length=1)
    title: str | None = None
    body: str | None = None
    commit_message: str | None = None
    base_branch: str | None = None
    branch_name: str | None = None
    branch_prefix: str | None = None
    draft: bool | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    reuse_existing_branch: bool = True
    update_existing_pr: bool = True

    @field_validator("title", "body", "commit_message")
    @classmethod
    def normalize_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        return value or None

    @field_validator("base_branch", "branch_name")
    @classmethod
    def validate_branch(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return normalize_branch_name(value)

    @field_validator("branch_prefix")
    @classmethod
    def validate_branch_prefix(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.removeprefix("refs/heads/").strip().strip("/")
        if not value:
            raise ValueError("branch_prefix cannot be empty")
        return normalize_branch_name(value)

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            return None
        if _CONTROL_CHARS.search(value):
            raise ValueError("idempotency_key contains control characters")
        return value[:80]

    @model_validator(mode="after")
    def validate_unique_paths(self) -> "PublishPullRequestRequest":
        seen: set[str] = set()
        for file in self.files:
            if file.path in seen:
                raise ValueError(f"duplicate file path: {file.path}")
            seen.add(file.path)
        return self


class ResolvedRepository(BaseModel):
    owner: str
    name: str
    base_branch: str | None = None


class BranchState(BaseModel):
    name: str
    commit_sha: str
    tree_sha: str
    created: bool


class CommitResult(BaseModel):
    commit_sha: str
    tree_sha: str
    changed: bool


class PullRequestResult(BaseModel):
    number: int
    url: str
    draft: bool
    existed: bool = False


class PublishPullRequestResult(BaseModel):
    status: PublishStatus
    owner: str
    repo: str
    base_branch: str
    branch_name: str
    pr_url: str | None
    pr_number: int | None = None
    commit_sha: str
    files: list[str]
    metadata: dict[str, Any] = Field(default_factory=dict)


def normalize_branch_name(value: str) -> str:
    branch = value.removeprefix("refs/heads/").strip().strip("/")
    if not branch:
        raise ValueError("branch name cannot be empty")
    if branch.endswith(".lock") or branch.endswith("/"):
        raise ValueError("branch name is not a valid Git ref")
    if branch.startswith(".") or branch.startswith("/"):
        raise ValueError("branch name is not a valid Git ref")
    if ".." in branch or "@{" in branch or _UNSAFE_BRANCH_CHARS.search(branch):
        raise ValueError("branch name is not a valid Git ref")
    return branch
