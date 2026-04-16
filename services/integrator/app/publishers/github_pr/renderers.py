from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from app.publishers.github_pr.schemas import PublishFile


class FileRenderer(Protocol):
    """Interface for converting domain objects into publishable repository files."""

    def render(self, source: Any) -> Sequence[PublishFile]:
        ...


@dataclass(frozen=True)
class AgentSkillsMarkdownSource:
    kit_slug: str
    content: str
    directory: str | None = None


class AgentSkillsMarkdownRenderer:
    """Example renderer for generated agent.skills.md marketplace kits."""

    def __init__(self, *, root_path: str = "kits", filename: str = "agent.skills.md") -> None:
        self.root_path = root_path.strip("/")
        self.filename = filename

    def render(self, source: AgentSkillsMarkdownSource | Mapping[str, Any]) -> list[PublishFile]:
        if isinstance(source, Mapping):
            kit_slug = str(source["kit_slug"])
            content = str(source["content"])
            directory = source.get("directory")
        else:
            kit_slug = source.kit_slug
            content = source.content
            directory = source.directory

        directory_part = str(directory).strip("/") if directory else _slugify_path_part(kit_slug)
        path = f"{self.root_path}/{directory_part}/{self.filename}" if self.root_path else f"{directory_part}/{self.filename}"
        return [PublishFile(path=path, content=content)]


def _slugify_path_part(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", value.strip().lower())
    slug = slug.strip("-._")
    return slug or "generated-kit"
