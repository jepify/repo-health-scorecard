# GitHub repository scorecard

When working on a software project it's valuable to be able to assess how the development process is
working. Are PRs being reviewed quickly? Are issues being closed or are they piling up? Is there a
healthy rhythm to the contributions? How is the code quality? Are there any proactive measures implemented?

This project scores GitHub repositories via a set of metrics.

## How it works

Data gathering is separated from metric evaluation:

1. **Facts** are collected first from multiple sources (GitHub REST API and a shallow clone of the
   repository) into a single immutable `GitHubRepositoryFacts` object.
2. **Metrics** consume those shared facts and each produce a score, severity and remediation advice.
   Metrics never fetch data themselves.
3. **Reporting** aggregates the metric evaluations into a `Scorecard` with a weighted overall score
   and renders it as a timestamped Markdown report.

## Usage

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/). A `GITHUB_TOKEN` environment variable is
recommended to avoid REST API rate limits.

```sh
uv run -m src.main -r pallets/flask -w 90
```

| Flag                  | Description                                            | Default  |
| --------------------- | ------------------------------------------------------ | -------- |
| `-r`, `--repo`        | Repository reference (`owner/name`, HTTPS or SSH URL). | required |
| `-w`, `--window_days` | Time window in days to evaluate the repository over.   | `30`     |

The report is written to `<owner>-<name>-health-<timestamp>.md` in the working directory.

## Project layout

| Path             | Responsibility                                                         |
| ---------------- | ---------------------------------------------------------------------- |
| `src/facts/`     | Repositories that gather facts (REST API client, raw code clone).      |
| `src/metrics/`   | Metric definitions and the evaluator that runs them.                   |
| `src/reporting/` | Scorecard rendering (Markdown).                                        |
| `src/models/`    | Shared domain models (repository, contributors, metrics).              |
| `src/cli/`       | Typed CLI argument parsing.                                            |
| `docs/adr/`      | Architecture Decision Records — read these before changing the design. |
