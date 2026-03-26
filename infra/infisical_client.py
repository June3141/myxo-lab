"""Infisical client configuration for dynamic secret retrieval.

Defines the mapping of secrets that should be retrieved from Infisical
instead of GitHub Actions secrets, along with project and environment
configuration for the Infisical SDK integration.

Ref: #87 — Migrate to dynamic API key retrieval via Infisical
"""

import pulumi

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config("infisical")
stack = pulumi.get_stack()

# Infisical project identifier (from Pulumi encrypted config)
# Using get_secret to avoid requiring config before Infisical is fully set up
infisical_project_id = config.get_secret("PROJECT_ID")
infisical_client_id = config.get_secret("CLIENT_ID")
infisical_client_secret = config.get_secret("CLIENT_SECRET")

# ---------------------------------------------------------------------------
# Environment mapping — Pulumi stack → Infisical environment slug
# ---------------------------------------------------------------------------
ENVIRONMENT_MAP: dict[str, str] = {
    "dev": "dev",
    "development": "dev",
    "staging": "staging",
    "prod": "prod",
    "production": "prod",
}

if stack not in ENVIRONMENT_MAP:
    pulumi.log.warn(f"Unknown stack '{stack}' — defaulting Infisical environment to 'dev'")
infisical_environment = ENVIRONMENT_MAP.get(stack, "dev")

# ---------------------------------------------------------------------------
# Secret mapping — migration path from GitHub Secrets to Infisical
#
# Each entry defines:
#   - source: where the secret currently lives
#       "infisical"       → retrieve dynamically via Infisical SDK
#       "github_secrets"  → keep in GitHub Actions secrets (Pulumi-managed)
#   - path: Infisical secret path (required for source="infisical")
# ---------------------------------------------------------------------------
SECRET_MAPPING: dict[str, dict[str, str | None]] = {
    # Phase 1: Migrate API keys to Infisical (dynamic retrieval)
    "ANTHROPIC_API_KEY_MYXO": {
        "source": "infisical",
        "path": "/api-keys/anthropic-myxo",
    },
    "ANTHROPIC_API_KEY_SCHEDULED": {
        "source": "infisical",
        "path": "/api-keys/anthropic-scheduled",
    },
    # Phase 2: Keep infrastructure credentials in GitHub Secrets for now
    "AWS_ACCESS_KEY_ID": {"source": "github_secrets", "path": None},
    "AWS_SECRET_ACCESS_KEY": {"source": "github_secrets", "path": None},
    "PULUMI_ACCESS_TOKEN": {"source": "github_secrets", "path": None},
    # GitHub App credentials — keep in GitHub Secrets
    "GITHUB_APP_PRIVATE_KEY": {"source": "github_secrets", "path": None},
    "MYXO_APP_ID": {"source": "github_secrets", "path": None},
}

# Derived lists for convenience
INFISICAL_SECRETS = [k for k, v in SECRET_MAPPING.items() if v["source"] == "infisical"]
GITHUB_SECRETS = [k for k, v in SECRET_MAPPING.items() if v["source"] == "github_secrets"]

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
pulumi.export("infisical_environment", infisical_environment)
pulumi.export("infisical_secret_count", len(INFISICAL_SECRETS))
pulumi.export("github_secret_count", len(GITHUB_SECRETS))
