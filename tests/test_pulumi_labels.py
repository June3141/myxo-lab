"""Tests for Pulumi GitHub labels and branch protection definitions."""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"

EXPECTED_LABELS = [
    "state: myxo-ready",
    "state: myxo-active",
    "state: myxo-abort",
    "state: myxo-complete",
    "state: researcher-review",
    "state: scheduled-experiment",
    "state: hypothesis-hold",
    "layer: infra",
    "layer: workflow",
    "layer: cli",
    "layer: security",
    "layer: github",
    "priority: critical",
    "priority: high",
    "priority: medium",
    "priority: low",
    "type: epic",
]


def _read_main() -> str:
    return (INFRA_DIR / "__main__.py").read_text()


def _extract_block(content: str, resource_name: str) -> str:
    """Extract code block for a named Pulumi resource."""
    start = content.find(f'"{resource_name}"')
    if start == -1:
        return ""
    # Find the next top-level resource or end of file
    next_resource = content.find("\ngithub.", start + 1)
    if next_resource == -1:
        return content[start:]
    return content[start:next_resource]


# --- Issue Labels ---


def test_issue_label_resource_used():
    content = _read_main()
    assert "github.IssueLabel(" in content, "__main__.py must use github.IssueLabel to declare labels"


def test_all_expected_labels_defined():
    content = _read_main()
    for label in EXPECTED_LABELS:
        assert f'"{label}"' in content or f"'{label}'" in content, f"Label '{label}' must be defined in __main__.py"


def test_repo_name_from_config():
    content = _read_main()
    assert "pulumi.Config" in content or "config.require" in content, (
        "Repo name should come from Pulumi config, not be hardcoded"
    )
    assert "repo_name" in content, "Repo name should be stored in a variable (e.g., repo_name)"
    uses_repo_var = any(
        pattern in content
        for pattern in (
            "repository=repo_name",
            "repository = repo_name",
            "repository_id=repo_name",
            "repository_id = repo_name",
        )
    )
    assert uses_repo_var, "IssueLabel/BranchProtection must use config-derived repo variable"


# --- Branch Protection ---


def test_branch_protection_resource_used():
    content = _read_main()
    assert "github.BranchProtection(" in content


def test_main_branch_protected():
    content = _read_main()
    assert '"main"' in content or "'main'" in content


def test_develop_branch_protected():
    content = _read_main()
    assert '"develop"' in content or "'develop'" in content


def test_require_pr_reviews_on_main():
    content = _read_main()
    block = _extract_block(content, "protect-main")
    assert block, "protect-main resource must be defined"
    assert "required_pull_request_reviews" in block, "main branch protection must require PR reviews"


def test_require_status_checks():
    content = _read_main()
    assert "required_status_checks" in content


def test_pr_title_lint_check():
    content = _read_main()
    assert "pr-title-lint" in content


def test_no_force_pushes_on_main():
    content = _read_main()
    block = _extract_block(content, "protect-main")
    assert block, "protect-main resource must be defined"
    assert "allows_force_pushes=False" in block or "allows_force_pushes = False" in block, (
        "main branch protection must disallow force pushes"
    )
