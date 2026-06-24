from typing import override

from src.facts.github_repository_fact_fetcher import GitHubRepositoryFacts
from src.metrics.metric import Metric
from src.models.metric_definition import MetricCategory, MetricDefinition, MetricEvaluation, MetricSeverity

DEPENDENCY_MANAGEMENT_METRIC: MetricDefinition = MetricDefinition(
    title="Dependency Management",
    description="Evaluates whether the repository uses"
    "proactive dependency management practices. "
    "Scans for signs of tools like Dependabot and Renovate.",
    implications="Without proactive dependency management, "
    "repositories are more likely to have unpatched vulnerabilities and outdated dependencies,"
    "which can lead to security risks and maintenance issues.",
    remediations="Integrate a proactive dependency management tool like Dependabot or"
    "Renovate to automatically keep dependencies up to date and secure.",
    category=MetricCategory.CODE_QUALITY,
    severity=MetricSeverity.HIGH,
)

# Canonical Dependabot config location.
_DEPENDABOT_PATHS: frozenset[str] = frozenset({
    ".github/dependabot.yml",
    ".github/dependabot.yaml",
})

# Locations Renovate searches for its configuration.
_RENOVATE_PATHS: frozenset[str] = frozenset({
    "renovate.json",
    "renovate.json5",
    ".github/renovate.json",
    ".github/renovate.json5",
    ".gitlab/renovate.json",
    ".gitlab/renovate.json5",
    ".renovaterc",
    ".renovaterc.json",
    ".renovaterc.json5",
})


class DependencyManagementMetricEvaluator(Metric):
    """Evaluates whether the repository uses proactive dependency management practices.
    Specifically liikes for "dependabot" and "renovate"
    """

    definition: MetricDefinition = DEPENDENCY_MANAGEMENT_METRIC

    @override
    def evaluate(self, facts: GitHubRepositoryFacts) -> MetricEvaluation:
        present_paths = {path.as_posix() for path in facts.raw_content.list_files().paths}

        has_dependabot = bool(present_paths & _DEPENDABOT_PATHS)
        has_renovate = bool(present_paths & _RENOVATE_PATHS)

        if has_dependabot or has_renovate:
            score = 10
        else:
            score = 0

        return MetricEvaluation(definition=self.definition, score=score)
