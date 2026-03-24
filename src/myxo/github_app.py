"""GitHub App Installation Token generation.

Generates short-lived installation tokens by:
1. Creating a JWT signed with the App's private key (RS256).
2. Exchanging the JWT for an installation access token via the GitHub API.
"""

from __future__ import annotations

import time

import httpx
import jwt


def generate_jwt(app_id: str, private_key: str) -> str:
    """Generate a JWT for GitHub App authentication.

    Args:
        app_id: The GitHub App ID.
        private_key: RSA private key in PEM format (string).

    Returns:
        Encoded JWT string.

    Raises:
        ValueError: If the private key is invalid.
    """
    now = int(time.time())
    payload = {
        "iat": now - 60,  # issued at: 60s in the past (clock drift tolerance)
        "exp": now + 600,  # expires: 10 minutes from now (GitHub max)
        "iss": app_id,
    }
    try:
        return jwt.encode(payload, private_key, algorithm="RS256")
    except Exception as exc:
        raise ValueError(f"Failed to sign JWT — check private key: {exc}") from exc


def get_installation_token(jwt_token: str, installation_id: str) -> dict:
    """Exchange a JWT for a GitHub App installation access token.

    Args:
        jwt_token: JWT string from :func:`generate_jwt`.
        installation_id: The installation ID for the target org/repo.

    Returns:
        Dict with ``token`` and ``expires_at`` keys.

    Raises:
        httpx.HTTPStatusError: On non-2xx responses from GitHub.
    """
    url = f"https://api.github.com/app/installations/{installation_id}/access_tokens"
    headers = {
        "Authorization": f"Bearer {jwt_token}",
        "Accept": "application/vnd.github+json",
    }
    response = httpx.post(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    return {"token": data["token"], "expires_at": data["expires_at"]}


def create_installation_token(app_id: str, private_key: str, installation_id: str) -> dict:
    """Convenience: generate JWT and exchange it for an installation token.

    Args:
        app_id: The GitHub App ID.
        private_key: RSA private key in PEM format (string).
        installation_id: The installation ID for the target org/repo.

    Returns:
        Dict with ``token`` and ``expires_at`` keys.
    """
    token = generate_jwt(app_id, private_key)
    return get_installation_token(token, installation_id)
