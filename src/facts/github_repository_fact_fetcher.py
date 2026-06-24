from typing import Self

from pydantic import BaseModel

from src.facts.github_rest_repository import GitHubRestRepository
from src.facts.raw_repository_repository import RawCodeRepository
from src.models.github import GitHubRepository, RepositoryContributions, RepositoryContributorStats


class GitHubRepositoryFacts(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    repository_name: str
    repository_url: str
    raw_content: RawCodeRepository
    contributions: RepositoryContributions
    contributor_stats: RepositoryContributorStats


class GitHubRepositoryFactFetcherException(Exception):
    pass


class GitHubRepositoryFactFetcher:
    """
    Fetches and aggregates facts about a GitHub repository.

    This class is responsible for gathering all relevant data about a repository,
    including raw content, contributions, and contributor statistics. It must be
    used as a context manager to ensure proper setup and teardown of resources.
    """

    raw_content: RawCodeRepository
    rest_api: GitHubRestRepository

    def __init__(
        self,
        github_repository: GitHubRepository,
        dep_rest_repository: GitHubRestRepository | None = None,
        dep_raw_repository: RawCodeRepository | None = None,
    ) -> None:
        self._github_repository = github_repository
        self.raw_content = dep_raw_repository or RawCodeRepository(github_repository)
        self.rest_api = dep_rest_repository or GitHubRestRepository(github_repository)

        self._github_repository_facts: GitHubRepositoryFacts | None = None

    @property
    def github_repository_facts(self) -> GitHubRepositoryFacts:
        """Returns the aggregated facts about the GitHub repository."""

        if self._github_repository_facts is None:
            raise GitHubRepositoryFactFetcherException("Must be used as a context manager")
        return self._github_repository_facts

    def setup(self) -> Self:
        """Fetches and aggregates facts about the GitHub repository."""

        self.raw_content.setup()
        self.rest_api.setup()

        # Aggregate the fetched facts into a single object for easy access
        self._github_repository_facts = GitHubRepositoryFacts(
            repository_name=f"{self._github_repository.owner}/{self._github_repository.name}",
            repository_url=self._github_repository.clone_url,
            raw_content=self.raw_content,
            contributions=self.rest_api.contributions,
            contributor_stats=self.rest_api.contributor_stats,
        )
        return self

    def teardown(self) -> None:
        self.raw_content.teardown()

    def __enter__(self) -> Self:
        self.setup()
        return self

    def __exit__(self, *_) -> None:
        self.teardown()
