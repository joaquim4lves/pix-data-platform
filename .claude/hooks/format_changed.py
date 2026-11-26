#!/usr/bin/env python3
"""PostToolUse hook for Edit and Write.

Reads the hook event JSON from stdin and formats the file that tool wrote.
Ruff covers Python. terraform fmt covers Terraform. sqlfluff is not a project
dependency, so SQL is left untouched. Failures are swallowed: the tool call
already succeeded, and a formatter miss must not fail the session.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


def _file_path(payload: object) -> Path | None:
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input")
    if isinstance(tool_input, dict) and isinstance(tool_input.get("file_path"), str):
        return Path(tool_input["file_path"])
    tool_response = payload.get("tool_response")
    if isinstance(tool_response, dict) and isinstance(tool_response.get("filePath"), str):
        return Path(tool_response["filePath"])
    return None


def _ruff_argv() -> list[str] | None:
    root = Path(__file__).resolve().parents[2]
    venv_ruff = root / ".venv" / "bin" / "ruff"
    if venv_ruff.is_file():
        return [str(venv_ruff)]
    found = shutil.which("ruff")
    if found:
        return [found]
    return [sys.executable, "-m", "ruff"]


def _run(argv: list[str], path: Path) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            [*argv, str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _note(text: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": text[:2000],
            }
        },
        sys.stdout,
    )


def _format_python(path: Path) -> None:
    ruff = _ruff_argv()
    if ruff is None:
        return
    before = path.read_text(encoding="utf-8")
    formatted = _run([*ruff, "format"], path)
    if formatted is None or formatted.returncode != 0:
        return
    checked = _run([*ruff, "check"], path)
    notes: list[str] = []
    if path.read_text(encoding="utf-8") != before:
        notes.append(f"ruff format updated {path.name}.")
    if checked is not None and checked.returncode != 0:
        detail = (checked.stdout or checked.stderr).strip()
        notes.append(f"ruff check reported:\n{detail}")
    if notes:
        _note(" ".join(notes))


def _format_terraform(path: Path) -> None:
    terraform = shutil.which("terraform")
    if terraform is None:
        return
    before = path.read_text(encoding="utf-8")
    result = _run([terraform, "fmt"], path)
    if result is None or result.returncode != 0:
        return
    if path.read_text(encoding="utf-8") != before:
        _note(f"terraform fmt updated {path.name}.")


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    path = _file_path(payload)
    if path is None or not path.is_file():
        return 0
    try:
        suffix = path.suffix.lower()
        if suffix == ".py":
            _format_python(path)
        elif suffix in {".tf", ".tfvars"}:
            _format_terraform(path)
    except (OSError, UnicodeError):
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
