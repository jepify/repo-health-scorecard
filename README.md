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

## Existing metics

### Dependency management

With AI and the world evolving more and more vulnerabilities emerge. We need to be proactive and have tooling to automate this.
Otherwise we end up not patching only parts and risk security of our applications.

Having d.g. Dependabot installed indicates if the maintainers care about their community and users. If they do not patch things, then users will switch.
It is also a sign of a proactive culture.

This is a demonstration of a tooling/code quality metric using the raw code repository.

### Possible paths

- Zizmor linter for GitHub actions.
- Precommits.
- Testing strategy
- Licensing

### Bus factor

As developers get effecient with AI and organizations grow, we end up having a lot of repos.
If some of these are tied up to individual it create silos and knowledge gaps which can be impactfull in the event that this individual leaves.

For an open source repo low bus factor shows signs of individaulization where a single person governs the repo.
It could led to less lead time on issues and feedback. Oppininions of this developer could also end up influincing the repo too much for it to be usable for others.

### Posible paths
- Semantic versioning

## Future iterations

- Use GitHub python package to acts as client towards GitHub. No need to re-invent the repo
- Logging over prints with nice progress
- More statistics from rest and GraphQL API to alow for even more metrics
- Increase number of metrics
- More visualizations in the output
- Better builder like pattern to configure the entire system making it more composable. Report generation, metric evaluation and registration.
- Error handling providing a unified way of handling them to the user

## Alternatives

- [ossf/scorecard](https://github.com/ossf/scorecard#what-is-scorecard). Opensource security foundation tool with focus on security scores.
