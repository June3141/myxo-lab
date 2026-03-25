"""GitHub App registration and permission configuration.

Defines the Myxo Lab GitHub App with required permissions and webhook events.
The App provides authenticated API access for mxl verify, syncer, and
automated issue/PR management.

Note: The actual App must be registered manually on GitHub first.
This module manages the installation and permission configuration via Pulumi.
"""

import pulumi

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config()
repo_name = config.require("repo")

app_config = pulumi.Config("github-app")
app_slug = app_config.get("slug") or "myxo-lab-bot"

# ---------------------------------------------------------------------------
# GitHub App Installation Repository
# ---------------------------------------------------------------------------
# The App must be created manually at https://github.com/settings/apps/new
# with the following permissions and events configured below.
#
# After creation, install it on the repository and note the installation ID.

# Required permissions for myxo operations:
# - issues: write       — create/update issues (verify drift, procedure flow)
# - pull_requests: write — create PRs (auto-fix, protocol generation)
# - contents: write     — push commits (sync, auto-fix)
# - actions: read       — read workflow run status

PERMISSIONS = {
    "issues": "write",
    "pull_requests": "write",
    "contents": "write",
    "actions": "read",
}

# Webhook events the App subscribes to:
WEBHOOK_EVENTS = [
    "issues",
    "pull_request",
    "push",
    "workflow_run",
]

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
pulumi.export("github_app_slug", app_slug)
pulumi.export("github_app_permissions", PERMISSIONS)
pulumi.export("github_app_events", WEBHOOK_EVENTS)
