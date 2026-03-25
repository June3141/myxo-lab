use std::sync::LazyLock;

use regex::Regex;

struct Pattern {
    label: &'static str,
    regex: Regex,
}

static PATTERNS: LazyLock<Vec<Pattern>> = LazyLock::new(|| {
    vec![
        Pattern {
            label: "aws-access-key",
            regex: Regex::new(r"AKIA[0-9A-Z]{16}").unwrap(),
        },
        Pattern {
            label: "aws-secret-key",
            regex: Regex::new(
                r"(?i)(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*[A-Za-z0-9/+=]{40}",
            )
            .unwrap(),
        },
        Pattern {
            label: "jwt",
            regex: Regex::new(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+").unwrap(),
        },
        Pattern {
            label: "github-token",
            regex: Regex::new(r"(?:github_pat_[A-Za-z0-9_]{22,}|gh[psourx]_[A-Za-z0-9_]{36,})")
                .unwrap(),
        },
        Pattern {
            label: "private-key",
            regex: Regex::new(
                r"-----BEGIN [A-Z ]*PRIVATE KEY-----[^-]+-----END [A-Z ]*PRIVATE KEY-----",
            )
            .unwrap(),
        },
    ]
});

pub struct Sanitizer;

impl Sanitizer {
    pub fn new() -> Self {
        Self
    }

    pub fn sanitize(&self, text: &str) -> String {
        let mut result = text.to_string();
        for p in PATTERNS.iter() {
            result = p
                .regex
                .replace_all(&result, format!("[REDACTED:{}]", p.label))
                .into_owned();
        }
        result
    }

    pub fn has_secrets(&self, text: &str) -> bool {
        PATTERNS.iter().any(|p| p.regex.is_match(text))
    }
}

impl Default for Sanitizer {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn sanitize_aws_access_key() {
        let s = Sanitizer::new();
        let text = "key = AKIAIOSFODNN7EXAMPLE";
        let result = s.sanitize(text);
        assert!(result.contains("[REDACTED:aws-access-key]"));
        assert!(!result.contains("AKIAIOSFODNN7EXAMPLE"));
    }

    #[test]
    fn sanitize_aws_secret_key() {
        let s = Sanitizer::new();
        let text = "aws_secret_access_key = wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";
        let result = s.sanitize(text);
        assert!(result.contains("[REDACTED:aws-secret-key]"));
    }

    #[test]
    fn sanitize_github_token() {
        let s = Sanitizer::new();
        let text = "token = ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijkl";
        let result = s.sanitize(text);
        assert!(result.contains("[REDACTED:github-token]"));
    }

    #[test]
    fn sanitize_jwt() {
        let s = Sanitizer::new();
        let text = "auth: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.abc123";
        let result = s.sanitize(text);
        assert!(result.contains("[REDACTED:jwt]"));
    }

    #[test]
    fn sanitize_private_key() {
        let s = Sanitizer::new();
        let text = "-----BEGIN RSA PRIVATE KEY-----\nMIIBogIBAAJ\n-----END RSA PRIVATE KEY-----";
        let result = s.sanitize(text);
        assert!(result.contains("[REDACTED:private-key]"));
    }

    #[test]
    fn no_secrets_unchanged() {
        let s = Sanitizer::new();
        let text = "hello world, no secrets here";
        assert_eq!(s.sanitize(text), text);
    }

    #[test]
    fn has_secrets_detects_key() {
        let s = Sanitizer::new();
        assert!(s.has_secrets("key = AKIAIOSFODNN7EXAMPLE"));
        assert!(!s.has_secrets("just plain text"));
    }
}
