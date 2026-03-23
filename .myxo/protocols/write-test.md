---
name: write-test
description: Test writing procedure
triggers:
  - test
  - write-test
  - tdd
---

## Steps
1. Review the specification and expected behavior of the target
2. Create a test file or add to an existing one
3. Write a failing test (RED)
4. Run the test and confirm it fails
5. Confirm the test is correct and commit
6. Write the implementation to make the test pass (GREEN)
7. Refactor (REFACTOR)

## Rules
- Follow the TDD cycle
- Place tests in the `tests/` directory
- Run tests with `uv run pytest`
- Prefix test filenames with `test_`
- Each test must be independently runnable
