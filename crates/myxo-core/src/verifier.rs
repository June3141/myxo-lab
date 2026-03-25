use std::collections::HashSet;

use crate::config::{ConfigError, LabelConfig};

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum CheckStatus {
    Ok,
    Fail,
    Warn,
}

#[derive(Debug, Clone)]
pub struct CheckResult {
    pub name: String,
    pub status: CheckStatus,
    pub message: String,
}

impl CheckResult {
    pub fn ok(name: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            status: CheckStatus::Ok,
            message: message.into(),
        }
    }

    pub fn fail(name: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            status: CheckStatus::Fail,
            message: message.into(),
        }
    }

    pub fn warn(name: impl Into<String>, message: impl Into<String>) -> Self {
        Self {
            name: name.into(),
            status: CheckStatus::Warn,
            message: message.into(),
        }
    }
}

/// Compare existing labels against expected labels (API-independent logic).
pub fn check_labels_against(existing: &[String], expected: &[LabelConfig]) -> Vec<CheckResult> {
    let existing_set: HashSet<&str> = existing.iter().map(|s| s.as_str()).collect();
    expected
        .iter()
        .map(|label| {
            if existing_set.contains(label.name.as_str()) {
                CheckResult::ok(format!("label: {}", label.name), "exists")
            } else {
                CheckResult::fail(format!("label: {}", label.name), "missing")
            }
        })
        .collect()
}

/// Compare existing secrets against expected secrets (API-independent logic).
pub fn check_secrets_against(existing: &[String], expected: &[String]) -> Vec<CheckResult> {
    let existing_set: HashSet<&str> = existing.iter().map(|s| s.as_str()).collect();
    expected
        .iter()
        .map(|secret| {
            if existing_set.contains(secret.as_str()) {
                CheckResult::ok(format!("secret: {secret}"), "configured")
            } else {
                CheckResult::fail(format!("secret: {secret}"), "not found")
            }
        })
        .collect()
}

/// GitHub API verifier using octocrab.
pub struct GitHubVerifier {
    crab: octocrab::Octocrab,
}

impl GitHubVerifier {
    pub fn new(token: &str) -> Result<Self, ConfigError> {
        let crab = octocrab::Octocrab::builder()
            .personal_token(token.to_string())
            .build()
            .map_err(|e| ConfigError::Api(format!("failed to create GitHub client: {e}")))?;
        Ok(Self { crab })
    }

    /// Fetch all labels from a repository (paginated) and check against expected.
    pub async fn check_labels(
        &self,
        owner: &str,
        repo: &str,
        expected: &[LabelConfig],
    ) -> Result<Vec<CheckResult>, ConfigError> {
        let mut existing = Vec::new();
        let mut page = self
            .crab
            .issues(owner, repo)
            .list_labels_for_repo()
            .per_page(100)
            .send()
            .await
            .map_err(|e| ConfigError::Api(format!("failed to fetch labels: {e}")))?;

        existing.extend(page.items.iter().map(|l| l.name.clone()));

        while let Some(next_page) = self
            .crab
            .get_page::<octocrab::models::Label>(&page.next)
            .await
            .map_err(|e| ConfigError::Api(format!("failed to fetch labels page: {e}")))?
        {
            existing.extend(next_page.items.iter().map(|l| l.name.clone()));
            page = next_page;
        }

        Ok(check_labels_against(&existing, expected))
    }

    /// Fetch secrets list from a repository and check against expected.
    pub async fn check_secrets(
        &self,
        owner: &str,
        repo: &str,
        expected: &[String],
    ) -> Result<Vec<CheckResult>, ConfigError> {
        let route = format!("/repos/{owner}/{repo}/actions/secrets");
        let response: serde_json::Value = self
            .crab
            .get(&route, None::<&()>)
            .await
            .map_err(|e| ConfigError::Api(format!("failed to fetch secrets: {e}")))?;

        let existing: Vec<String> = response
            .get("secrets")
            .and_then(|v| v.as_array())
            .into_iter()
            .flatten()
            .filter_map(|s| s["name"].as_str().map(String::from))
            .collect();

        Ok(check_secrets_against(&existing, expected))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn check_result_ok() {
        let r = CheckResult::ok("test", "passed");
        assert_eq!(r.status, CheckStatus::Ok);
        assert_eq!(r.name, "test");
    }

    #[test]
    fn check_result_fail() {
        let r = CheckResult::fail("test", "missing");
        assert_eq!(r.status, CheckStatus::Fail);
    }

    #[test]
    fn check_result_warn() {
        let r = CheckResult::warn("test", "not ideal");
        assert_eq!(r.status, CheckStatus::Warn);
    }

    #[test]
    fn check_labels_all_present() {
        let existing = vec!["bug".to_string(), "enhancement".to_string()];
        let expected = vec![
            LabelConfig {
                name: "bug".into(),
                color: "d73a4a".into(),
            },
            LabelConfig {
                name: "enhancement".into(),
                color: "a2eeef".into(),
            },
        ];
        let results = check_labels_against(&existing, &expected);
        assert!(results.iter().all(|r| r.status == CheckStatus::Ok));
    }

    #[test]
    fn check_labels_missing() {
        let existing = vec!["bug".to_string()];
        let expected = vec![
            LabelConfig {
                name: "bug".into(),
                color: "d73a4a".into(),
            },
            LabelConfig {
                name: "missing-label".into(),
                color: "000000".into(),
            },
        ];
        let results = check_labels_against(&existing, &expected);
        assert_eq!(results[0].status, CheckStatus::Ok);
        assert_eq!(results[1].status, CheckStatus::Fail);
    }

    #[test]
    fn check_secrets_all_present() {
        let existing = vec!["GITHUB_TOKEN".to_string(), "SECRET_A".to_string()];
        let expected = vec!["GITHUB_TOKEN".to_string()];
        let results = check_secrets_against(&existing, &expected);
        assert!(results.iter().all(|r| r.status == CheckStatus::Ok));
    }

    #[test]
    fn check_secrets_missing() {
        let existing: Vec<String> = vec![];
        let expected = vec!["MISSING_SECRET".to_string()];
        let results = check_secrets_against(&existing, &expected);
        assert_eq!(results[0].status, CheckStatus::Fail);
    }

    #[tokio::test]
    async fn verifier_new_with_token() {
        let verifier = GitHubVerifier::new("test-token");
        assert!(verifier.is_ok());
    }
}
