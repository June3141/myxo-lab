use serde::Deserialize;

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
    pub fn ok(name: &str, message: &str) -> Self {
        Self {
            name: name.to_string(),
            status: CheckStatus::Ok,
            message: message.to_string(),
        }
    }

    pub fn fail(name: &str, message: &str) -> Self {
        Self {
            name: name.to_string(),
            status: CheckStatus::Fail,
            message: message.to_string(),
        }
    }

    pub fn warn(name: &str, message: &str) -> Self {
        Self {
            name: name.to_string(),
            status: CheckStatus::Warn,
            message: message.to_string(),
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct LabelExpectation {
    pub name: String,
    pub color: String,
}

/// Compare existing labels against expected labels (API-independent logic).
pub fn check_labels_against(
    existing: &[String],
    expected: &[LabelExpectation],
) -> Vec<CheckResult> {
    expected
        .iter()
        .map(|label| {
            if existing.contains(&label.name) {
                CheckResult::ok(&format!("label: {}", label.name), "exists")
            } else {
                CheckResult::fail(&format!("label: {}", label.name), "missing")
            }
        })
        .collect()
}

/// Compare existing secrets against expected secrets (API-independent logic).
pub fn check_secrets_against(existing: &[String], expected: &[String]) -> Vec<CheckResult> {
    expected
        .iter()
        .map(|secret| {
            if existing.contains(secret) {
                CheckResult::ok(&format!("secret: {secret}"), "configured")
            } else {
                CheckResult::fail(&format!("secret: {secret}"), "not found")
            }
        })
        .collect()
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
            LabelExpectation {
                name: "bug".into(),
                color: "d73a4a".into(),
            },
            LabelExpectation {
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
            LabelExpectation {
                name: "bug".into(),
                color: "d73a4a".into(),
            },
            LabelExpectation {
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
}
