# 002 - Metrics definition

## Status

Accepted

## Context

Per [001-architecture](./001-architecture.md), metrics consume a shared
`GitHubRepositoryFacts` object and each produce a result. For those results to be
combined into a scorecard and rendered into a report, every metric must speak a
**common, well-typed shape** — regardless of which source its facts came from.

We also expect metrics to vary in kind: some describe the project's people and
process (e.g. bus factor), others its proactive engineering practices (e.g. code
scanning, automated dependency updates). The model needs to accommodate both
without a separate format per metric.

## Decision

Define a single result shape that every metric returns:

- **`severity`** — how serious the finding is: `LOW` | `MEDIUM` | `HIGH`.
- **`title`** — short name of the metric.
- **`description`** — what the metric measures and why it matters.
- **`implications`** — what not following the metric leads to.
- **`remediations`** — how to resolve or improve the finding.
- **`score`** — `0`–`10`, where higher is better.

`severity` and `score` are modelled as enums / bounded values, not free strings,
in line with the well-typed architecture.

Metrics are grouped into **categories**:

- **Metadata metrics** — describe contributors and process health, e.g. _bus
  factor_ (contributor count and distribution).
- **Code-quality metrics** — describe proactive engineering measures, e.g. active
  code scanning and automated dependency updates. These weigh most heavily on
  overall health.

## Consequences

**Positive**

- A uniform result shape lets the reporting layer aggregate and render any metric
  without special-casing.
- Categories give the scorecard a natural structure and allow weighting by kind.
- Enums for `severity`/`score` keep results valid by construction.

**Negative / trade-offs**

- A fixed shape constrains metrics that might want richer, metric-specific output.
- Categorisation and scoring weights are editorial choices that will need tuning
  as more metrics are added.
