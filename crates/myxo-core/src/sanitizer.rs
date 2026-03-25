// Sanitizer module - to be implemented

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
