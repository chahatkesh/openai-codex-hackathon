from __future__ import annotations

from enum import Enum
from typing import Any


class GitHubPublishErrorCode(str, Enum):
    INVALID_PAYLOAD = "INVALID_PAYLOAD"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    AUTH_FAILED = "AUTH_FAILED"
    BRANCH_CREATION_FAILED = "BRANCH_CREATION_FAILED"
    FILE_CONFLICT = "FILE_CONFLICT"
    PR_CREATION_FAILED = "PR_CREATION_FAILED"
    GITHUB_API_ERROR = "GITHUB_API_ERROR"


class GitHubPublishError(Exception):
    """Typed exception raised by the GitHub PR publishing module."""

    def __init__(
        self,
        code: GitHubPublishErrorCode,
        message: str,
        *,
        status_code: int | None = None,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "code": self.code.value,
            "message": self.message,
        }
        if self.status_code is not None:
            payload["status_code"] = self.status_code
        if self.details is not None:
            payload["details"] = self.details
        return payload
