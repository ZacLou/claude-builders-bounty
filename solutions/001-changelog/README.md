# Generate Changelog

A tiny bash script that auto-generates a `CHANGELOG.md` from commits since the latest git tag.

## Setup

1. Copy `changelog.sh` into your repo (or anywhere in your `$PATH`).
2. Make it executable: `chmod +x changelog.sh`.
3. Run it: `bash changelog.sh`.

## Usage

```bash
# Generate CHANGELOG.md in the current repo
bash changelog.sh

# Generate CHANGELOG.md in another repo
bash changelog.sh /path/to/repo
```

## How it works

- Finds the latest git tag with `git describe --tags --abbrev=0`.
- Collects commits from that tag to `HEAD`.
- Categorizes commits by prefix:
  - `feat`, `add` → **Added**
  - `fix` → **Fixed**
  - `change`, `update`, `refactor`, `perf` → **Changed**
  - `remove`, `delete`, `drop` → **Removed**
  - everything else → **Other**
- Writes the result to `CHANGELOG.md`.
