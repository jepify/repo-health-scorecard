import re
from datetime import UTC, datetime
from typing import Any, Self

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


class Contributor(BaseModel):
    """A single contributor to a repository and how much they have contributed.

    ``contributions`` is the number of commits GitHub attributes to this user,
    as reported by the REST contributors endpoint.
    """

    login: str
    github_id: int
    profile_url: str
    contributions: int

    @classmethod
    def parse(cls, payload: dict[str, Any]) -> Self:
        """Parse a contributor from a GitHub REST API payload (parse, don't validate)."""
        return cls(
            login=payload["login"],
            github_id=payload["id"],
            profile_url=payload["html_url"],
            contributions=payload["contributions"],
        )


class RepositoryContributions(BaseModel):
    """The set of contributors to a repository, with convenience aggregates.

    Contributors are ordered by commit count, descending, matching the order
    returned by the GitHub REST API.
    """

    contributors: list[Contributor]

    @property
    def contributor_count(self) -> int:
        """How many distinct contributors the repository has."""
        return len(self.contributors)

    @property
    def total_contributions(self) -> int:
        """The sum of every contributor's commit count."""
        return sum(contributor.contributions for contributor in self.contributors)

    @property
    def top_contributor(self) -> Contributor | None:
        """The single most active contributor, or ``None`` if there are none."""
        if not self.contributors:
            return None
        return max(self.contributors, key=lambda contributor: contributor.contributions)


class ContributorWeek(BaseModel):
    """A single week of a contributor's activity (from ``/stats/contributors``)."""

    week_start: datetime  # 'w' — start of the week, UTC
    commits: int  # 'c'
    additions: int  # 'a'
    deletions: int  # 'd'


class ContributorActivity(BaseModel):
    """A contributor's weekly commit history over the life of the repository."""

    login: str
    weeks: list[ContributorWeek]

    @classmethod
    def parse(cls, payload: dict[str, Any]) -> Self:
        """Parse one author's stats from a GitHub REST API payload (parse, don't validate)."""
        return cls(
            login=payload["author"]["login"],
            weeks=[
                ContributorWeek(
                    week_start=datetime.fromtimestamp(week["w"], tz=UTC),
                    commits=week["c"],
                    additions=week["a"],
                    deletions=week["d"],
                )
                for week in payload["weeks"]
            ],
        )

    def commits_since(self, since: datetime) -> int:
        """Total commits in weeks starting on or after ``since``."""
        return sum(week.commits for week in self.weeks if week.week_start >= since)


class RepositoryContributorStats(BaseModel):
    """Per-contributor weekly commit activity (from ``/stats/contributors``).

    Unlike :class:`RepositoryContributions`, this carries timestamps, enabling
    time-windowed analysis such as bus factor over a recent period.
    """

    contributors: list[ContributorActivity]

    def commit_counts_since(self, since: datetime) -> list[int]:
        """Each contributor's commit count since ``since``, descending, excluding zeros."""
        counts = (contributor.commits_since(since) for contributor in self.contributors)
        return sorted((count for count in counts if count > 0), reverse=True)
