# 003 - Raw code repository

## Status

Accepted

## Context

Many facts about a repository can be derived directly from its files (config
presence, CI definitions, lint setup, file patterns) without spending GitHub API
calls. Per [001-architecture](./001-architecture.md), one of our data sources is
the raw cloned `HEAD` of the repository.

We need a component that makes the working tree available locally and exposes a
small, typed interface for the facts repositories to query it.

## Decision

Introduce a **RawCode repository** that:

1. **Clones** the target GitHub repository into a temporary folder.
2. Performs a **shallow clone of `HEAD` only** (`--depth 1`, single branch, no
   history) to minimise time and disk usage.
3. Cleans up the temporary folder when done.

It exposes two query methods over the cloned tree:

- **`search`** — find lines matching a pattern across files (grep-like). Returns
  the matching files, line numbers, and matched content.
- **`list_files`** — find files matching a name/path glob (find-like). Returns
  the matching file paths.

Both methods return typed results (Pydantic models), never raw `dict`/`list` of
primitives, in line with the well-typed architecture.

## Consequences

**Positive**

- Cheap source of facts: one shallow clone yields unlimited local queries with no
  API cost.
- Shallow `HEAD`-only clone keeps clone time and disk footprint small.
- Simple grep/find interface is easy for facts repositories to consume and test.

**Negative / trade-offs**

- Only the current `HEAD` is available; history-based not avaliable.
- Requires local `git` and temporary disk space.
