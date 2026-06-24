from datetime import datetime
from typing import Protocol, override

from pydantic import BaseModel

from src.models.metric_definition import MetricEvaluation


class ScorecardRepositoryInfo(BaseModel):
    """Basic identifying information about the repository being scored."""

    title: str
    url: str
    commit: str
    generated_at: datetime


class Scorecard(Protocol):
    """The aggregated result of evaluating every metric against a repository."""

    repository: ScorecardRepositoryInfo
    evaluations: list[MetricEvaluation]

    def overall_score(self) -> float: ...


class WeightedAverageScorecard(Scorecard):
    """The aggregated result of evaluating every metric against a repository.

    The overall score is a weighted average of every metric's score.
    """

    repository: ScorecardRepositoryInfo
    evaluations: list[MetricEvaluation]

    def __init__(self, repository: ScorecardRepositoryInfo, evaluations: list[MetricEvaluation]) -> None:
        self.repository = repository
        self.evaluations = evaluations

    @override
    def overall_score(self) -> float:
        """The overall health score: a weighted average of every metric's score.

        Each evaluation contributes proportionally to its own weight (category
        and severity, per ADR 002). Returns ``0.0`` when there are no metrics.
        """

        total_weight = sum(evaluation._weight() for evaluation in self.evaluations)
        if total_weight == 0:
            return 0.0
        weighted_total = sum(evaluation.score * evaluation._weight() for evaluation in self.evaluations)
        return weighted_total / total_weight
