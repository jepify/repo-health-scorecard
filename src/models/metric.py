from datetime import datetime
from enum import Enum
from typing import Annotated, Protocol

from pydantic import BaseModel, Field

from src.facts.github_repository_fact_fetcher import GitHubRepositoryFacts


class MetricSeverity(Enum):
    """How serious a metric finding is."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MetricCategory(Enum):
    """The kind of concern a metric describes.

    Per ADR 002, code-quality metrics weigh most heavily on overall health.
    """

    METADATA = "metadata"
    CODE_QUALITY = "code_quality"


# Score is bounded 0-10, where higher is better.
MetricScore = Annotated[int, Field(ge=0, le=10)]


class MetricDefinition(BaseModel):
    """The static description of what a metric measures.

    This is metric-author supplied metadata that does not depend on any
    particular repository's facts. Evaluating a metric pairs this definition
    with a :class:`MetricEvaluation`.
    """

    title: str
    description: str
    implications: str
    remediations: str
    category: MetricCategory
    severity: MetricSeverity


class MetricEvaluation(BaseModel):
    """The result of evaluating a metric against a repository's facts."""

    definition: MetricDefinition
    score: MetricScore

    def _weight(self) -> int:
        """How much this metric should influence the overall score."""
        category_weight = {
            MetricCategory.METADATA: 1,
            MetricCategory.CODE_QUALITY: 3,
        }[self.definition.category]
        severity_weight = {
            MetricSeverity.LOW: 1,
            MetricSeverity.MEDIUM: 2,
            MetricSeverity.HIGH: 3,
        }[self.definition.severity]
        return category_weight * severity_weight


class Metric(Protocol):
    """A metric that evaluates a repository's facts against its definition.

    Implementations take the shared, immutable facts and produce a :class:`MetricEvaluation`.
    They must not fetch data themselves (see ADR 001).
    """

    def evaluate(
        self,
        facts: GitHubRepositoryFacts,
    ) -> MetricEvaluation: ...


class ScorecardRepositoryInfo(BaseModel):
    """Basic identifying information about the repository being scored."""

    title: str
    url: str
    commit: str
    generated_at: datetime



class Scorecard(BaseModel):
    """The aggregated result of evaluating every metric against a repository.

    Holds the backing data for a report: basic repository information and the
    list of :class:`MetricEvaluation` results. It also owns the weighted-average
    computation so that the same scorecard can be rendered into multiple formats
    (markdown, json, ...) from a single, consistent source of truth — the
    reporting layer only chooses *how* to present this data, never *what* it is.
    """

    repository: ScorecardRepositoryInfo
    evaluations: list[MetricEvaluation]

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
