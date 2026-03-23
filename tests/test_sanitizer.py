"""Tests for ContextSanitizer — secret scanning before LLM."""

from myxo.sanitizer import ContextSanitizer


# --- AWS Access Key ---


def test_redacts_aws_access_key() -> None:
    sanitizer = ContextSanitizer()
    text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
    result = sanitizer.sanitize(text)
    assert "AKIAIOSFODNN7EXAMPLE" not in result
    assert "[REDACTED:aws-access-key]" in result


def test_has_secrets_detects_aws_access_key() -> None:
    sanitizer = ContextSanitizer()
    assert sanitizer.has_secrets("key = AKIAIOSFODNN7EXAMPLE")


# --- AWS Secret Key ---


def test_redacts_aws_secret_key() -> None:
    sanitizer = ContextSanitizer()
    text = "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    result = sanitizer.sanitize(text)
    assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in result
    assert "[REDACTED:aws-secret-key]" in result


def test_has_secrets_detects_aws_secret_key() -> None:
    sanitizer = ContextSanitizer()
    assert sanitizer.has_secrets(
        "aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    )


# --- Private Key ---


def test_redacts_private_key_header() -> None:
    sanitizer = ContextSanitizer()
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAJBALR...\n-----END RSA PRIVATE KEY-----"
    result = sanitizer.sanitize(text)
    assert "-----BEGIN RSA PRIVATE KEY-----" not in result
    assert "[REDACTED:private-key]" in result


def test_redacts_ec_private_key() -> None:
    sanitizer = ContextSanitizer()
    text = "-----BEGIN EC PRIVATE KEY-----\nMHQCAQEE...\n-----END EC PRIVATE KEY-----"
    result = sanitizer.sanitize(text)
    assert "[REDACTED:private-key]" in result


def test_redacts_full_pem_block() -> None:
    """Multi-line PEM key body (base64 payload) is fully redacted."""
    sanitizer = ContextSanitizer()
    text = (
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF068wEJ8HPXEY2UQxHOm\n"
        "WsLOGpKx3KNDB+sFm1jMCH4a0gKsVd3vOEJMPqGP6xHPE36d3DCPIZ+\n"
        "-----END RSA PRIVATE KEY-----"
    )
    result = sanitizer.sanitize(text)
    assert "MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn" not in result
    assert "WsLOGpKx3KNDB+sFm1jMCH4a0gKsVd3vOEJMPqGP6xHPE36d3DCPIZ+" not in result
    assert "-----BEGIN RSA PRIVATE KEY-----" not in result
    assert "-----END RSA PRIVATE KEY-----" not in result
    assert "[REDACTED:private-key]" in result


# --- JWT ---


def test_redacts_jwt_token() -> None:
    sanitizer = ContextSanitizer()
    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        ".eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0"
        ".SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
    text = f"Authorization: Bearer {token}"
    result = sanitizer.sanitize(text)
    assert token not in result
    assert "[REDACTED:jwt]" in result


# --- Password ---


def test_redacts_password_single_quotes() -> None:
    sanitizer = ContextSanitizer()
    text = "password = 'super_secret_123'"
    result = sanitizer.sanitize(text)
    assert "super_secret_123" not in result
    assert "[REDACTED:password]" in result


def test_redacts_password_double_quotes() -> None:
    sanitizer = ContextSanitizer()
    text = 'password = "my-database-pw!"'
    result = sanitizer.sanitize(text)
    assert "my-database-pw!" not in result
    assert "[REDACTED:password]" in result


def test_redacts_password_no_spaces() -> None:
    sanitizer = ContextSanitizer()
    text = "password='compact_secret'"
    result = sanitizer.sanitize(text)
    assert "compact_secret" not in result
    assert "[REDACTED:password]" in result


def test_password_word_boundary_no_false_positive() -> None:
    """Words like 'mypassword' should NOT trigger redaction."""
    sanitizer = ContextSanitizer()
    text = "mypassword = 'not_a_match'"
    assert sanitizer.sanitize(text) == text
    assert not sanitizer.has_secrets(text)


# --- GitHub Token ---


def test_redacts_github_pat() -> None:
    sanitizer = ContextSanitizer()
    text = "GITHUB_TOKEN=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl"
    result = sanitizer.sanitize(text)
    assert "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl" not in result
    assert "[REDACTED:github-token]" in result


def test_redacts_github_server_token() -> None:
    sanitizer = ContextSanitizer()
    text = "token: ghs_1234567890abcdefghijklmnopqrstuvwxyz"
    result = sanitizer.sanitize(text)
    assert "ghs_1234567890abcdefghijklmnopqrstuvwxyz" not in result
    assert "[REDACTED:github-token]" in result


# --- Clean text passthrough ---


def test_clean_text_unchanged() -> None:
    sanitizer = ContextSanitizer()
    text = "This is a normal log message with no secrets."
    assert sanitizer.sanitize(text) == text


def test_has_secrets_returns_false_for_clean_text() -> None:
    sanitizer = ContextSanitizer()
    assert not sanitizer.has_secrets("Just some regular code: x = 42")


def test_code_with_password_word_but_no_value() -> None:
    sanitizer = ContextSanitizer()
    text = "# Enter your password below"
    assert sanitizer.sanitize(text) == text
    assert not sanitizer.has_secrets(text)


# --- Multiple secrets ---


def test_redacts_multiple_different_secrets() -> None:
    sanitizer = ContextSanitizer()
    text = (
        "aws_access_key_id = AKIAIOSFODNN7EXAMPLE\n"
        "password = 'db_secret_pass'\n"
        "GITHUB_TOKEN=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl\n"
    )
    result = sanitizer.sanitize(text)
    assert "[REDACTED:aws-access-key]" in result
    assert "[REDACTED:password]" in result
    assert "[REDACTED:github-token]" in result
    assert "AKIAIOSFODNN7EXAMPLE" not in result
    assert "db_secret_pass" not in result


def test_has_secrets_true_with_multiple() -> None:
    sanitizer = ContextSanitizer()
    text = "AKIAIOSFODNN7EXAMPLE and password = 'oops'"
    assert sanitizer.has_secrets(text)
