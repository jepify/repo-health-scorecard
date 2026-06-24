from typing import Self

from src.facts.github_api_client import DefaultGitHubAPIClient, GitHubAPIClient
from src.models.github import (
    Contributor,
    ContributorActivity,
    GitHubRepository,
    RepositoryContributions,
    RepositoryContributorStats,
)

# GitHub caps list endpoints at 100 items per page; use the max to minimise calls.
_MAX_PER_PAGE = "100"


class GitHubRestRepository:
    """Gathers repository facts from the GitHub REST API (see ADR 001).

    Acts as a facade over :class:`GitHubAPIClient`.s

    On :meth:`setup` it fetches every contributor (all-time counts) and their
    weekly commit activity, exposing them as typed facts. Metrics never call this
    directly; they consume the facts it contributes.
    """

    def __init__(
        self,
        repository: GitHubRepository,
        dep_api_client: GitHubAPIClient | None = None,
    ) -> None:
        self._repository = repository
        # The network call is the side-effectful step; inject a fake to test.
        self._api_client = dep_api_client or DefaultGitHubAPIClient()
        self._contributions: RepositoryContributions | None = None
        self._contributor_stats: RepositoryContributorStats | None = None

    @property
    def contributions(self) -> RepositoryContributions:
        if self._contributions is None:
            raise RuntimeError("Repository is not set up. Call setup() first.")
        return self._contributions

    @property
    def contributor_stats(self) -> RepositoryContributorStats:
        if self._contributor_stats is None:
            raise RuntimeError("Repository is not set up. Call setup() first.")
        return self._contributor_stats

    def setup(self) -> Self:
        """Fetch contributor counts and weekly commit stats from the REST API."""

        if self._contributions is not None and self._contributor_stats is not None:
            return self

        self._contributions = self.get_repo_contributers()
        print(f"Found {self._contributions.contributor_count} contributors")

        self._contributor_stats = self.get_repo_contributor_stats()
        print(f"Loaded weekly stats for {len(self._contributor_stats.contributors)} contributors")

        return self

    def get_repo_contributers(self) -> RepositoryContributions:
        """Returns repository contributors from the GitHub REST API."""

        owner, name = self._repository.owner, self._repository.name
        print(f"Fetching contributors for {owner}/{name} from the GitHub REST API")
        contributor_payloads = self._api_client.get_collection(
            f"/repos/{owner}/{name}/contributors",
            {"per_page": _MAX_PER_PAGE, "anon": "true"},
        )
        return RepositoryContributions(
            contributors=[Contributor.parse(payload) for payload in contributor_payloads],
        )

    def get_repo_contributor_stats(self) -> RepositoryContributorStats:
        """Returns repository contributor stats from the GitHub REST API."""

        owner, name = self._repository.owner, self._repository.name
        print(f"Fetching weekly commit stats for {owner}/{name} from the GitHub REST API")
        stats_payloads = self._api_client.get_computed_collection(
            f"/repos/{owner}/{name}/stats/contributors",
        )
        return RepositoryContributorStats(
            contributors=[ContributorActivity.parse(payload) for payload in stats_payloads],
        )
