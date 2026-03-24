---
name: python-code-structure
description: Python code structure rules for src/myxo/ (file size, function size, single responsibility, layer separation). Reference this when writing or reviewing Python implementation code.
user-invocable: false
---

# Python Code Structure Rules

## File Size

- Source files: **300 lines max** (excludes tests and auto-generated files)
- When exceeding: extract functionality into a separate module
- Exceptions allowed only with justification in a comment

## Function / Method Size

- **50 lines max** per function or method
- When exceeding: split into helper functions or private methods
- Test helpers and fixtures are exempt

## Single Responsibility

- Each module focuses on **one concern**
- Litmus test: can you describe what this file does in one sentence?
- A dataclass + its associated logic may live in the same file
- Examples from this codebase:
  - `rate_limiter.py` — GitHub API rate limit parsing only
  - `sanitizer.py` — secret detection only

## Layer Separation

| Layer | Location | Responsibility | May depend on |
|-------|----------|---------------|---------------|
| CLI | `cli.py` | User I/O, Typer command definitions only | Domain |
| Domain | `src/myxo/*.py` | Core business logic | (interfaces only) |
| Infra | `infra/` | Pulumi resource definitions, cloud config | Domain |
| Tests | `tests/` | 1:1 mapping with source (`test_{module}.py`) | Domain, CLI |

**Dependency direction:** CLI → Domain ← Infra (no reverse dependencies)

- CLI must not contain business logic — delegate to domain modules
- Domain modules must not import from CLI or infra directly

## Gotchas

- `__init__.py` is exempt from single responsibility — it serves as the package's public API surface
- Test files often exceed 300 lines because of fixtures and parametrized cases — this is expected
- `cli.py` tends to grow as commands are added; when it exceeds 300 lines, split into `cli/` package with one file per command group
- Pulumi infra files (`infra/`) follow Pulumi conventions (resource definitions in sequence), not general domain patterns — layer separation rules still apply but internal structure may differ
- Auto-generated files (`uv.lock`, `package-lock.json`) and config files (`pyproject.toml`) are exempt from all limits

## Validation

After writing or modifying source files, verify limits:

```bash
# Check file sizes (source files only, excludes tests and auto-generated)
find src/ -name '*.py' ! -name '__init__.py' -exec awk 'END{if(NR>300) print FILENAME": "NR" lines"}' {} \;

# Check function sizes
ruff check --select E302 src/
```

If any file exceeds 300 lines, propose a split before committing.

## When Limits Are Approaching

- Propose file splitting **before** implementation, not after
- Split by responsibility, not by arbitrary line count
- Prefer extracting a cohesive module over mechanical splitting
