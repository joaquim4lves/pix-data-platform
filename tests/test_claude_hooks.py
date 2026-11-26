"""Hook scripts take the Claude Code JSON payload on stdin.

Exit 2 blocks a PreToolUse Bash call. The format hook stays exit 0 even when
it has nothing to do, which is the non-fatal contract for PostToolUse.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BLOCK = ROOT / ".claude" / "hooks" / "block_unsafe_bash.py"
FORMAT = ROOT / ".claude" / "hooks" / "format_changed.py"


def _run(script: Path, payload: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )


def _bash(command: str) -> dict[str, object]:
    return {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
    }


def _edit(path: Path) -> dict[str, object]:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {"file_path": str(path), "content": path.read_text(encoding="utf-8")},
        "tool_response": {"filePath": str(path), "type": "create"},
    }


@pytest.mark.parametrize(
    "command",
    [
        "terraform apply",
        "terraform apply -auto-approve",
        "terraform -chdir=infra/terraform/envs/dev apply",
        "terraform destroy -auto-approve",
        "cd infra && terraform apply",
        "aws s3 rm s3://pix-data-local/raw",
        "aws --profile dev s3 rm s3://pix-data-local/raw",
        "aws s3 cp data.parquet s3://pix-data-local/raw",
        "aws lambda update-function-code --function-name pix",
        "aws iam create-user --user-name pix",
        "git push --force origin main",
        "git push origin main --force",
        "git push -f",
        "rm -rf data/raw",
        "rm -fr /tmp/pix-scratch",
    ],
)
def test_unsafe_bash_exits_2(command: str) -> None:
    result = _run(BLOCK, _bash(command))
    assert result.returncode == 2
    assert result.stderr.startswith("Blocked:")
    body = json.loads(result.stdout)
    decision = body["hookSpecificOutput"]
    assert decision["hookEventName"] == "PreToolUse"
    assert decision["permissionDecision"] == "deny"
    assert decision["permissionDecisionReason"].startswith("Blocked:")


@pytest.mark.parametrize(
    "command",
    [
        "make test",
        "make lint",
        "make tf-check",
        "terraform fmt -check -recursive -diff infra/terraform",
        "terraform -chdir=infra/terraform/bootstrap validate",
        "aws s3 ls",
        "aws --profile dev s3 ls s3://pix-data-local",
        "aws sts get-caller-identity",
        "aws s3api list-buckets",
        "git status",
        "git diff",
        "git push origin HEAD",
        "rm data/tmp-file",
    ],
)
def test_safe_bash_exits_0(command: str) -> None:
    result = _run(BLOCK, _bash(command))
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_invalid_hook_json_does_not_block() -> None:
    result = subprocess.run(
        ["python3", str(BLOCK)],
        input="{not json",
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""


def _ruff_installed() -> bool:
    if (ROOT / ".venv" / "bin" / "ruff").is_file() or shutil.which("ruff"):
        return True
    probe = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    return probe.returncode == 0


def test_format_hook_rewrites_python(tmp_path: Path) -> None:
    path = tmp_path / "sample.py"
    path.write_text("def foo( ):\n    x=1\n    return x\n", encoding="utf-8")
    result = _run(FORMAT, _edit(path))
    assert result.returncode == 0
    if not _ruff_installed():
        return
    assert path.read_text(encoding="utf-8") == "def foo():\n    x = 1\n    return x\n"
    note = json.loads(result.stdout)
    assert note["hookSpecificOutput"]["hookEventName"] == "PostToolUse"
    assert "ruff format" in note["hookSpecificOutput"]["additionalContext"]


def test_format_hook_reports_ruff_check_without_failing(tmp_path: Path) -> None:
    if not _ruff_installed():
        pytest.skip("ruff is not installed")
    path = tmp_path / "broken.py"
    path.write_text("import os\n", encoding="utf-8")
    result = _run(FORMAT, _edit(path))
    assert result.returncode == 0
    note = json.loads(result.stdout)
    assert "ruff check" in note["hookSpecificOutput"]["additionalContext"]


def test_format_hook_leaves_sql_alone(tmp_path: Path) -> None:
    path = tmp_path / "model.sql"
    original = "select 1\n"
    path.write_text(original, encoding="utf-8")
    result = _run(FORMAT, _edit(path))
    assert result.returncode == 0
    assert result.stdout == ""
    assert path.read_text(encoding="utf-8") == original


def test_format_hook_formats_terraform_when_present(tmp_path: Path) -> None:
    path = tmp_path / "main.tf"
    path.write_text('resource "null_resource" "x" {\ncount = 1\n}\n', encoding="utf-8")
    before = path.read_text(encoding="utf-8")
    result = _run(FORMAT, _edit(path))
    assert result.returncode == 0
    if shutil.which("terraform") is None:
        assert path.read_text(encoding="utf-8") == before
        assert result.stdout == ""
        return
    assert "count" in path.read_text(encoding="utf-8")
    assert result.returncode == 0


def test_format_hook_ignores_bad_json(tmp_path: Path) -> None:
    result = subprocess.run(
        ["python3", str(FORMAT)],
        input="[]",
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert tmp_path.exists()


def test_hook_scripts_are_executable() -> None:
    assert os.access(BLOCK, os.X_OK)
    assert os.access(FORMAT, os.X_OK)


def test_agentic_json_and_settings() -> None:
    features = json.loads(
        (ROOT / "docs" / "agentic" / "feature_list.json").read_text(encoding="utf-8")
    )
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in features]
    assert len(ids) == len(set(ids))
    for item in features:
        assert isinstance(item["description"], str) and item["description"]
        assert item["steps"]
        assert all(isinstance(step, str) and step for step in item["steps"])
        assert item["passes"] is False
    assert "make test" in " ".join(settings["permissions"]["allow"])
    deny = settings["permissions"]["deny"]
    assert "Bash(terraform apply)" in deny
    assert "Bash(terraform destroy)" in deny
    assert "Bash(aws *)" in deny
    assert "Read(.env)" in deny
    assert settings["hooks"]["PreToolUse"][0]["matcher"] == "Bash"
    assert settings["hooks"]["PostToolUse"][0]["matcher"] == "Edit|Write"
    pre = settings["hooks"]["PreToolUse"][0]["hooks"][0]
    post = settings["hooks"]["PostToolUse"][0]["hooks"][0]
    assert pre["type"] == "command"
    assert post["type"] == "command"
    assert pre["command"].endswith("block_unsafe_bash.py")
    assert post["command"].endswith("format_changed.py")


def test_claude_workflow_skips_without_a_secret() -> None:
    text = (ROOT / ".github" / "workflows" / "claude.yml").read_text(encoding="utf-8")
    assert "anthropics/claude-code-action@v1" in text
    assert "ANTHROPIC_API_KEY" in text
    assert "present=false" in text
    assert "\n  push:" not in text
    assert "workflow_dispatch" not in text


def test_agent_init_shell_syntax() -> None:
    script = ROOT / "scripts" / "agent-init.sh"
    assert os.access(script, os.X_OK)
    subprocess.run(["bash", "-n", str(script)], check=True)


def test_claude_md_stays_short() -> None:
    lines = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()
    assert len(lines) < 150
    assert "@docs/adr/README.md" in "\n".join(lines)
