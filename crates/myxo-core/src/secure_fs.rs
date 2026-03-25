// SecureFilesystem module - to be implemented

#[cfg(test)]
mod tests {
    use super::*;

    fn make_guard(allowed: &[&str], blocked: &[&str]) -> SecureFilesystem {
        SecureFilesystem::new(
            allowed.iter().map(|s| s.to_string()).collect(),
            blocked.iter().map(|s| s.to_string()).collect(),
            None,
        )
    }

    #[test]
    fn allows_matching_path() {
        let guard = make_guard(&["src/**"], &[]);
        assert!(guard.check_access("src/main.rs"));
    }

    #[test]
    fn blocks_non_matching_path() {
        let guard = make_guard(&["src/**"], &[]);
        assert!(!guard.check_access("secrets/key.pem"));
    }

    #[test]
    fn blocked_takes_priority() {
        let guard = make_guard(&["**"], &["*.pem"]);
        assert!(!guard.check_access("certs/server.pem"));
        assert!(guard.check_access("src/main.rs"));
    }

    #[test]
    fn env_file_blocked() {
        let guard = make_guard(&["**"], &[".env*"]);
        assert!(!guard.check_access(".env"));
        assert!(!guard.check_access(".env.local"));
    }

    #[test]
    fn with_project_root() {
        let guard = SecureFilesystem::new(
            vec!["src/**".into()],
            vec![],
            Some("/project".into()),
        );
        assert!(guard.check_access("/project/src/main.rs"));
        assert!(!guard.check_access("/other/src/main.rs"));
    }

    #[test]
    fn relative_path_resolved_against_root() {
        let guard = SecureFilesystem::new(
            vec!["src/**".into()],
            vec![],
            Some("/project".into()),
        );
        assert!(guard.check_access("src/main.rs"));
    }

    #[test]
    fn absolute_path_rejected_without_root() {
        let guard = make_guard(&["**"], &[]);
        assert!(!guard.check_access("/etc/passwd"));
    }

    #[test]
    fn validate_access_raises_on_denied() {
        let guard = make_guard(&["src/**"], &[]);
        assert!(guard.validate_access("secrets/key.pem").is_err());
        assert!(guard.validate_access("src/main.rs").is_ok());
    }
}
