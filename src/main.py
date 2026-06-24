from datetime import UTC, datetime

from src.cli.cli import ScorecardArgs
from src.facts.github_repository_fact_fetcher import GitHubRepositoryFactFetcher
from src.metrics.metrics_evaluator import MetricEvaluator
from src.models.scorecard import ScorecardRepositoryInfo, WeightedAverageScorecard
from src.reporting.markdown import MarkdownReport


def main(args: ScorecardArgs) -> None:
    print("Scanning repository")
    print("Evaluating metrics since:", args.time_window, "ago")

    evaluation_since = datetime.now(UTC) - args.time_window

    # Per ADR 001: gather facts first, then evaluate metrics against those
    # shared facts. Metrics never fetch data themselves.
    try:
        # Need to cleanup temp cloned repository after evaluation, so use a context manager to ensure cleanup.
        with GitHubRepositoryFactFetcher(args.repository) as fact_fetcher:
            facts = fact_fetcher.github_repository_facts
            print("Repository URL:", facts.repository_url)

            evaluations = MetricEvaluator(evaluation_since).evaluate(facts)

            scorecard = WeightedAverageScorecard(
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
