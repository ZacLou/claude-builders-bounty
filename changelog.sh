#!/usr/bin/env bash
# generate-changelog — auto-generate CHANGELOG.md from git history
#
# Usage:
#   ./changelog.sh              Print changelog to stdout
#   ./changelog.sh -w           Write/update CHANGELOG.md in current directory
#   ./changelog.sh -o FILE      Write output to FILE
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/generate_changelog.py"

exec python3 "$PY_SCRIPT" "$@"
