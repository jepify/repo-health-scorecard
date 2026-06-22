# Repo-health-scorecard Instructions

This repo is a GitHub repository scorecard that assesses the health of a GitHub repository based on various metrics such as review latency, issue throughput, contribution rhythm, code quality, etc. The data needed to answer these questions is gathered from the GitHub API (REST and GraphQL) and the raw files of the repository.

The architecture of the project separates data gathering from metric evaluation. A set of repositories pull data from different sources and contribute to a shared, immutable `GitHubRepositoryFacts` object. Metrics then take this object as input and produce a metric result without fetching data themselves.

## ADRs

Project decisions are documented in the ADRs (Architecture Decision Records) located in the `docs/adr` folder.
**Always** refer to these before making any decisions.
**Be aware** if a assumptions going to break any decisions.
**STOP** and notify the user if you are not sure about the decisions or assumptions.

## Architecture

Metrics are stored in the `src/metrics` folder.
Facts and their repositories are stored in the `src/facts` folder.
Report generation is stored in the `src/reporting` folder.

CLI interface is defined via TAP (Typed Argument Parser) in `sr/cli/cli.py`.

Models are defined in `src/models` and should be used across the codebase for consistency.

### Well typed architecture

The architecture is designed to be well-typed, with clear interfaces and protocols.
Everything must be typed.

**Avoid** using dict, list. **Prefer** Pydantic models, Classes, enums, and newtype patterns.

**Prefer** parse-dont-validate patterns where possible. Do not use Pydantic frozen models, instead rely on immutability by convention and parse-only construction.

### Dependency injection

Prefer dependency injection via constructor injection. Avoid global state and singletons.

```python
class GitHubRepositoryFactsRepository:
    def __init__(self, dep_github_api_client: GitHubAPIClient | None, dep_raw_code_repository: RawCodeRepository | None):
        self.github_api_client = dep_github_api_client or GitHubAPIClient()
        self.raw_code_repository = dep_raw_code_repository or RawCodeRepository()
```

## Tooling

Prefer using the `filesystem` mcp server for efficient access.
