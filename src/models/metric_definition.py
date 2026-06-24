from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field


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
