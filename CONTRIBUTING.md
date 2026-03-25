# Contributing to myxo-lab

## Prerequisites

| Tool       | Version  | Install                                    |
|------------|----------|--------------------------------------------|
| Rust       | 1.85+    | [rustup.rs](https://rustup.rs)             |
| Python     | 3.13+    | System or [pyenv](https://github.com/pyenv/pyenv) |
| uv         | latest   | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| go-task    | latest   | `brew install go-task` or [taskfile.dev](https://taskfile.dev) |
| pre-commit | latest   | `uv tool install pre-commit`               |

## Setup

```bash
git clone git@github.com:myxo-lab/myxo-lab.git
cd myxo-lab
uv sync                    # Python deps
pre-commit install         # Git hooks
cp .env.example .env       # Environment variables (edit values)
```

## Testing

```bash
task test      # Run all tests (Python + Rust)
task lint      # Lint all (ruff, clippy, fmt checks)
task check     # Full CI check (lint + test)
```

Individual targets:

```bash
task py:test       # pytest with coverage
task rust:test     # cargo test
task py:lint       # ruff check
task rust:lint     # clippy
```

## Code Style

- **Python**: [Ruff](https://docs.astral.sh/ruff/) — `task py:fmt:fix` to auto-format
- **Rust**: `cargo fmt` — `task rust:fmt:fix` to auto-format
- Run `task fmt` to format everything at once

## Commits

This project uses [gitmoji](https://gitmoji.dev/) commit prefixes.

Format: `<type>: <emoji> <subject>`

Examples:

```
feat: ✨ add workflow dispatch trigger
fix: 🐛 correct token refresh logic
docs: 📝 update CONTRIBUTING guide
test: ✅ add sanitizer edge-case tests
refactor: ♻️ extract rate-limiter module
```

See `.claude/skills/commit-rules/` for the full list.

## Pull Requests

1. Branch from `develop` (`feature/xxx`, `fix/xxx`, etc.)
2. Keep commits focused — one logical change per commit
3. All CI checks must pass before merge
4. PRs are **squash-merged** into `develop`
5. Reference the related issue: `Closes #123`
