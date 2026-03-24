---
name: testing
description: Project-wide testing strategy and conventions
triggers:
  - writing tests
  - reviewing test code
  - setting up test infrastructure
---

## Steps

1. Classify the test by size (Small / Medium / Large) before writing it
2. Apply the corresponding pytest marker (`@pytest.mark.small`, `@pytest.mark.medium`, `@pytest.mark.large`)
3. Follow the TDD cycle: write a failing test (RED), implement until it passes (GREEN), then refactor (REFACTOR)
4. Run the full suite with `uv run pytest` and confirm no regressions
5. When investigating coverage gaps, use `uv run pytest --cov` (requires `pytest-cov`)
6. Lint test code with `uv run ruff check`

## Rules

### Test Sizes

| Size   | Marker            | Scope                        | Network | Filesystem | Timeout |
|--------|-------------------|------------------------------|---------|------------|---------|
| Small  | `@pytest.mark.small`  | Pure logic, single function  | No      | No         | Fast    |
| Medium | `@pytest.mark.medium` | Module integration, fixtures | Mocked  | Temp only  | Moderate|
| Large  | `@pytest.mark.large`  | End-to-end, external deps    | Allowed | Allowed    | Slow    |

- Tests without an explicit marker are auto-classified as **small** by conftest.py.
- CI runs `small` and `medium` tests on PRs via `-m "small or medium"`; `large` tests run on scheduled builds.

### TDD Cycle

- **RED**: Write the test first. It must fail for the right reason.
- **GREEN**: Write the minimum code to make the test pass.
- **REFACTOR**: Clean up without changing behavior; all tests must stay green.
- Commit at each phase boundary (failing test, passing test, refactored code).

### Coverage

- Use coverage as a **discovery tool** to find untested code paths, not as a sufficiency metric.
- Do not set hard coverage thresholds that encourage low-value tests.
- Focus test effort on business logic and error handling.

### Layer-Specific Strategies

- **CLI (`src/myxo/cli.py`)**: Test command parsing and output format; mock underlying services.
- **Infrastructure (`infra/`)**: Validate Pulumi resource declarations via unit tests; use `pulumi.runtime.set_mocks()`.
- **Workflow (`.github/workflows/`)**: Prefer act or manual smoke tests; keep CI YAML minimal and composable.

### Mock Usage

- Prefer dependency injection over monkey-patching.
- Mock at the boundary (network, filesystem, external API), not deep inside the unit.
- Use `pytest` fixtures and `unittest.mock.patch` for isolation.
- Never mock the code under test itself.
