use glob_match::glob_match;

use crate::config::ConfigError;

pub struct SecureFilesystem {
    allowed: Vec<String>,
    blocked: Vec<String>,
    project_root: Option<String>,
}

impl SecureFilesystem {
    pub fn new(allowed: Vec<String>, blocked: Vec<String>, project_root: Option<String>) -> Self {
        Self {
            allowed,
            blocked,
            project_root: project_root.map(|r| r.replace('\\', "/")),
        }
    }

    pub fn check_access(&self, path: &str) -> bool {
        let path = path.replace('\\', "/");

        if self.project_root.is_none() && path.starts_with('/') {
            return false;
        }

        if !self.is_within_root(&path) {
            return false;
        }

        if self.matches_any(&path, &self.blocked) {
            return false;
        }

        self.matches_any(&path, &self.allowed)
    }

    pub fn validate_access(&self, path: &str) -> Result<(), ConfigError> {
        if self.check_access(path) {
            Ok(())
        } else {
            Err(ConfigError::Format(format!(
                "access denied: '{path}' is not in the allowed file list"
            )))
        }
    }

    fn is_within_root(&self, path: &str) -> bool {
        let Some(root) = &self.project_root else {
            return true;
        };

        let resolved = if path.starts_with('/') {
            path.to_string()
        } else {
            format!("{}/{}", root.trim_end_matches('/'), path)
        };

        let root_prefix = root.trim_end_matches('/');
        resolved == root_prefix || resolved.starts_with(&format!("{root_prefix}/"))
    }

    fn matches_any(&self, path: &str, patterns: &[String]) -> bool {
        let filename = path.rsplit('/').next().unwrap_or(path);

        for pattern in patterns {
            if glob_match(pattern, path) {
                return true;
            }
            if glob_match(pattern, filename) {
                return true;
            }
            let parts: Vec<&str> = path.split('/').collect();
            for i in 0..parts.len() {
                let sub = parts[i..].join("/");
                if glob_match(pattern, &sub) {
                    return true;
                }
            }
        }
        false
    }
}

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
        let guard = SecureFilesystem::new(vec!["src/**".into()], vec![], Some("/project".into()));
        assert!(guard.check_access("/project/src/main.rs"));
        assert!(!guard.check_access("/other/src/main.rs"));
    }

    #[test]
    fn relative_path_resolved_against_root() {
        let guard = SecureFilesystem::new(vec!["src/**".into()], vec![], Some("/project".into()));
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
