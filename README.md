# git-ownership

> Bus factor analysis for your codebase — who owns what, and what happens if they leave.

[![CI](https://github.com/Aliipou/git-ownership/actions/workflows/ci.yml/badge.svg)](https://github.com/Aliipou/git-ownership/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**git-ownership** walks your git history using `git blame` to calculate true line-level code ownership per author, per file, and per directory — then surfaces **bus factor risk**: the minimum number of contributors whose departure would leave >50% of the codebase unmaintained.

## Features

- **Line-level ownership**: real `git blame` data, not just commit counts
- **Bus factor calculation**: per-file, per-directory, and whole-repo
- **Heat map**: ASCII heat map of ownership concentration by directory
- **Rich terminal output**: color-coded tables with ownership percentages
- **Export**: JSON report for CI pipelines and dashboards
- **Fast**: parallel blame with configurable file limit

## Installation

```bash
pip install git-ownership
```

Or from source:

```bash
git clone https://github.com/Aliipou/git-ownership
cd git-ownership
pip install -e ".[dev]"
```

## Usage

### Analyze current repo

```bash
git-ownership analyze
```

### Analyze a specific repo

```bash
git-ownership analyze /path/to/repo --max-files 2000
```

### Export JSON report

```bash
git-ownership analyze . --output ownership.json
```

### Show heat map

```bash
git-ownership heatmap
```

## Example Output

```
┌─────────────────────────────────────────────────────────────────────┐
│                    git-ownership v1.0.0                             │
├──────────────────────────────────┬───────────┬──────────┬───────────┤
│ File                             │ Top Owner │ %        │ Bus Factor│
├──────────────────────────────────┼───────────┼──────────┼───────────┤
│ src/auth/middleware.py           │ alice     │ 94%      │ 1 ⚠️      │
│ src/database/models.py           │ bob       │ 67%      │ 2         │
│ src/api/routes.py                │ alice     │ 45%      │ 3 ✓       │
└──────────────────────────────────┴───────────┴──────────┴───────────┘

Repo bus factor: 2  (2 contributors own >50% of all lines)
High-risk files: 12  (single contributor owns >80% of lines)
```

## Bus Factor Definition

A file's bus factor is the minimum number of contributors whose combined lines make up >50% of that file. A repo-level bus factor of 1 means one person leaving could orphan most of your codebase.

## CI Integration

```yaml
- name: Check bus factor
  run: |
    pip install git-ownership
    git-ownership analyze . --output ownership.json --min-bus-factor 2
  # Exits non-zero if repo bus factor < min-bus-factor
```

## License

MIT
