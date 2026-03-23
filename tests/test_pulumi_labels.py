"""Tests for Pulumi GitHub labels and branch protection definitions."""

from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parent.parent / "infra"

EXPECTED_LABELS = [
    "state: pseudopod-ready",
    "state: pseudopod-active",
    "state: pseudopod-abort",
    "state: pseudopod-complete",
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


class TestIssueLabelDefinitions:
    """IssueLabel resources must be declared for every Myxo label."""

    def test_issue_label_resource_used(self):
        content = _read_main()
        assert "github.IssueLabel(" in content, (
            "__main__.py must use github.IssueLabel to declare labels"
        )

    def test_all_expected_labels_defined(self):
        content = _read_main()
        for label in EXPECTED_LABELS:
            assert f'"{label}"' in content or f"'{label}'" in content, (
                f"Label '{label}' must be defined in __main__.py"
            )

    def test_repo_name_from_config(self):
        content = _read_main()
        assert "pulumi.Config" in content or "config.require" in content, (
            "Repo name should come from Pulumi config, not be hardcoded"
        )


class TestBranchProtection:
    """Branch protection rules must be declared for main and develop."""

    def test_branch_protection_resource_used(self):
        content = _read_main()
        assert "github.BranchProtection(" in content, (
            "__main__.py must use github.BranchProtection"
        )

    def test_main_branch_protected(self):
        content = _read_main()
        assert '"main"' in content or "'main'" in content, (
            "main branch must be referenced for protection"
        )

    def test_develop_branch_protected(self):
        content = _read_main()
        assert '"develop"' in content or "'develop'" in content, (
            "develop branch must be referenced for protection"
        )

    def test_require_pr_reviews(self):
        content = _read_main()
        assert "required_pull_request_reviews" in content, (
            "main branch protection must require PR reviews"
        )

    def test_require_status_checks(self):
        content = _read_main()
        assert "required_status_checks" in content, (
            "Branch protection must require status checks"
        )

    def test_pr_title_lint_check(self):
        content = _read_main()
        assert "pr-title-lint" in content, (
            "Status checks must include pr-title-lint"
        )

    def test_no_force_pushes_on_main(self):
        content = _read_main()
        assert "allows_force_pushes" in content, (
            "Force push setting must be explicitly configured"
        )
