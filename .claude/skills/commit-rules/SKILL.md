---
name: commit-rules
description: Commit message format (gitmoji), PR template, and commit granularity rules for the Myxo Lab project. Reference this when creating commits or pull requests.
user-invocable: false
---

# Commit & PR Rules

## Commit Message Format

```
<type>: <emoji> <subject>

<body>

<footer>
```

### Type (required)

| Type | When to use |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `test` | Add or update tests |
| `refactor` | Refactor (no behavior change) |
| `chore` | Build, CI, or config changes |
| `style` | Code formatting only |
| `perf` | Performance improvement |

### Emoji (required) — gitmoji

Place after the colon. Full list is generated from upstream and stored in `.claude/hooks/gitmoji-pattern.txt`.
Commonly used:

| Emoji | Meaning |
|-------|---------|
| ✨ | New feature |
| 🐛 | Bug fix |
| 📝 | Documentation only |
| ✅ | Add or update tests |
| ♻️ | Refactor (no behavior change) |
| 🔧 | Build, CI, or config changes |
| 🎨 | Code formatting only |
| ⚡️ | Performance improvement |
| 🔥 | Remove code or files |
| 💥 | Breaking change |
| 🚀 | Deploy |
| 🚧 | Work in progress |
| 🔒 | Security fix |
| ⬆️ | Upgrade dependencies |
| 🗃️ | Database migration |
| 🎉 | Initial commit |

### Subject (required)

- English, lowercase start, no trailing period
- 50 characters max
- Imperative mood: "add", "fix", "remove" (not "added", "fixed")

### Body (optional)

- Explain **why**, not what (the diff shows what)
- Wrap at 72 characters

### Footer (optional)

- `BREAKING CHANGE: <description>`
- `Closes #<issue>` / `Refs #<issue>`

### Examples

```
feat: ✨ add hypothesis tracking endpoint

The /hypotheses endpoint enables tracking of active experiments.
This will be used by the Protocol agent for task decomposition.
```

```
test: ✅ add pseudopod execution tests

Write failing tests first per TDD workflow.
Tests cover spawn, execute, and report operations.

Refs #12
```

## Commit Granularity Rules

### Code Changes

- Max **10 files** per commit
- Max **300 lines** added+deleted (excluding tests and auto-generated files)
- **1 commit = 1 concern** — never mix feat and fix in the same commit
- Auto-generated files (uv.lock, package-lock.json) do not count toward limits
- If limits are exceeded, split the commit. If splitting is impractical, explain why in the body.

### Test Code

- **1 commit = tests for 1 feature** (one module, one component)
- Name the test target explicitly in the subject
- Max **5 test files** per commit
- Related unit + integration tests for the same module may be combined

### TDD Commit Pattern

Always separate test commits from implementation commits:

```
test: ✅ add pseudopod execution tests          ← tests only (expected to fail)
feat: ✨ implement pseudopod execution           ← implementation (tests pass)
refactor: ♻️ extract experiment validation logic ← refactor (tests still pass)
```

- TDD test commits MUST be made before the implementation commit
- Test commits are in a failing state — note this in the body if needed
- Never modify tests during the implementation phase

## Pull Request Rules

See `pr-rules` skill for full PR creation rules (merge strategy, labels, milestones, assignees).

PR titles follow the same format as commit messages (squash merge makes the title the final commit).

## Language

All commit messages and PR descriptions must be in **English**.
