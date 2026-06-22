from datetime import UTC, datetime

from src.cli.cli import ScorecardArgs
from src.facts.github_repository_fact_fetcher import GitHubRepositoryFactFetcher
from src.metrics.metrics_evaluator import MetricEvaluator
from src.models.metric import Scorecard, ScorecardRepositoryInfo
from src.reporting.markdown import MarkdownReport


def main(args: ScorecardArgs) -> None:
    """Entry point for running the module directly (not recommended)."""
    print("Scanning repository")

    evaluation_since = datetime.now(UTC) - args.time_window

    # Per ADR 001: gather facts first, then evaluate metrics against those
    # shared facts. Metrics never fetch data themselves.
    try:
        with GitHubRepositoryFactFetcher(args.repository) as fact_runner:
            facts = fact_runner.github_repository_facts
            print("Repository URL:", facts.repository_url)

            evaluations = MetricEvaluator(evaluation_since).evaluate(facts)

            scorecard = Scorecard(
                repository=ScorecardRepositoryInfo(
                    title=facts.repository_name,
                    url=facts.repository_url,
                    commit=facts.raw_content.commit_sha,
                    generated_at=datetime.now(),
                ),
                evaluations=evaluations,
            )

        report = MarkdownReport().generate(scorecard)

        repo_slug = facts.repository_name.replace("/", "-")
        timestamp = scorecard.repository.generated_at.strftime("%Y%m%dT%H%M%S")
        output_path = f"{repo_slug}-health-{timestamp}.md"
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(report)
        print("Wrote report to:", output_path)
    except Exception as e:
        print("Error:", str(e))


if __name__ == "__main__":
    main(ScorecardArgs().parse_args())
