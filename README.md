# GitHub repository scorecard

When working on a software project it's valuable to be able to assess how the development process is
working. Are PRs being reviewed quickly? Are issues being closed or are they piling up? Is there a
healthy rhythm to the contributions? How is the code quality? Are there any proactive measures implemented?

This project scores GitHub repositories via a set of metrics.
Metrics can be found in [002-metrics-definition](./docs/adr/002-metrics-definition.md).

## TODOs

- [ ] Create CLI for wrapping repo input and time window
- [ ] Create GitHub RepositoryFacts

  - [ ] Create RestAPI repository
  - [ ] Create GraphQL repository
- [ ] Create type for final report. With date, commit sha information, link. A Total metric score, a section for metrics
- [ ] Create a folder with metrics building on a general protocol/interface.
      Should have description of what and why this is important - nterpretations.
      Should have remidations
- [ ] Create report strategy to support multiple reports in the future.

### PRioritized metric development
- [ ] Create RawCode repository
- [ ] Create Proactive tooling metrics. Start with simple dependabot, renovate.
- [ ] Create GitHub action checks via Zizmor and general GitHub action lint perhaps.
  // This should hopefully drive the implementation of the file interface in place

- Create other repos to drag information about contributers, GitHub issues and PR reviews.


## Nice to haves
Logging
