"""Myxo Lab infrastructure definition."""

import pulumi
import pulumi_github as github

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config()
repo_name = config.require("repo")

# ---------------------------------------------------------------------------
# Issue Labels
# ---------------------------------------------------------------------------
LABELS: dict[str, str] = {
    # state
    "state: myxo-ready": "0e8a16",
    "state: myxo-active": "1d76db",
    "state: myxo-abort": "b60205",
    "state: myxo-complete": "0e8a16",
    "state: researcher-review": "fbca04",
    "state: scheduled-experiment": "c5def5",
    "state: hypothesis-hold": "d4c5f9",
    # layer
    "layer: infra": "bfd4f2",
    "layer: workflow": "bfd4f2",
    "layer: cli": "bfd4f2",
    "layer: security": "bfd4f2",
    "layer: github": "bfd4f2",
    # priority
    "priority: critical": "b60205",
    "priority: high": "d93f0b",
    "priority: medium": "fbca04",
    "priority: low": "0e8a16",
    # type
    "type: epic": "3e4b9e",
}

for label_name, color in LABELS.items():
    resource_name = label_name.replace(" ", "-").replace(":", "")
    github.IssueLabel(
        resource_name,
        repository=repo_name,
        name=label_name,
        color=color,
    )

# ---------------------------------------------------------------------------
# Branch Protection — main
# ---------------------------------------------------------------------------
github.BranchProtection(
    "protect-main",
    repository_id=repo_name,
    pattern="main",
    required_pull_request_reviews=[
        github.BranchProtectionRequiredPullRequestReviewArgs(
            required_approving_review_count=1,
            dismiss_stale_reviews=True,
        )
    ],
    required_status_checks=[
        github.BranchProtectionRequiredStatusCheckArgs(
            strict=True,
            contexts=["pr-title-lint"],
        )
    ],
    allows_force_pushes=False,
    allows_deletions=False,
)

# ---------------------------------------------------------------------------
# Branch Protection — develop
# ---------------------------------------------------------------------------
github.BranchProtection(
    "protect-develop",
    repository_id=repo_name,
    pattern="develop",
    required_status_checks=[
        github.BranchProtectionRequiredStatusCheckArgs(
            strict=True,
            contexts=["pr-title-lint"],
        )
    ],
    allows_force_pushes=False,
    allows_deletions=False,
)

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
pulumi.export("status", "initialized")
pulumi.export("label_count", len(LABELS))
