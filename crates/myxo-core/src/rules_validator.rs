const MAX_LINES: usize = 50;
const MAX_LINE_LENGTH: usize = 120;

pub fn validate_rules(content: &str) -> Vec<String> {
    if content.trim().is_empty() {
        return vec![];
    }

    let mut errors = Vec::new();
    let mut lines: Vec<&str> = content.split('\n').collect();

    // Remove trailing empty line caused by final newline
    if lines.last() == Some(&"") {
        lines.pop();
    }

    if lines.len() > MAX_LINES {
        errors.push(format!(
            "rules.md exceeds {MAX_LINES} lines (found {})",
            lines.len()
        ));
    }

    for (i, line) in lines.iter().enumerate() {
        let line_num = i + 1;

        if line.len() > MAX_LINE_LENGTH {
            errors.push(format!(
                "Line {line_num}: exceeds {MAX_LINE_LENGTH} characters (found {})",
                line.len()
            ));
        }

        if line.is_empty() || line.starts_with('#') {
            continue;
        }

        if !line.starts_with("- ") {
            let preview: String = line.chars().take(40).collect();
            errors.push(format!(
                "Line {line_num}: must start with '- ' (bullet point), got: {preview}"
            ));
        }
    }

    errors
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn valid_rules_no_errors() {
        let content = "# Rules\n\n- Rule one\n- Rule two\n";
        let errors = validate_rules(content);
        assert!(errors.is_empty());
    }

    #[test]
    fn empty_content_no_errors() {
        let errors = validate_rules("");
        assert!(errors.is_empty());
    }

    #[test]
    fn invalid_line_format() {
        let content = "# Rules\n\nNot a bullet line\n";
        let errors = validate_rules(content);
        assert!(!errors.is_empty());
        assert!(errors[0].contains("must start with '- '"));
    }

    #[test]
    fn exceeds_max_lines() {
        let content = (0..51)
            .map(|i| format!("- Rule {i}"))
            .collect::<Vec<_>>()
            .join("\n");
        let errors = validate_rules(&content);
        assert!(errors.iter().any(|e| e.contains("exceeds 50 lines")));
    }

    #[test]
    fn exceeds_max_line_length() {
        let long_line = format!("- {}", "a".repeat(120));
        let errors = validate_rules(&long_line);
        assert!(errors.iter().any(|e| e.contains("exceeds 120 characters")));
    }
}
