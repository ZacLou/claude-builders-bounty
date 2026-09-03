#!/usr/bin/env bash
set -euo pipefail

# generate-changelog
# Generates a CHANGELOG.md from commits since the last git tag.
# Usage:
#   bash changelog.sh              # writes ./CHANGELOG.md
#   bash changelog.sh <repo-path>  # writes <repo-path>/CHANGELOG.md

REPO_PATH="${1:-.}"
cd "$REPO_PATH"

LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
if [ -z "$LATEST_TAG" ]; then
    echo "No tags found in $REPO_PATH; using all commits." >&2
    RANGE="HEAD"
else
    RANGE="${LATEST_TAG}..HEAD"
fi

TMP_FILE=$(mktemp)
trap 'rm -f "$TMP_FILE"' EXIT

git log "$RANGE" --pretty=format:'%s' > "$TMP_FILE" 2>/dev/null || true

if [ ! -s "$TMP_FILE" ]; then
    echo "No commits found in range $RANGE." >&2
    exit 0
fi

added=()
fixed=()
changed=()
removed=()
other=()

while IFS= read -r line; do
    # Strip common prefixes like "feat:" or "feat(scope):"
    clean=$(echo "$line" | sed -E 's/^[a-z]+(\([^)]+\))?: *//')
    lower=$(echo "$line" | tr '[:upper:]' '[:lower:]')
    case "$lower" in
        feat*|add*)
            added+=("- $clean") ;;
        fix*)
            fixed+=("- $clean") ;;
        change*|update*|refactor*|perf*)
            changed+=("- $clean") ;;
        remove*|delete*|drop*)
            removed+=("- $clean") ;;
        *)
            other+=("- $clean") ;;
    esac
done < "$TMP_FILE"

{
    echo "# Changelog"
    echo ""
    if [ -n "$LATEST_TAG" ]; then
        echo "## Unreleased (since ${LATEST_TAG})"
    else
        echo "## Unreleased"
    fi
    echo ""
    if [ ${#added[@]} -gt 0 ]; then
        echo "### Added"
        printf '%s\n' "${added[@]}"
        echo ""
    fi
    if [ ${#fixed[@]} -gt 0 ]; then
        echo "### Fixed"
        printf '%s\n' "${fixed[@]}"
        echo ""
    fi
    if [ ${#changed[@]} -gt 0 ]; then
        echo "### Changed"
        printf '%s\n' "${changed[@]}"
        echo ""
    fi
    if [ ${#removed[@]} -gt 0 ]; then
        echo "### Removed"
        printf '%s\n' "${removed[@]}"
        echo ""
    fi
    if [ ${#other[@]} -gt 0 ]; then
        echo "### Other"
        printf '%s\n' "${other[@]}"
        echo ""
    fi
} > CHANGELOG.md

echo "CHANGELOG.md generated in $REPO_PATH"
