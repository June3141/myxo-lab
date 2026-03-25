// Rules validator module - to be implemented

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
        let content = (0..51).map(|i| format!("- Rule {i}")).collect::<Vec<_>>().join("\n");
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
