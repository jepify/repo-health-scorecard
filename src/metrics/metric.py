from typing import Protocol

from src.facts.github_repository_fact_fetcher import GitHubRepositoryFacts
from src.models.metric_definition import MetricEvaluation


class Metric(Protocol):
    """A metric that evaluates a repository's facts against its definition.

    Implementations take the shared, immutable facts and produce a :class:`MetricEvaluation`.
    They must not fetch data themselves (see ADR 001).
    """

    def evaluate(
        self,
        facts: GitHubRepositoryFacts,
    ) -> MetricEvaluation: ...
