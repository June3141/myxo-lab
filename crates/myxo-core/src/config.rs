// Config module - to be implemented

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
