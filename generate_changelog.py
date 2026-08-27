#!/usr/bin/env python3
"""Generate a structured CHANGELOG.md from git history.

Fetches commits since the last git tag, auto-categorizes by conventional
commit prefix, and outputs a Keep a Changelog–style CHANGELOG.md.
"""

import subprocess
import sys
import re
from datetime import date
from pathlib import Path

CATEGORIES = {
    "Added": ["feat", "add", "added", "create", "new", "implement"],
    "Fixed": ["fix", "fixed", "bug", "patch", "resolve", "repair", "correct"],
    "Changed": ["change", "changed", "update", "updated", "refactor", "improve",
                "improved", "modify", "modified", "adjust", "tweak", "enhance",
                "enhanced", "optimize", "optimized", "rework"],
    "Removed": ["remove", "removed", "delete", "deleted", "drop", "dropped",
                "deprecate", "deprecated", "cleanup"],
}

UNKNOWN_LABEL = "Other"

def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()

def latest_tag() -> str | None:
    try:
        return run(["git", "describe", "--tags", "--abbrev=0"])
    except subprocess.CalledProcessError:
        return None

def commits_since_tag(tag: str | None) -> list[str]:
    if tag:
        range_spec = f"{tag}..HEAD"
    else:
        range_spec = "HEAD"
    try:
        log = run(["git", "log", range_spec, "--pretty=format:%s"])
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in log.split("\n") if line.strip()]

def parse_conventional_prefix(msg: str) -> tuple[str | None, str]:
    """Extract type from conventional commit: 'type(scope): description' or 'type: desc'."""
    m = re.match(r'^(\w+(?:\([^)]*\))?)[!:]?\s*[:;]\s*(.+)', msg)
    if m:
        prefix = m.group(1).split("(")[0].strip().lower()
        desc = m.group(2).strip()
        return prefix, desc
    return None, msg

def categorize(msg: str) -> str:
    """Categorize a commit message into Added/Fixed/Changed/Removed/Other."""
    prefix, desc = parse_conventional_prefix(msg)
    search = (prefix or "").lower() + " " + desc.lower()
    for category, keywords in CATEGORIES.items():
        for kw in keywords:
            if search.startswith(kw) or f" {kw}" in search[:40]:
                return category
    return UNKNOWN_LABEL

def build_changelog() -> str:
    tag = latest_tag()
    commits = commits_since_tag(tag)

    if not commits:
        return f"# Changelog\n\n## [{date.today()}] — No changes since last tag\n\nNo commits found since `{tag or 'the beginning'}`.\n"

    buckets: dict[str, list[str]] = {c: [] for c in CATEGORIES}
    buckets[UNKNOWN_LABEL] = []

    for msg in commits:
        buckets[categorize(msg)].append(msg)

    today = date.today().isoformat()
    tag_ref = tag if tag else "first release"
    lines = [
        "# Changelog",
        "",
        f"## [{today}] — {tag_ref} → HEAD",
        "",
    ]

    for cat in ["Added", "Changed", "Fixed", "Removed", UNKNOWN_LABEL]:
        entries = buckets.get(cat, [])
        if not entries:
            continue
        lines.append(f"### {cat}")
        for entry in entries:
            lines.append(f"- {entry}")
        lines.append("")

    return "\n".join(lines)

def main():
    output_path = None
    write_mode = False

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] in ("-o", "--output"):
            i += 1
            output_path = args[i]
            write_mode = True
        elif args[i] in ("-w", "--write"):
            write_mode = True
        elif args[i] in ("-h", "--help"):
            print(__doc__)
            print("Usage: generate_changelog.py [-o FILE] [-w]")
            print("  -o FILE   Write output to FILE (default: CHANGELOG.md)")
            print("  -w        Overwrite CHANGELOG.md in current directory")
            sys.exit(0)
        i += 1

    changelog = build_changelog()

    if write_mode:
        target = output_path or "CHANGELOG.md"
        existing = ""
        if Path(target).exists():
            existing = Path(target).read_text()
        # Prepend new entry after the title line
        if existing.strip():
            title_end = existing.find("\n")
            if title_end == -1:
                title_end = len(existing)
            prefix = existing[:title_end].rstrip()
            suffix = existing[title_end:].lstrip("\n")
            new_body = "\n".join(
                line for line in changelog.split("\n")
                if not line.startswith("# Changelog")
            ).strip()
            combined = f"{prefix}\n\n{new_body}\n\n{suffix}"
        else:
            combined = changelog
        Path(target).write_text(combined + "\n")
        print(f"✅ CHANGELOG written to {target}")
    else:
        print(changelog)

if __name__ == "__main__":
    main()
