---
name: pr-rules
description: PR creation rules for Myxo Lab. Enforces squash merge conventions, title format, labels, milestones, and assignees. Reference this when creating pull requests.
user-invocable: false
---

# Pull Request Rules

## Merge Strategy

| Target branch | Merge method | Why |
|---------------|-------------|-----|
| `develop` | **Squash merge** | Clean history — PR title becomes the commit message |
| `main` | **Merge commit** | Preserve develop history on release |

Because PRs to `develop` are squash-merged, the **PR title IS the final commit message**. Follow commit-rules format exactly.

## PR Title Format

```
<type>: <emoji> <subject>
```

- Same rules as commit messages (see commit-rules skill)
- English, lowercase start, no trailing period, imperative mood
- Max 70 characters
- Examples:
  - `feat: ✨ implement myxo init command`
  - `fix: 🐛 resolve experiment scheduling race condition`

## PR Body Template

```markdown
## Summary
<1-3 sentences describing the change>

Closes #<issue>
```

- `Closes #N` for issues being resolved, `Refs #N` for related issues
- All PRs must reference related issues when applicable
- **Do NOT include Test plan in the PR body**

## Test Plan Comment

After creating the PR, post a **separate comment** with the test plan:

```bash
gh pr comment <PR_NUMBER> --repo June3141/myxo-lab --body "$(cat <<'EOF'
## Test plan
- [x] Verification steps as checklist
EOF
)"
```

## Labels

Use existing labels from the repository. Match based on the change:

| Category | Labels |
|----------|--------|
| Layer | `layer: cli`, `layer: infra`, `layer: workflow`, `layer: github`, `layer: security` |
| Priority | `priority: critical`, `priority: high`, `priority: medium`, `priority: low` |

Do NOT create new labels. If no label fits, omit it.

## Milestone

Assign the appropriate milestone based on the issue being closed:

| Milestone | When |
|-----------|------|
| `Phase 1: PoC` | Foundation, CLI, Pulumi, GitHub Actions, MCP, security |
| `Phase 2: 本番化` | Temporal, Protocol/Assay agents, GitHub App |
| `Phase 3: 拡張` | OSS release, cost monitoring, auto-rollback |

## Assignee

Always assign the PR to the current GitHub user (the operator running Claude Code).
Determine with: `gh api user --jq '.login'`

## Branch Strategy

- Feature branches: `feature/<name>` from `develop`
- PRs target: `develop`
- `main` is protected — no direct pushes

## gh pr create Example

```bash
ASSIGNEE=$(gh api user --jq '.login')

# Step 1: Create PR (no test plan in body)
gh pr create \
  --base develop \
  --title "feat: ✨ implement myxo init command" \
  --label "layer: cli" \
  --milestone "Phase 1: PoC" \
  --assignee "$ASSIGNEE" \
  --body "$(cat <<'EOF'
## Summary
Implement `myxo init` to scaffold `.myxo/` directory structure.

Closes #7
EOF
)"

# Step 2: Post test plan as separate comment
gh pr comment <PR_NUMBER> --repo June3141/myxo-lab --body "$(cat <<'EOF'
## Test plan
- [x] `uv run pytest -v` passes all tests
- [x] `myxo init` creates expected directory structure
EOF
)"
```

## Language

All PR titles and descriptions must be in **English**.
