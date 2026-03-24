"""Tests for GitHub App Installation Token generation."""

from __future__ import annotations

import base64
import json
import time
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from myxo.github_app import create_installation_token, generate_jwt, get_installation_token

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _generate_test_private_key() -> str:
    """Generate a fresh RSA-2048 private key in PEM format for testing."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


# Module-level fixture (generated once per test session).
_TEST_PRIVATE_KEY = _generate_test_private_key()


# ---------------------------------------------------------------------------
# generate_jwt
# ---------------------------------------------------------------------------


class TestGenerateJwt:
    """Tests for generate_jwt."""

    def test_jwt_has_three_segments(self):
        """JWT must be three dot-separated base64url segments."""
        token = generate_jwt("12345", _TEST_PRIVATE_KEY)
        parts = token.split(".")
        assert len(parts) == 3

    def test_jwt_segments_are_base64url(self):
        """Each segment should be valid base64url."""
        token = generate_jwt("12345", _TEST_PRIVATE_KEY)
        for segment in token.split("."):
            # base64url decode (add padding)
            padded = segment + "=" * (4 - len(segment) % 4)
            base64.urlsafe_b64decode(padded)  # should not raise

    def test_jwt_claims_contain_iss(self):
        """JWT payload must contain 'iss' matching the app_id."""
        token = generate_jwt("12345", _TEST_PRIVATE_KEY)
        payload = _decode_jwt_payload(token)
        assert payload["iss"] == "12345"

    def test_jwt_claims_contain_iat(self):
        """JWT payload must contain 'iat' claim."""
        token = generate_jwt("12345", _TEST_PRIVATE_KEY)
        payload = _decode_jwt_payload(token)
        assert "iat" in payload

    def test_jwt_claims_contain_exp(self):
        """JWT payload must contain 'exp' claim."""
        token = generate_jwt("12345", _TEST_PRIVATE_KEY)
        payload = _decode_jwt_payload(token)
        assert "exp" in payload

    def test_jwt_iat_has_clock_drift_tolerance(self):
        """iat should be ~60 seconds in the past."""
        now = time.time()
        token = generate_jwt("12345", _TEST_PRIVATE_KEY)
        payload = _decode_jwt_payload(token)
        # iat should be now - 60, with some tolerance
        assert payload["iat"] == pytest.approx(now - 60, abs=5)

    def test_jwt_exp_is_ten_minutes_from_now(self):
        """exp should be ~10 minutes (600s) in the future."""
        now = time.time()
        token = generate_jwt("12345", _TEST_PRIVATE_KEY)
        payload = _decode_jwt_payload(token)
        assert payload["exp"] == pytest.approx(now + 600, abs=5)

    def test_jwt_uses_rs256_algorithm(self):
        """JWT header must specify RS256 algorithm."""
        token = generate_jwt("12345", _TEST_PRIVATE_KEY)
        header = _decode_jwt_header(token)
        assert header["alg"] == "RS256"

    def test_invalid_private_key_raises(self):
        """Invalid private key should raise ValueError."""
        with pytest.raises(ValueError, match="private key"):
            generate_jwt("12345", "not-a-valid-key")


# ---------------------------------------------------------------------------
# get_installation_token
# ---------------------------------------------------------------------------


class TestGetInstallationToken:
    """Tests for get_installation_token."""

    def test_makes_post_request_with_correct_url(self):
        """Should POST to the correct GitHub API endpoint."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "ghs_abc123",
            "expires_at": "2026-03-24T12:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("myxo.github_app.httpx.post", return_value=mock_response) as mock_post:
            get_installation_token("fake-jwt", "99999")
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == "https://api.github.com/app/installations/99999/access_tokens"

    def test_sends_authorization_header(self):
        """Should include Bearer JWT in Authorization header."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "ghs_abc123",
            "expires_at": "2026-03-24T12:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("myxo.github_app.httpx.post", return_value=mock_response) as mock_post:
            get_installation_token("fake-jwt", "99999")
            call_args = mock_post.call_args
            headers = call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer fake-jwt"
            assert headers["Accept"] == "application/vnd.github+json"

    def test_returns_token_and_expires_at(self):
        """Should return dict with token and expires_at."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "token": "ghs_abc123",
            "expires_at": "2026-03-24T12:00:00Z",
        }
        mock_response.raise_for_status = MagicMock()

        with patch("myxo.github_app.httpx.post", return_value=mock_response):
            result = get_installation_token("fake-jwt", "99999")
            assert result["token"] == "ghs_abc123"
            assert result["expires_at"] == "2026-03-24T12:00:00Z"

    def test_raises_on_http_error(self):
        """Should propagate HTTP errors."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("401 Unauthorized")

        with (
            patch("myxo.github_app.httpx.post", return_value=mock_response),
            pytest.raises(Exception, match="401"),
        ):
            get_installation_token("bad-jwt", "99999")


# ---------------------------------------------------------------------------
# create_installation_token
# ---------------------------------------------------------------------------


class TestCreateInstallationToken:
    """Tests for create_installation_token."""

    def test_combines_jwt_generation_and_token_exchange(self):
        """Should call generate_jwt then get_installation_token."""
        expected = {"token": "ghs_combined", "expires_at": "2026-03-24T12:00:00Z"}

        with (
            patch("myxo.github_app.generate_jwt", return_value="mock-jwt") as mock_gen,
            patch("myxo.github_app.get_installation_token", return_value=expected) as mock_get,
        ):
            result = create_installation_token("12345", _TEST_PRIVATE_KEY, "99999")
            mock_gen.assert_called_once_with("12345", _TEST_PRIVATE_KEY)
            mock_get.assert_called_once_with("mock-jwt", "99999")
            assert result == expected


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _decode_jwt_payload(token: str) -> dict:
    """Decode the payload (second segment) of a JWT without verification."""
    payload_b64 = token.split(".")[1]
    padded = payload_b64 + "=" * (4 - len(payload_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))


def _decode_jwt_header(token: str) -> dict:
    """Decode the header (first segment) of a JWT."""
    header_b64 = token.split(".")[0]
    padded = header_b64 + "=" * (4 - len(header_b64) % 4)
    return json.loads(base64.urlsafe_b64decode(padded))
