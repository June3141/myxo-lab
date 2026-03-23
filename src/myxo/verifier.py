"""GitHub settings verifier for myxo verify command."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Literal

import httpx


async def _resolve_json(resp: Any) -> Any:
    """Call resp.json(), awaiting if necessary (for mock compatibility)."""
    result = resp.json()
    if inspect.isawaitable(result):
        return await result
    return result


@dataclass
class CheckResult:
    """Result of a single verification check."""

    name: str
    status: Literal["ok", "fail", "warn"]
    message: str


class GitHubVerifier:
    """Verifies GitHub repository settings against .myxo/ configuration."""

    API_BASE = "https://api.github.com"

    def __init__(self, token: str) -> None:
        self.token = token
        self._headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }

    # ------------------------------------------------------------------
    # Labels
    # ------------------------------------------------------------------

    async def check_labels(
        self, repo: str, expected: list[dict[str, str]]
    ) -> list[CheckResult]:
        """Check that all expected labels exist on the repository."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.API_BASE}/repos/{repo}/labels",
                headers=self._headers,
            )

        data = await _resolve_json(resp) if resp.status_code == 200 else []
        existing = {lbl["name"] for lbl in data}

        results: list[CheckResult] = []
        for label in expected:
            name = label["name"]
            if name in existing:
                results.append(
                    CheckResult(name=f"label: {name}", status="ok", message="exists")
                )
            else:
                results.append(
                    CheckResult(
                        name=f"label: {name}", status="fail", message="missing"
                    )
                )
        return results

    async def fix_labels(
        self, repo: str, expected: list[dict[str, str]]
    ) -> None:
        """Create missing labels on the repository."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.API_BASE}/repos/{repo}/labels",
                headers=self._headers,
            )

        data = await _resolve_json(resp) if resp.status_code == 200 else []
        existing = {lbl["name"] for lbl in data}

        async with httpx.AsyncClient() as client:
            for label in expected:
                if label["name"] not in existing:
                    await client.post(
                        f"{self.API_BASE}/repos/{repo}/labels",
                        headers=self._headers,
                        json={"name": label["name"], "color": label.get("color", "")},
                    )

    # ------------------------------------------------------------------
    # Branch Protection
    # ------------------------------------------------------------------

    async def check_branch_protection(
        self, repo: str, config: dict[str, Any]
    ) -> list[CheckResult]:
        """Check branch protection settings."""
        branch = config["branch"]

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.API_BASE}/repos/{repo}/branches/{branch}/protection",
                headers=self._headers,
            )

        results: list[CheckResult] = []

        if resp.status_code == 404:
            results.append(
                CheckResult(
                    name=f"branch_protection: {branch}",
                    status="fail",
                    message="not configured",
                )
            )
            return results

        data = await _resolve_json(resp)
        pr_reviews = data.get("required_pull_request_reviews", {})

        # Check required review count
        actual_reviews = pr_reviews.get("required_approving_review_count", 0)
        expected_reviews = config.get("required_reviews", 1)

        if actual_reviews >= expected_reviews:
            results.append(
                CheckResult(
                    name=f"branch_protection: {branch}",
                    status="ok",
                    message=f"required_reviews={actual_reviews}",
                )
            )
        else:
            results.append(
                CheckResult(
                    name=f"branch_protection: {branch}",
                    status="fail",
                    message=f"required_reviews={actual_reviews}, expected>={expected_reviews}",
                )
            )

        # Check dismiss stale reviews
        if config.get("dismiss_stale_reviews"):
            actual_dismiss = pr_reviews.get("dismiss_stale_reviews", False)
            if actual_dismiss:
                results.append(
                    CheckResult(
                        name=f"branch_protection: {branch} dismiss_stale",
                        status="ok",
                        message="enabled",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        name=f"branch_protection: {branch} dismiss_stale",
                        status="warn",
                        message="not enabled",
                    )
                )

        return results

    async def fix_branch_protection(
        self, repo: str, config: dict[str, Any]
    ) -> None:
        """Update branch protection to match configuration."""
        branch = config["branch"]
        async with httpx.AsyncClient() as client:
            await client.put(
                f"{self.API_BASE}/repos/{repo}/branches/{branch}/protection",
                headers=self._headers,
                json={
                    "required_pull_request_reviews": {
                        "required_approving_review_count": config.get(
                            "required_reviews", 1
                        ),
                        "dismiss_stale_reviews": config.get(
                            "dismiss_stale_reviews", False
                        ),
                    },
                    "enforce_admins": True,
                    "required_status_checks": None,
                    "restrictions": None,
                },
            )

    # ------------------------------------------------------------------
    # Secrets
    # ------------------------------------------------------------------

    async def check_secrets(
        self, repo: str, expected: list[str]
    ) -> list[CheckResult]:
        """Check that all expected secrets are configured."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.API_BASE}/repos/{repo}/actions/secrets",
                headers=self._headers,
            )

        existing: set[str] = set()
        if resp.status_code == 200:
            data = await _resolve_json(resp)
            existing = {s["name"] for s in data.get("secrets", [])}

        results: list[CheckResult] = []
        for secret_name in expected:
            if secret_name in existing:
                results.append(
                    CheckResult(
                        name=f"secret: {secret_name}",
                        status="ok",
                        message="configured",
                    )
                )
            else:
                results.append(
                    CheckResult(
                        name=f"secret: {secret_name}",
                        status="fail",
                        message="not found",
                    )
                )
        return results
