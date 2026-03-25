"""GitHub App permission and event metadata.

Defines the required permissions and webhook events for the Myxo Lab GitHub App.
The App itself must be registered manually at https://github.com/settings/apps/new.
This module exports the configuration as Pulumi stack outputs for reference.
"""

import pulumi

app_config = pulumi.Config("github-app")
app_slug = app_config.get("slug") or "myxo-lab-bot"

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
