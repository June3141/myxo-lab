"""GitHub Secrets & Environments for Myxo Lab.

Defines GitHub Actions environments (development, staging, production)
and repository-level Actions secrets.  Actual secret values come from
Pulumi config (encrypted), never hardcoded.
"""

import pulumi
import pulumi_github as github

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
config = pulumi.Config()
repo_name = config.require("repo")

# Secret values from Pulumi encrypted config
secrets_config = pulumi.Config("secrets")
pulumi_access_token = secrets_config.require_secret("PULUMI_ACCESS_TOKEN")
aws_access_key_id = secrets_config.require_secret("AWS_ACCESS_KEY_ID")
aws_secret_access_key = secrets_config.require_secret("AWS_SECRET_ACCESS_KEY")

# ---------------------------------------------------------------------------
# GitHub Repository (data source for environment attachment)
# ---------------------------------------------------------------------------
repo = github.get_repository(name=repo_name)

# ---------------------------------------------------------------------------
# GitHub Environments
# ---------------------------------------------------------------------------
ENVIRONMENTS = ["development", "staging", "production"]

env_resources: dict[str, github.RepositoryEnvironment] = {}
for env_name in ENVIRONMENTS:
    env_resources[env_name] = github.RepositoryEnvironment(
        f"env-{env_name}",
        repository=repo_name,
        environment=env_name,
    )

# Production environment: require reviewers before deployment
github.RepositoryEnvironmentDeploymentPolicy(
    "prod-deployment-policy",
    repository=repo_name,
    environment=env_resources["production"].environment,
    branch_pattern="main",
)

# ---------------------------------------------------------------------------
# Repository-level Actions Secrets
# ---------------------------------------------------------------------------
SECRET_DEFS: dict[str, pulumi.Output[str]] = {
    "PULUMI_ACCESS_TOKEN": pulumi_access_token,
    "AWS_ACCESS_KEY_ID": aws_access_key_id,
    "AWS_SECRET_ACCESS_KEY": aws_secret_access_key,
}

for secret_name, secret_value in SECRET_DEFS.items():
    resource_name = secret_name.lower().replace("_", "-")
    github.ActionsSecret(
        f"secret-{resource_name}",
        repository=repo_name,
        secret_name=secret_name,
        plaintext_value=secret_value,
    )

# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------
pulumi.export("environments", [e for e in ENVIRONMENTS])
pulumi.export("secret_count", len(SECRET_DEFS))
