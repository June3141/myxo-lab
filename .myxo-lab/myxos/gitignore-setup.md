---
name: gitignore-setup
description: Generate a proper .gitignore using gitignore.io
triggers:
  - Repository initial setup
timeout: 300
env:
  - GITHUB_TOKEN
---

## Steps
1. Detect project languages and frameworks from the repository
2. Query gitignore.io API for relevant templates
3. Merge templates into a single .gitignore file
4. Verify no tracked files would be ignored by the new rules
5. Commit the generated .gitignore

## Rules
- Always include OS-specific ignores (macOS, Windows, Linux)
- Preserve any existing custom rules in .gitignore
- Do not ignore files that are already tracked by git
- Sort sections alphabetically for readability
