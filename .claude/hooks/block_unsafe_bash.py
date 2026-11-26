#!/usr/bin/env python3
"""PreToolUse hook for the Bash tool.

Claude Code writes the hook event JSON to stdin. Exit 0 leaves the normal
permission flow alone. Exit 2 blocks the tool call and shows stderr to the
model, which is the documented blocking signal for PreToolUse.
"""

from __future__ import annotations

import json
import re
import shlex
import sys

_TERRAFORM = re.compile(
    r"\bterraform\b(?:\s+-\S+)*\s+(apply|destroy)\b",
    re.IGNORECASE,
)
_AWS_CALL = re.compile(r"(?:^|\s)aws\b(.*)$", re.IGNORECASE)
_READ_PREFIXES = ("list-", "get-", "describe-", "head-", "lookup-")
_BOOLEAN_AWS = {"--debug", "--no-verify-ssl", "--no-sign-request", "--no-cli-pager"}
_FORCE_PUSH = re.compile(
    r"\bgit\b(?:\s+-\S+)*\s+push\b.*(?:--force-with-lease\b|--force\b|(?<!\S)-f\b)",
    re.IGNORECASE,
)


def segments(command: str) -> list[str]:
    return [part.strip() for part in re.split(r"&&|\|\||;|\n", command) if part.strip()]


def _rm_rf(segment: str) -> bool:
    match = re.search(r"\brm\b(?P<rest>.*)$", segment)
    if match is None:
        return False
    rest = match.group("rest")
    flags = re.findall(r"(?:^|\s)(-[A-Za-z]+)", rest)
    letters = "".join(flag.lstrip("-") for flag in flags)
    recursive = "r" in letters or "--recursive" in rest
    force = "f" in letters or "--force" in rest
    return recursive and force


def _aws_rest(tokens: list[str]) -> list[str]:
    index = 1
    while index < len(tokens) and tokens[index].startswith("-"):
        flag = tokens[index]
        index += 1
        if flag in _BOOLEAN_AWS or flag.startswith("--no-") or "=" in flag:
            continue
        if index < len(tokens) and not tokens[index].startswith("-"):
            index += 1
    return tokens[index:]


def _aws_read_only(rest: list[str]) -> bool:
    if not rest or rest[0] == "configure":
        return False
    if rest[0] == "help":
        return True
    if rest[:2] == ["sts", "get-caller-identity"]:
        return True
    if len(rest) >= 2 and rest[0] == "s3" and rest[1] == "ls":
        return True
    return len(rest) >= 2 and rest[1].startswith(_READ_PREFIXES)


def _aws_mutating(segment: str) -> bool:
    match = _AWS_CALL.search(segment)
    if match is None:
        return False
    invocation = ("aws" + match.group(1)).strip()
    try:
        tokens = shlex.split(invocation)
    except ValueError:
        return True
    if not tokens or tokens[0].lower() != "aws":
        return False
    return not _aws_read_only(_aws_rest(tokens))


def block_reason(command: str) -> str | None:
    """Return the deny message, or None when the command may proceed."""
    for segment in segments(command):
        terraform = _TERRAFORM.search(segment)
        if terraform is not None:
            verb = terraform.group(1).lower()
            return (
                f"Blocked: terraform {verb} is not allowed. "
                "Run make tf-check. Do not apply or destroy this stack."
            )
        if _FORCE_PUSH.search(segment):
            return "Blocked: git push --force is not allowed."
        if _rm_rf(segment):
            return "Blocked: rm -rf is not allowed."
        if _aws_mutating(segment):
            return (
                "Blocked: AWS mutating call is not allowed. "
                "Read-only list, get, describe, head, and s3 ls may proceed. "
                "Do not create, change, or delete AWS resources."
            )
    return None


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    command = ""
    if isinstance(tool_input, dict) and isinstance(tool_input.get("command"), str):
        command = tool_input["command"]
    reason = block_reason(command)
    if reason is None:
        return 0
    sys.stderr.write(reason + "\n")
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
