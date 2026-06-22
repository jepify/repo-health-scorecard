from datetime import datetime

from src.facts.github_repository_fact_fetcher import GitHubRepositoryFacts
from src.metrics.metrics_definitions.bus_factor import BusFactorMetricEvaluator
from src.metrics.metrics_definitions.dependency_management import DependencyManagementMetricEvaluator
from src.models.metric import Metric, MetricEvaluation


class MetricEvaluator:
    """Evaluates a set of metrics against a repository's facts to produce list of metric evaluations.
    Responsible for collecting and orchestrating the evaluation of all metrics.
    Could be the place where we load metrics from config or from an external source.
    """

    def __init__(self, evaluation_since: datetime) -> None:
        # The window bounds time-sensitive metrics (e.g. bus factor).
        self._evaluation_since = evaluation_since

    def _metrics(self) -> list[Metric]:
        return [
            DependencyManagementMetricEvaluator(),
            BusFactorMetricEvaluator(self._evaluation_since),
        ]

    def evaluate(
        self,
        facts: GitHubRepositoryFacts,
    ) -> list[MetricEvaluation]:
        """Generates all metrics for a repository."""
        evaluations = []
        for metric in self._metrics():
            evaluations.append(metric.evaluate(facts))
        return evaluations
