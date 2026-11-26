---
name: new-slice
description: Start one portfolio slice. Use when beginning a feature, opening a branch, drafting an ADR, or writing the pull request for a single change.
---

Work one item from `docs/agentic/feature_list.json`. Do not start a second item in the same branch.

1. Read `CLAUDE.md`, the open feature, and `docs/agentic/progress.md`. Explore the files the feature names before editing.
2. Write the plan in the progress log: files to touch, commands that will prove it, and whether an ADR is required. An architectural decision gets `docs/adr/ADR-00N.md` in the same shape as ADR-008 (status, date, context, decision, alternatives, consequences) and a row in `docs/adr/README.md` and the README ADR table.
3. Branch from the current base. The name describes the slice. If the work stacks on an open pull request, say `Stacked on #<n> — merge after #<n>` in the PR body and do not merge that PR.
4. Implement only that slice. Do not edit or delete tests to make them pass. Do not run `terraform apply` or call AWS.
5. Run `/verify`. Record the commands and results in the progress log. Set `passes` to true only after every step for that feature succeeded.
6. Pull request body:

```text
## What changed
<one slice, in plain sentences>

## How it was verified
<command and result>

## ADR
<none, or a link>
```

Release notes are a single README row, and only when `/release` cuts a tag. A slice does not add a release row.
