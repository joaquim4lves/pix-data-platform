---
name: release
description: Tag a release and draft GitHub release notes in this repo's one-line style. Use only when asked to cut a version.
---

Do not tag unless someone asked for a release and `/verify` is green.

1. Read `pyproject.toml` `version`, `transform/dbt/dbt_project.yml` `version`, the README release table, and `git tag`. They should name the same release you are cutting. v0.1 through v0.6 are the tagged history. v1.0 is the Metabase slice.
2. Add one README row, the same shape as the others: a tag link when the tag exists, then one sentence about what landed. Terraform rows say "Not applied" when that is still true. Do not paste a changelog.
3. Tag `vX.Y` on the commit that will be released. Annotated message is the same sentence as the table row.
4. Publish with `gh release create vX.Y --title "vX.Y" --notes "<the same sentence>"` only after the tag is the commit you verified. Do not force-push the tag.
5. Leave `docs/agentic/feature_list.json` alone except for a feature whose steps include this release and actually passed.
