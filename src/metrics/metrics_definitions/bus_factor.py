from datetime import datetime
from typing import override

from src.facts.github_repository_fact_fetcher import GitHubRepositoryFacts
from src.models.metric import Metric, MetricCategory, MetricDefinition, MetricEvaluation, MetricSeverity

BUS_FACTOR_METRIC: MetricDefinition = MetricDefinition(
    title="Bus Factor",
    description=(
        "Measures how concentrated recent commit activity is among contributors. "
        "A low bus factor means a small number of people account for most of the "
        "work within the evaluated window."
        "Scored by counting how many contributors it takes to account for 80% of commits"
        "1 contributor = 0 score, 2-3 contributors = 2 score, 4-5 contributors = 4 score, "
        "6-7 contributors = 6 score, 8 contributors = 8 score, 9+ contributors = 10 score."
    ),
    implications=(
        "If only one or two people produce most commits, the project is highly "
        "exposed: losing them stalls development and erases undocumented knowledge."
    ),
    remediations=("Spread ownership and knowledge through code review, pairing, documentation, and by onboarding additional regular contributors."),
    category=MetricCategory.METADATA,
    severity=MetricSeverity.HIGH,
)

# Share of commits that defines the "core" set of contributors.
_DOMINANCE_THRESHOLD = 0.8


class BusFactorMetricEvaluator(Metric):
    """Scores how many contributors it takes to account for 80% of recent commits.

    Only commits on or after ``contributions_since`` are counted, so the score
    reflects a recent window (e.g. the last 90 days) rather than all of history.
    """

    definition: MetricDefinition = BUS_FACTOR_METRIC

    def __init__(self, contributions_since: datetime) -> None:
        self._contributions_since = contributions_since

    @override
    def evaluate(self, facts: GitHubRepositoryFacts) -> MetricEvaluation:
        commit_counts = facts.contributor_stats.commit_counts_since(self._contributions_since)
        bus_factor = self._bus_factor(commit_counts)
        return MetricEvaluation(definition=self.definition, score=self._score(bus_factor))

    def _bus_factor(self, commit_counts: list[int]) -> int:
        """How many top contributors are needed to first exceed 80% of all commits.

        ``commit_counts`` is expected sorted descending. Accumulates commits from
        the most active contributor down until the running total crosses the
        threshold, then returns how many contributors that took.
        """
        total = sum(commit_counts)
        if total == 0:
            return 0

        threshold = total * _DOMINANCE_THRESHOLD
        accumulated = 0
        contributors_needed = 0
        for count in commit_counts:
            accumulated += count
            contributors_needed += 1
            if accumulated >= threshold:
                break
        return contributors_needed

    def _score(self, bus_factor: int) -> int:
        """Map the bus factor to a 0-10 score (more shared ownership scores higher)."""
        if bus_factor <= 1:
            return 0
        if bus_factor <= 3:
            return 2
        if bus_factor <= 5:
            return 4
        if bus_factor <= 7:
            return 6
        if bus_factor <= 8:
            return 8
        return 10
