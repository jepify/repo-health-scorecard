from typing import override

from src.models.metric import MetricEvaluation, Scorecard
from src.reporting.report import GenerateReport


class MarkdownReport(GenerateReport):
    """Renders a :class:`Scorecard` as a Markdown document.

    A concrete :class:`GenerateReport` strategy. It only formats the scorecard's
    backing data; the overall score and weights come from the scorecard itself.
    """

    @override
    def generate(self, scorecard: Scorecard) -> str:
        sections = [
            "# Repo Score Card",
            self._repository_section(scorecard),
            self._overall_score_section(scorecard),
            self._metrics_section(scorecard),
        ]
        return "\n\n".join(sections) + "\n"

    def _repository_section(self, scorecard: Scorecard) -> str:
        repository = scorecard.repository
        return "\n".join([
            "## Repository",
            "",
            f"- **Repository:** [{repository.title}](https://github.com/{repository.title})",
            f"- **URL:** {repository.url}",
            f"- **Commit:** {repository.commit}",
            f"- **Generated at:** {repository.generated_at.isoformat()}",
        ])

    def _overall_score_section(self, scorecard: Scorecard) -> str:
        return "\n".join([
            "## Overall Score",
            "",
            f"**{scorecard.overall_score():.1f} / 10** (weighted average across all metrics)",
        ])

    def _metrics_section(self, scorecard: Scorecard) -> str:
        lines = ["## Metrics"]
        for evaluation in scorecard.evaluations:
            lines.append("")
            lines.append(self._metric_entry(evaluation))
        return "\n".join(lines)

    def _metric_entry(self, evaluation: MetricEvaluation) -> str:
        definition = evaluation.definition
        return "\n".join([
            f"### {definition.title} — {evaluation.score} / 10",
            "",
            f"- **Category:** {definition.category.value}",
            f"- **Severity:** {definition.severity.value}",
            f"- **Description:** {definition.description}",
            f"- **Implications:** {definition.implications}",
            f"- **Remediations:** {definition.remediations}",
        ])
