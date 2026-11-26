#!/usr/bin/env bash
# Print repo state and prepare the local verifier. No AWS and no terraform apply.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "== pix-data-platform agent init =="
echo "root: ${ROOT}"
echo "branch: $(git rev-parse --abbrev-ref HEAD)"
echo "commit: $(git rev-parse --short HEAD) $(git log -1 --format=%s)"
echo "status:"
git status --short
echo
python3 --version

if [[ ! -x .venv/bin/python ]]; then
  echo "creating .venv and installing .[dev]"
  python3 -m venv .venv
  .venv/bin/python -m pip install -e '.[dev]'
fi
echo "python: $(.venv/bin/python -c 'import sys; print(sys.executable)')"

if [[ -f .env ]]; then
  echo ".env: present (contents not printed)"
else
  echo ".env: absent"
fi

.venv/bin/python - <<'PY'
import json
from pathlib import Path

items = json.loads(Path("docs/agentic/feature_list.json").read_text(encoding="utf-8"))
pending = [item["id"] for item in items if item["passes"] is False]
done = [item["id"] for item in items if item["passes"] is True]
print(f"features: {len(done)} passing, {len(pending)} open")
if pending:
    print(f"next: {pending[0]}")
PY

echo
echo "Verification, still no AWS:"
echo "  make lint"
echo "  make test"
echo "  python -c \"from pathlib import Path; from tests.pix_warehouse import write_sample_raw; write_sample_raw(Path('data/raw'))\""
echo "  make dbt-deps && make dbt-build"
echo "  make airflow-test          # pip install -e '.[dev,airflow]' first"
echo "  make metabase-validate"
echo "  make tf-check              # terraform fmt, init -backend=false, validate"
echo "Do not run terraform apply, terraform destroy, or a mutating aws command."
