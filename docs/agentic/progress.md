# Agent progress

This is the session log for long-running work. `docs/agentic/feature_list.json` is the list of what done means. Read both at the start of a session, then `scripts/agent-init.sh`.

## How to append

Add a dated section at the end. Include:

- the feature id you touched
- what you changed
- the verify commands and whether each one passed
- the next id, or "none"
- anything the next session must not undo

Rules:

- Change a feature only by setting `passes` from false to true, after every step succeeded.
- Do not delete a feature, edit its steps, or reorder the file to make the backlog look finished.
- `aws-apply-runbook` stays `passes: false` until a human records a real apply. An agent does not apply AWS.
- One feature per session. Leave the tree compiling and the tests you ran green.

## Current state

- Date: 2026-11-26
- v1.0 Metabase dashboards are the parent slice (PR #7) and are not a feature in this ledger.
- The agent harness is in place. No feature has been implemented under it.
- Open: 8. Passing: 0. Next id: `live-ingest-med`.
- Do not run `terraform apply` or a mutating AWS call.

## Log

### 2026-11-26

- Added `CLAUDE.md`, shared Claude Code settings, hooks, skills, read-only reviewers, this ledger, and `scripts/agent-init.sh`.
- No warehouse feature was implemented. Every `passes` value is false.
- Next session should run `scripts/agent-init.sh`, then take `live-ingest-med` only.
