"""Tests for ContextSanitizer — secret scanning before LLM."""

from myxo.sanitizer import ContextSanitizer


class TestSanitizeAWSAccessKey:
    """AWS Access Key ID pattern: AKIA followed by 16 uppercase alphanumeric chars."""

    def test_redacts_aws_access_key(self) -> None:
        sanitizer = ContextSanitizer()
        text = "aws_access_key_id = AKIAIOSFODNN7EXAMPLE"
        result = sanitizer.sanitize(text)
        assert "AKIAIOSFODNN7EXAMPLE" not in result
        assert "[REDACTED:aws-access-key]" in result

    def test_has_secrets_detects_aws_access_key(self) -> None:
        sanitizer = ContextSanitizer()
        assert sanitizer.has_secrets("key = AKIAIOSFODNN7EXAMPLE")


class TestSanitizeAWSSecretKey:
    """AWS Secret Access Key: 40-char base64 after common prefixes."""

    def test_redacts_aws_secret_key(self) -> None:
        sanitizer = ContextSanitizer()
        text = "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        result = sanitizer.sanitize(text)
        assert "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" not in result
        assert "[REDACTED:aws-secret-key]" in result

    def test_has_secrets_detects_aws_secret_key(self) -> None:
        sanitizer = ContextSanitizer()
        assert sanitizer.has_secrets(
            "aws_secret_access_key=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )


class TestSanitizePrivateKey:
    """Private Key blocks: -----BEGIN ... PRIVATE KEY-----."""

    def test_redacts_private_key_header(self) -> None:
        sanitizer = ContextSanitizer()
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAJBALR..."
        result = sanitizer.sanitize(text)
        assert "-----BEGIN RSA PRIVATE KEY-----" not in result
        assert "[REDACTED:private-key]" in result

    def test_redacts_ec_private_key(self) -> None:
        sanitizer = ContextSanitizer()
        text = "-----BEGIN EC PRIVATE KEY-----"
        result = sanitizer.sanitize(text)
        assert "[REDACTED:private-key]" in result


class TestSanitizeJWT:
    """JWT tokens: eyJ... three base64url segments separated by dots."""

    def test_redacts_jwt_token(self) -> None:
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


class TestSanitizePassword:
    """Generic password patterns: password = '...' or password = "..."."""

    def test_redacts_password_single_quotes(self) -> None:
        sanitizer = ContextSanitizer()
        text = "password = 'super_secret_123'"
        result = sanitizer.sanitize(text)
        assert "super_secret_123" not in result
        assert "[REDACTED:password]" in result

    def test_redacts_password_double_quotes(self) -> None:
        sanitizer = ContextSanitizer()
        text = 'password = "my-database-pw!"'
        result = sanitizer.sanitize(text)
        assert "my-database-pw!" not in result
        assert "[REDACTED:password]" in result

    def test_redacts_password_no_spaces(self) -> None:
        sanitizer = ContextSanitizer()
        text = "password='compact_secret'"
        result = sanitizer.sanitize(text)
        assert "compact_secret" not in result
        assert "[REDACTED:password]" in result


class TestSanitizeGitHubToken:
    """GitHub tokens: ghp_ or ghs_ followed by 36+ alphanumeric chars."""

    def test_redacts_github_pat(self) -> None:
        sanitizer = ContextSanitizer()
        text = "GITHUB_TOKEN=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl"
        result = sanitizer.sanitize(text)
        assert "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl" not in result
        assert "[REDACTED:github-token]" in result

    def test_redacts_github_server_token(self) -> None:
        sanitizer = ContextSanitizer()
        text = "token: ghs_1234567890abcdefghijklmnopqrstuvwxyz"
        result = sanitizer.sanitize(text)
        assert "ghs_1234567890abcdefghijklmnopqrstuvwxyz" not in result
        assert "[REDACTED:github-token]" in result


class TestCleanTextPassthrough:
    """Clean text without secrets should pass through unchanged."""

    def test_clean_text_unchanged(self) -> None:
        sanitizer = ContextSanitizer()
        text = "This is a normal log message with no secrets."
        assert sanitizer.sanitize(text) == text

    def test_has_secrets_returns_false_for_clean_text(self) -> None:
        sanitizer = ContextSanitizer()
        assert not sanitizer.has_secrets("Just some regular code: x = 42")

    def test_code_with_password_word_but_no_value(self) -> None:
        sanitizer = ContextSanitizer()
        text = "# Enter your password below"
        assert sanitizer.sanitize(text) == text
        assert not sanitizer.has_secrets(text)


class TestMultipleSecrets:
    """Multiple secrets in one text should all be redacted."""

    def test_redacts_multiple_different_secrets(self) -> None:
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

    def test_has_secrets_true_with_multiple(self) -> None:
        sanitizer = ContextSanitizer()
        text = "AKIAIOSFODNN7EXAMPLE and password = 'oops'"
        assert sanitizer.has_secrets(text)
