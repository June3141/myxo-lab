---
name: code-structure
description: Code structure rules (file size, function size, single responsibility, layer separation). Reference this when writing or reviewing implementation code.
user-invocable: false
---

# Code Structure Rules

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

## When Limits Are Approaching

- Propose file splitting **before** implementation, not after
- Split by responsibility, not by arbitrary line count
- Prefer extracting a cohesive module over mechanical splitting
