# Agentic development

This repository is set up so a coding agent can start from a clean context window and still know how the project is built, what it must not do, and how to prove a slice. The files follow Anthropic's Claude Code docs and three write-ups:

- [Claude Code memory](https://code.claude.com/docs/en/memory) (`CLAUDE.md`, `@` imports, `CLAUDE.local.md`)
- [Skills](https://code.claude.com/docs/en/skills) and [sub-agents](https://code.claude.com/docs/en/sub-agents)
- [Hooks](https://code.claude.com/docs/en/hooks) and [settings](https://code.claude.com/docs/en/settings)
- [Permission modes](https://code.claude.com/docs/en/permission-modes) and [permissions](https://code.claude.com/docs/en/permissions)
- [Headless](https://code.claude.com/docs/en/headless) (`claude -p` for an unattended prompt; CI does not call it)
- [GitHub Actions](https://code.claude.com/docs/en/github-actions)
- [Best practices for agentic coding](https://www.anthropic.com/research/claude-code-best-practices)
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)

The decision record is [ADR-008](../adr/ADR-008.md).

## What is loaded every session

`CLAUDE.md` is short on purpose. Context engineering says the always-on prompt should hold what the agent cannot see quickly, not a copy of every runbook. The file imports the ADR index with `@docs/adr/README.md`. Runbooks and `docs/spike-bcb.md` stay on disk until the task needs them.

`CLAUDE.local.md` is for one person's notes. It is gitignored. Nested `CLAUDE.md` files under `transform/dbt`, `infra/terraform`, and `orchestration` load when the agent reads those trees, because the commands there are not the root commands.

## What is enforced

`.claude/settings.json` is the shared team settings file.

The allow list is commands that exist and are reversible: `make test`, `make lint`, `make dbt-build`, the other dbt and Airflow and Metabase check targets, pytest, ruff, `git status` / `diff` / `log`, and the exact `terraform fmt` and `init -backend=false` / `validate` lines inside `make tf-check`. There is no sqlfluff target because the project does not use sqlfluff. `terraform plan` is not allowed. A plan can talk to a backend.

The deny list blocks `terraform apply`, `terraform destroy`, every `aws` CLI call, `git push --force`, `rm -rf`, and reads of `.env` and `secrets/`. Deny wins over allow, including in modes that skip prompts. `.env.example` stays readable.

Hooks are the deterministic half. Best practice is to put a rule in a hook when a paragraph in `CLAUDE.md` is not good enough.

- `PostToolUse` on `Edit` and `Write` runs `.claude/hooks/format_changed.py`. Python goes through ruff format and ruff check. `.tf` files go through `terraform fmt` when the binary exists. The script reads the hook JSON on stdin, ignores SQL, and exits 0 if a formatter is missing or fails.
- `PreToolUse` on `Bash` runs `.claude/hooks/block_unsafe_bash.py`. Terraform apply and destroy, mutating AWS CLI calls, `git push --force`, and `rm -rf` exit 2 with a message on stderr. Exit 2 is the documented block. Read-only `aws` list, get, describe, head, and `s3 ls` are not blocked by the hook. The deny rule still blocks every `aws` invocation unless a later settings change removes it.

`make test` includes `tests/test_claude_hooks.py`, which feeds sample hook JSON to both scripts.

## What the agent does on purpose

Skills under `.claude/skills/` are the repeated workflows. Each `SKILL.md` has the `name` and `description` frontmatter from the skills doc. Invoke them as `/new-slice`, `/add-bcb-entity`, `/dbt-model`, `/verify`, and `/release`.

| Skill | When |
| --- | --- |
| `new-slice` | One branch, one feature, an ADR when the shape of the system changes, a pull request body |
| `add-bcb-entity` | A new Olinda resource from the contract to the Airflow map |
| `dbt-model` | A model, its YAML, and a test |
| `verify` | Lint, unit tests, dbt build, DAG import, Metabase checks, `make tf-check` |
| `release` | A tag and a one-line GitHub release in the README's style |

Subagents in `.claude/agents/` are read-only. `data-quality-reviewer` checks dbt and dashboard SQL against the domain rules. `code-reviewer` checks a diff against `CLAUDE.md`. Both are limited to Read, Grep, and Glob, so they cannot edit the tree or run a shell.

## Long-running sessions

The harness post splits a long job into an initializer and later sessions that do one feature and leave the tree clean.

- `docs/agentic/feature_list.json` is the backlog after v1.0: live MED, CNAE, and DICT ingestion, a municipality-to-national reconciliation, the AWS apply runbook (agents do not apply), Athena publication of the dashboard marts, and optional Spark and AI slices that start with an ADR. Every item has `passes: false`.
- `docs/agentic/progress.md` is the log. Append a session. Do not rewrite history to hide a failure.
- `scripts/agent-init.sh` prints the branch, git status, and the next open feature. It creates `.venv` and installs `.[dev]` when the venv is missing. It does not start Docker, read `.env`, or call AWS.

A later session should run the init script, do one failing feature, run `/verify`, and only then set `passes` to true.

## GitHub

`.github/workflows/claude.yml` uses `anthropics/claude-code-action@v1` when someone mentions `@claude` on an issue, issue comment, pull request review, or review comment. That is the interactive example from the GitHub Actions doc, plus the secret gate this repo already uses for Terraform.

Required secret: `ANTHROPIC_API_KEY`, a Claude API key stored as a repository secret. The Claude GitHub App also has to be installed on the repository, with contents, issues, and pull requests access, or the action has nothing to answer as. The job checks the secret and skips the action when it is empty, so a public fork or a fresh clone does not fail the workflow. This file is not referenced by `.github/workflows/ci.yml` and should not be added to required checks.

`claude_args` sets `--max-turns 8` so a mention cannot run without a bound.
