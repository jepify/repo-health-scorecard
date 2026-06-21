from __future__ import annotations

import re
from typing import Self

from pydantic import BaseModel

_REPO_PATTERN = re.compile(
    r"^(?:https?://github\.com/|ssh://git@github\.com/|git@github\.com:)?"
    r"(?P<owner>[A-Za-z0-9_.-]+)/(?P<name>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


class GitHubRepository(BaseModel):
    """A parsed reference to a GitHub repository.

    Accepts ``owner/name``, an HTTPS URL or an SSH URL and exposes the parts
    needed to clone it. Parse, don't validate: construct via :meth:`parse`.
    """

    owner: str
    name: str

    @classmethod
    def parse(cls, value: str) -> Self:
        match = _REPO_PATTERN.match(value.strip())
        if match is None:
            raise ValueError(f"Not a valid GitHub repository reference: {value!r}")
        return cls(owner=match["owner"], name=match["name"])

    @property
    def clone_url(self) -> str:
        return f"git@github.com:{self.owner}/{self.name}.git"
