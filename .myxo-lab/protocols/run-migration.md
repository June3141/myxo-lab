---
name: run-migration
description: Database migration execution procedure
triggers:
  - migration
  - migrate
  - run-migration
---

## Steps
1. Check the current migration state
2. Create a new migration file
3. Review the migration contents
4. Run the migration
5. Verify the results

## Rules
- Take a backup before running in production
- Prepare a rollback plan for destructive changes
- Ensure migrations are idempotent
- Pass migration tests in CI before merging
