// Syncer module - to be implemented

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn converter_names() {
        assert_eq!(ClaudeConverter.name(), "claude");
        assert_eq!(CodexConverter.name(), "codex");
        assert_eq!(CursorConverter.name(), "cursor");
        assert_eq!(WindsurfConverter.name(), "windsurf");
    }

    #[test]
    fn converter_output_paths() {
        let root = std::path::Path::new("/repo");
        assert_eq!(ClaudeConverter.output_path(root), root.join("CLAUDE.md"));
        assert_eq!(CodexConverter.output_path(root), root.join("AGENTS.md"));
        assert_eq!(
            CursorConverter.output_path(root),
            root.join(".cursor/rules")
        );
        assert_eq!(
            WindsurfConverter.output_path(root),
            root.join(".windsurfrules")
        );
    }

    #[test]
    fn convert_adds_autogen_header() {
        let output = ClaudeConverter.convert("hello");
        assert!(output.starts_with(AUTOGEN_HEADER));
        assert!(output.contains("hello"));
    }

    #[test]
    fn syncer_collect_reads_rules() {
        let dir = std::env::temp_dir().join("myxo-syncer-test");
        let myxo_dir = dir.join(".myxo-lab");
        std::fs::create_dir_all(&myxo_dir).unwrap();
        std::fs::write(myxo_dir.join("rules.md"), "# Rules\n").unwrap();

        let syncer = MyxoSyncer::new(&myxo_dir);
        let content = syncer.collect().unwrap();
        assert!(content.contains("# Rules"));

        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn syncer_collect_includes_protocols() {
        let dir = std::env::temp_dir().join("myxo-syncer-proto-test");
        let myxo_dir = dir.join(".myxo-lab");
        let protocols_dir = myxo_dir.join("protocols");
        std::fs::create_dir_all(&protocols_dir).unwrap();
        std::fs::write(myxo_dir.join("rules.md"), "# Rules\n").unwrap();
        std::fs::write(protocols_dir.join("a.md"), "# Protocol A\n").unwrap();

        let syncer = MyxoSyncer::new(&myxo_dir);
        let content = syncer.collect().unwrap();
        assert!(content.contains("# Rules"));
        assert!(content.contains("# Protocol A"));

        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn syncer_sync_writes_file() {
        let dir = std::env::temp_dir().join("myxo-syncer-write-test");
        let myxo_dir = dir.join(".myxo-lab");
        std::fs::create_dir_all(&myxo_dir).unwrap();
        std::fs::write(myxo_dir.join("rules.md"), "# Rules\n").unwrap();

        let syncer = MyxoSyncer::new(&myxo_dir);
        let path = syncer.sync(&dir, "claude").unwrap();
        assert_eq!(path, dir.join("CLAUDE.md"));
        let content = std::fs::read_to_string(&path).unwrap();
        assert!(content.starts_with(AUTOGEN_HEADER));

        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn syncer_sync_unknown_target_fails() {
        let dir = std::env::temp_dir().join("myxo-syncer-unknown-test");
        let myxo_dir = dir.join(".myxo-lab");
        std::fs::create_dir_all(&myxo_dir).unwrap();
        std::fs::write(myxo_dir.join("rules.md"), "# Rules\n").unwrap();

        let syncer = MyxoSyncer::new(&myxo_dir);
        assert!(syncer.sync(&dir, "nonexistent").is_err());

        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn syncer_sync_all_creates_all_targets() {
        let dir = std::env::temp_dir().join("myxo-syncer-all-test");
        let myxo_dir = dir.join(".myxo-lab");
        std::fs::create_dir_all(&myxo_dir).unwrap();
        std::fs::write(myxo_dir.join("rules.md"), "# Rules\n").unwrap();

        let syncer = MyxoSyncer::new(&myxo_dir);
        let paths = syncer.sync_all(&dir).unwrap();
        assert_eq!(paths.len(), 4);

        std::fs::remove_dir_all(&dir).ok();
    }
}
