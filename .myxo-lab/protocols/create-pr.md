---
name: create-pr
description: Pull request creation procedure
triggers:
  - pr
  - pull-request
  - create-pr
---

## Steps
1. Verify the current branch and base branch
2. Review the diff and stage changes
3. Write a commit message
4. Push to the remote
5. Create the PR with `gh pr create`

## Rules
- Keep the PR title under 70 characters
- Include a Summary section in the body
- Use develop as the base branch
- Link related issues with Closes #XX
