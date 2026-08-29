#!/usr/bin/env python3
"""Claude Code pre-tool-use hook: blocks destructive bash commands.

Reads the JSON tool-call payload from stdin. If the tool is Bash and the
command matches a known destructive pattern, logs the attempt and exits with
code 2 so Claude Code blocks the call. Safe commands exit 0.

Install:
    mkdir -p ~/.claude/hooks/pre-tool-use
    cp pre-tool-use.py ~/.claude/hooks/pre-tool-use/
    chmod +x ~/.claude/hooks/pre-tool-use/pre-tool-use.py
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional

LOG_FILE = Path.home() / ".claude" / "hooks" / "blocked.log"


@dataclass(frozen=True)
class Rule:
    id: str
    description: str
    help: str
    # Callable receives a list of command tokens (split on shell metacharacters).
    matches: callable


def _tokens(command: str) -> list[str]:
    """Split a shell command into tokens, preserving quoted substrings.

    Handles pipes, semicolons, &&, || and subshells by splitting on those
    boundaries first, then lexing each segment. This is intentionally a
    lightweight parser; it does not expand variables or aliases.
    """
    command = command.strip()
    if not command:
        return []

    # Break compound commands into simple commands.
    segments = re.split(r"[;|&]|\|\||&&|\$\(|`", command)
    tokens: list[str] = []
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        try:
            tokens.extend(shlex.split(segment))
        except ValueError:
            # Fall back to whitespace split if shlex cannot parse it.
            tokens.extend(segment.split())
    return tokens


def _lowercase(tokens: Iterable[str]) -> list[str]:
    return [t.lower() for t in tokens]


def _has_rm_rf(tokens: list[str]) -> bool:
    """Match rm -rf / rm -fr and variants, including rm -r -f."""
    for i, t in enumerate(tokens):
        if t != "rm":
            continue
        # Look ahead for flags and path arguments.
        flags = ""
        for j in range(i + 1, min(i + 5, len(tokens))):
            arg = tokens[j]
            if arg.startswith("-"):
                flags += arg
            else:
                break
        if "r" in flags and "f" in flags:
            return True
    return False


def _has_force_push(tokens: list[str]) -> bool:
    """Match git push --force / -f."""
    for i, t in enumerate(tokens):
        if t != "git":
            continue
        if "push" not in tokens[i + 1 : i + 4]:
            continue
        for arg in tokens[i + 1 : i + 6]:
            if arg in ("--force", "-f"):
                return True
            if arg == "--force-with-lease":
                # --force-with-lease is the safer variant; do not block.
                return False
    return False


def _has_drop_table(tokens: list[str]) -> bool:
    """Match DROP TABLE [IF EXISTS] ..."""
    lowered = _lowercase(tokens)
    for i, t in enumerate(lowered):
        if t == "drop" and i + 1 < len(lowered) and lowered[i + 1] == "table":
            return True
    return False


def _has_truncate_table(tokens: list[str]) -> bool:
    lowered = _lowercase(tokens)
    for i, t in enumerate(lowered):
        if t == "truncate" and i + 1 < len(lowered) and lowered[i + 1] == "table":
            return True
    return False


def _has_unqualified_delete(tokens: list[str]) -> bool:
    """Match DELETE FROM <table> without a WHERE clause in the same statement."""
    lowered = _lowercase(tokens)
    for i, t in enumerate(lowered):
        if t == "delete" and i + 1 < len(lowered) and lowered[i + 1] == "from":
            # Scan until the next SQL keyword that would start a new statement.
            remainder = lowered[i + 2 :]
            if "where" not in remainder:
                return True
    return False


def _has_disk_overwrite(tokens: list[str]) -> bool:
    """Match dd if=... of=/dev/... or mkfs on block devices."""
    lowered = _lowercase(tokens)
    for i, t in enumerate(lowered):
        if t == "dd":
            for arg in tokens[i + 1 :]:
                if arg.lower().startswith("of=/dev/"):
                    return True
        if t in ("mkfs", "mkfs.ext4", "mkfs.xfs", "mkfs.ntfs"):
            for arg in tokens[i + 1 :]:
                if arg.startswith("/dev/"):
                    return True
        if t in (">", ">>") and i + 1 < len(tokens):
            target = tokens[i + 1].lower()
            if target.startswith("/dev/sd") or target.startswith("/dev/nvme"):
                return True
    return False


def _has_filesystem_nuke(tokens: list[str]) -> bool:
    """Match chmod -R 000 /, rm -rf /, etc."""
    lowered = _lowercase(tokens)
    for i, t in enumerate(lowered):
        if t == "rm" and "-rf" in "".join(tokens[i + 1 : i + 4]):
            for arg in tokens[i + 1 :]:
                if arg == "/" or arg.startswith("/~") is False and arg in ("/", "/*"):
                    return True
        if t == "chmod" and i + 1 < len(tokens) and tokens[i + 1].startswith("-"):
            flags = tokens[i + 1]
            if "r" in flags:
                for arg in tokens[i + 2 :]:
                    if arg in ("/", "/*"):
                        return True
    return False


RULES: list[Rule] = [
    Rule(
        id="rm-rf",
        description="Recursive force delete (`rm -rf` / `rm -fr`)",
        help="Use `trash` or delete files explicitly without `-r -f`.",
        matches=_has_rm_rf,
    ),
    Rule(
        id="force-push",
        description="Git force push (`--force` / `-f`)",
        help="Use `--force-with-lease` or coordinate with your team.",
        matches=_has_force_push,
    ),
    Rule(
        id="drop-table",
        description="DROP TABLE",
        help="Backup the table and run the statement manually if intended.",
        matches=_has_drop_table,
    ),
    Rule(
        id="truncate-table",
        description="TRUNCATE TABLE",
        help="Use DELETE with a WHERE clause or run manually.",
        matches=_has_truncate_table,
    ),
    Rule(
        id="unqualified-delete",
        description="DELETE FROM without WHERE",
        help="Add a WHERE clause, or run the statement manually.",
        matches=_has_unqualified_delete,
    ),
    Rule(
        id="disk-overwrite",
        description="Raw disk write (`dd` / `mkfs` to block device)",
        help="Target block-device writes are extremely destructive; run them manually.",
        matches=_has_disk_overwrite,
    ),
    Rule(
        id="filesystem-nuke",
        description="Filesystem-level destructive operation on root",
        help="Operations like `chmod -R 000 /` or `rm -rf /` will brick the system.",
        matches=_has_filesystem_nuke,
    ),
]


def evaluate(command: str) -> Optional[Rule]:
    tokens = _tokens(command)
    if not tokens:
        return None
    for rule in RULES:
        try:
            if rule.matches(tokens):
                return rule
        except Exception:
            continue
    return None


def log_blocked(command: str, rule: Rule, project_path: str) -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = (
        f"[{timestamp}] BLOCKED | rule={rule.id} | "
        f"reason={rule.description} | command={command!r} | path={project_path}\n"
    )
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(entry)


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If stdin is not valid JSON, let Claude Code handle it.
        return 0

    tool_name = payload.get("tool_name") or ""
    if tool_name != "Bash":
        return 0

    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command:
        return 0

    rule = evaluate(command)
    if rule is None:
        return 0

    project_path = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    log_blocked(command, rule, project_path)

    # Write a structured message to stderr so Claude Code shows it.
    print("🚫 BLOCKED by pre-tool-use hook", file=sys.stderr)
    print(f"Rule: {rule.id} — {rule.description}", file=sys.stderr)
    print(f"Command: {command}", file=sys.stderr)
    print(f"Why blocked: {rule.description} can cause irreversible data loss.", file=sys.stderr)
    print(f"How to proceed: {rule.help}", file=sys.stderr)
    print(f"Logged to: {LOG_FILE}", file=sys.stderr)

    return 2


if __name__ == "__main__":
    sys.exit(main())
