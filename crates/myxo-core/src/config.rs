use std::path::Path;

use serde::Deserialize;

#[derive(Debug, thiserror::Error)]
pub enum ConfigError {
    #[error("failed to read config file: {0}")]
    Io(#[from] std::io::Error),
    #[error("failed to parse config YAML: {0}")]
    Yaml(#[from] serde_yaml::Error),
}

#[derive(Debug, Deserialize)]
pub struct MyxoConfig {
    pub version: String,
    #[serde(default)]
    pub github: Option<GitHubConfig>,
}

#[derive(Debug, Deserialize)]
pub struct GitHubConfig {
    pub repo: String,
    #[serde(default)]
    pub labels: Vec<LabelConfig>,
    #[serde(default)]
    pub branch_protection: Option<BranchProtectionConfig>,
    #[serde(default)]
    pub secrets: Vec<String>,
}

#[derive(Debug, Deserialize)]
pub struct LabelConfig {
    pub name: String,
    pub color: String,
}

#[derive(Debug, Deserialize)]
pub struct BranchProtectionConfig {
    pub branch: String,
    #[serde(default)]
    pub required_reviews: u32,
    #[serde(default)]
    pub dismiss_stale_reviews: bool,
}

impl MyxoConfig {
    pub fn from_yaml(yaml: &str) -> Result<Self, ConfigError> {
        Ok(serde_yaml::from_str(yaml)?)
    }

    pub fn from_file(path: &Path) -> Result<Self, ConfigError> {
        let content = std::fs::read_to_string(path)?;
        Self::from_yaml(&content)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const MINIMAL_CONFIG: &str = r#"
version: "0.1"
"#;

    const FULL_CONFIG: &str = r#"
version: "0.1"
github:
  repo: owner/repo
  labels:
    - name: "bug"
      color: "d73a4a"
    - name: "enhancement"
      color: "a2eeef"
  branch_protection:
    branch: main
    required_reviews: 1
    dismiss_stale_reviews: true
  secrets:
    - GITHUB_TOKEN
    - PULUMI_ACCESS_TOKEN
"#;

    #[test]
    fn parse_minimal_config() {
        let config = MyxoConfig::from_yaml(MINIMAL_CONFIG).unwrap();
        assert_eq!(config.version, "0.1");
        assert!(config.github.is_none());
    }

    #[test]
    fn parse_full_config() {
        let config = MyxoConfig::from_yaml(FULL_CONFIG).unwrap();
        assert_eq!(config.version, "0.1");
        let github = config.github.unwrap();
        assert_eq!(github.repo, "owner/repo");
        assert_eq!(github.labels.len(), 2);
        assert_eq!(github.labels[0].name, "bug");
        assert_eq!(github.labels[0].color, "d73a4a");
    }

    #[test]
    fn parse_branch_protection() {
        let config = MyxoConfig::from_yaml(FULL_CONFIG).unwrap();
        let bp = config.github.unwrap().branch_protection.unwrap();
        assert_eq!(bp.branch, "main");
        assert_eq!(bp.required_reviews, 1);
        assert!(bp.dismiss_stale_reviews);
    }

    #[test]
    fn parse_secrets() {
        let config = MyxoConfig::from_yaml(FULL_CONFIG).unwrap();
        let secrets = config.github.unwrap().secrets;
        assert_eq!(secrets, vec!["GITHUB_TOKEN", "PULUMI_ACCESS_TOKEN"]);
    }

    #[test]
    fn invalid_yaml_returns_error() {
        let result = MyxoConfig::from_yaml("{{invalid");
        assert!(result.is_err());
    }

    #[test]
    fn missing_version_returns_error() {
        let result = MyxoConfig::from_yaml("github:\n  repo: test");
        assert!(result.is_err());
    }

    #[test]
    fn from_file_returns_error_for_missing_file() {
        let result = MyxoConfig::from_file(std::path::Path::new("/nonexistent/config.yaml"));
        assert!(result.is_err());
    }
}
