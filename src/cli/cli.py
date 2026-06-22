from datetime import timedelta
from typing import override

from tap import Tap

from src.models.github import GitHubRepository


class ScorecardArgs(Tap):
    """Command line arguments for the repo health scorecard."""

    repo: str  # GitHub repository reference (owner/name, HTTPS or SSH URL).
    window_days: int = 30  # Time window in days to evaluate the repository over.

    @override
    def configure(self) -> None:
        self.add_argument("-r", "--repo")
        self.add_argument("-w", "--window_days")

    @property
    def repository(self) -> GitHubRepository:
        return GitHubRepository.parse(self.repo)

    @property
    def time_window(self) -> timedelta:
        return timedelta(days=self.window_days)
