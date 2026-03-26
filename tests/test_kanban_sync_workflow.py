"""Tests for kanban-sync GitHub Actions workflow."""

from pathlib import Path

from helpers import get_on_block, load_workflow

WORKFLOW_PATH = Path(__file__).parent.parent / ".github" / "workflows" / "kanban-sync.yml"

EXPECTED_LABELS = [
    "state: myxo-ready",
    "state: myxo-active",
    "state: myxo-abort",
    "state: myxo-complete",
    "state: researcher-review",
]


def _load_kanban_workflow() -> dict:
    """Load and parse the workflow YAML."""
    return load_workflow(WORKFLOW_PATH)


def test_workflow_file_exists():
    """Workflow YAML file must exist."""
    assert WORKFLOW_PATH.is_file(), f"{WORKFLOW_PATH} does not exist"


def test_workflow_is_valid_yaml():
    """Workflow file must be valid YAML that parses without error."""
    data = _load_kanban_workflow()
    assert isinstance(data, dict)


def test_trigger_on_issues_labeled():
    """Workflow must trigger on issues labeled event."""
    data = _load_kanban_workflow()
    on_block = get_on_block(data)
    issues_cfg = on_block.get("issues", {})
    assert "labeled" in issues_cfg.get("types", [])


def test_references_all_state_labels():
    """Workflow must reference every expected state label."""
    content = WORKFLOW_PATH.read_text()
    for label in EXPECTED_LABELS:
        assert label in content, f"Missing label reference: {label}"


def test_has_permissions_block():
    """Workflow must declare a permissions block."""
    data = _load_kanban_workflow()
    assert "permissions" in data, "Top-level permissions block missing"
    perms = data["permissions"]
    assert "issues" in perms
    assert "repository-projects" in perms


def test_no_expression_injection_in_run_blocks():
    """Run blocks must not contain ${{ }} expressions (security)."""
    data = _load_kanban_workflow()
    jobs = data.get("jobs", {})
    for job_name, job_cfg in jobs.items():
        for step in job_cfg.get("steps", []):
            run_block = step.get("run", "")
            assert "${{" not in run_block, (
                f"Expression injection risk in job '{job_name}', "
                f"step '{step.get('name', '?')}': run block contains ${{{{ }}}}"
            )
