use std::collections::HashMap;
use std::path::Path;

use crate::config::ConfigError;

pub type Frontmatter = HashMap<String, serde_yaml::Value>;

#[derive(Debug)]
pub struct Document {
    pub frontmatter: Frontmatter,
    pub body: String,
}

impl Document {
    pub fn parse(content: &str) -> Result<Self, ConfigError> {
        if !content.starts_with("---\n") {
            return Err(ConfigError::Format(
                "missing YAML frontmatter opening delimiter".into(),
            ));
        }

        let rest = &content[4..];
        let closing_idx = rest.find("\n---\n").ok_or_else(|| {
            ConfigError::Format("missing YAML frontmatter closing delimiter".into())
        })?;

        let yaml_text = &rest[..closing_idx];
        let body = &rest[closing_idx + 5..];

        let frontmatter: Frontmatter = serde_yaml::from_str(yaml_text)
            .map_err(|e| ConfigError::Format(format!("invalid frontmatter YAML: {e}")))?;

        Ok(Self {
            frontmatter,
            body: body.to_string(),
        })
    }

    pub fn load(path: &Path) -> Result<Self, ConfigError> {
        let content = std::fs::read_to_string(path).map_err(|e| ConfigError::Io {
            path: path.to_path_buf(),
            source: e,
        })?;
        Self::parse(&content)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const VALID_DOC: &str = "---\nname: test\ndescription: a test\n---\n## Body\nContent here\n";
    const NO_FRONTMATTER: &str = "Just some text";
    const NO_CLOSING: &str = "---\nname: test\nno closing delimiter";
    const INVALID_YAML: &str = "---\n{{bad\n---\nBody\n";

    #[test]
    fn parse_valid_frontmatter() {
        let doc = Document::parse(VALID_DOC).unwrap();
        assert_eq!(doc.frontmatter["name"], "test");
        assert_eq!(doc.frontmatter["description"], "a test");
        assert!(doc.body.contains("## Body"));
    }

    #[test]
    fn parse_fails_without_opening_delimiter() {
        assert!(Document::parse(NO_FRONTMATTER).is_err());
    }

    #[test]
    fn parse_fails_without_closing_delimiter() {
        assert!(Document::parse(NO_CLOSING).is_err());
    }

    #[test]
    fn parse_fails_with_invalid_yaml() {
        assert!(Document::parse(INVALID_YAML).is_err());
    }

    #[test]
    fn load_from_file() {
        let dir = std::env::temp_dir().join("myxo-frontmatter-test");
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("test.md");
        std::fs::write(&path, VALID_DOC).unwrap();

        let doc = Document::load(&path).unwrap();
        assert_eq!(doc.frontmatter["name"], "test");

        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn load_missing_file_returns_error() {
        let path = std::env::temp_dir().join("myxo-nonexistent-doc.md");
        assert!(Document::load(&path).is_err());
    }
}
