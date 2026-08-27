# generate-changelog

> Auto-generate a structured `CHANGELOG.md` from git history.
> Bounty submission for [claude-builders-bounty#1](https://github.com/claude-builders-bounty/claude-builders-bounty/issues/1).

## Setup (3 steps)

```bash
# 1. Copy the script into any git repo
cp changelog.sh generate_changelog.py /path/to/your/repo/

# 2. Make it executable
chmod +x changelog.sh

# 3. Run it
./changelog.sh
```

## Usage

| Command | What it does |
|---------|-------------|
| `./changelog.sh` | Print changelog to stdout |
| `./changelog.sh -w` | Write/update `CHANGELOG.md` in current directory |
| `./changelog.sh -o FILE` | Write output to a custom file |

## How it works

1. Finds the latest git tag with `git describe --tags`
2. Reads all commits since that tag
3. Parses conventional commit prefixes (`feat:`, `fix:`, `refactor:`, etc.)
4. Auto-categorizes into:
   - **Added** — `feat`, `add`, `new`, `implement`
   - **Fixed** — `fix`, `bug`, `patch`, `resolve`
   - **Changed** — `refactor`, `update`, `improve`, `tweak`
   - **Removed** — `remove`, `delete`, `deprecate`, `drop`
   - **Other** — everything else
5. Outputs a [Keep a Changelog](https://keepachangelog.com/)–style markdown

## Sample output

```
# Changelog

## [2026-08-27] — v1.0.0 → HEAD

### Added
- feat: initial README with bounty board

### Fixed
- fix: correct license year

### Changed
- refactor: split changelog generation into separate module

### Other
- Initial commit
```

## Requirements

- Python 3.9+
- Git
