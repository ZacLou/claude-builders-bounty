# Pre-Tool-Use Safety Hook

A Claude Code `pre-tool-use` hook that intercepts dangerous Bash commands before they run.

## Install

```bash
mkdir -p ~/.claude/hooks
cp solutions/003-pre-tool-hook/pre-tool-use ~/.claude/hooks/pre-tool-use
chmod +x ~/.claude/hooks/pre-tool-use
```

## What it blocks

| Pattern | Why |
|---|---|
| `rm -rf` | Recursive irreversible deletion |
| `DROP TABLE` | Destroys table structure and data |
| `TRUNCATE` | Bulk delete without row-level logging |
| `DELETE FROM` without `WHERE` | Deletes all rows |
| `git push --force` | Overwrites remote history |

## Logging

Every blocked attempt is appended to:

```
~/.claude/hooks/blocked.log
```

Format:

```
2026-09-03T12:34:56+00:00 | /path/to/project | rm -rf / | rm -rf can recursively delete files irreversibly.
```

## Test

```bash
echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf /tmp/foo"}}' | python3 ~/.claude/hooks/pre-tool-use
# {"decision": "block", "message": "..."}

echo '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}' | python3 ~/.claude/hooks/pre-tool-use
# {"decision": "allow"}
```
