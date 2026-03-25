---
name: rust-code-structure
description: Rust code structure rules for crates/ (file size, function size, module organization, crate separation). Reference this when writing or reviewing Rust implementation code.
user-invocable: false
---

# Rust Code Structure Rules

## File Size

- Source files: **500 lines max** (excludes tests and auto-generated files)
- `impl` blocks, `match` arms, and type definitions contribute to higher line counts — this is expected
- When exceeding: extract into a submodule or separate file
- Build files incrementally — a 500-line file should grow over multiple commits, not appear in one

## Function / Method Size

- **50 lines max** per function or method
- `?` operator keeps error handling concise — long functions usually indicate mixed concerns
- When exceeding: extract helper functions as `fn` or closures

## Single Responsibility

- Each module focuses on **one concern**
- Litmus test: can you describe what this module does in one sentence?
- A struct + its `impl` block naturally live in the same file
- When a module grows submodules, use directory form: `verifier/mod.rs` + `verifier/labels.rs`

## Crate Separation

| Crate | Location | Responsibility | May depend on |
|-------|----------|---------------|---------------|
| CLI | `crates/myxo-cli/` | `clap` parsing, user I/O, output formatting only | Core |
| Core | `crates/myxo-core/` | Domain logic, traits, types | (external crates only) |

**Dependency direction:** CLI → Core (no reverse dependency)

- CLI is a thin entry point — delegate all logic to Core
- Core must not depend on CLI or any presentation concern
- Use `pub(crate)` by default; only `pub` what the crate's public API needs
- Re-export key types from `lib.rs` for a clean public surface

## Module Organization

As `myxo-core` grows, organize by domain concern:

```
crates/myxo-core/src/
├── lib.rs           # pub mod declarations, re-exports
├── error.rs         # thiserror error types
├── config.rs        # serde_yaml config parsing
├── verifier.rs      # or verifier/mod.rs + submodules
├── syncer.rs
└── protocol.rs
```

- Prefer flat files (`verifier.rs`) until complexity demands submodules
- Split into `verifier/mod.rs` + submodules when a file exceeds 500 lines or has distinct sub-concerns

## Testing

- **Unit tests**: `#[cfg(test)] mod tests` inside the source file
- **Integration tests**: `crates/myxo-cli/tests/` (one file per feature area)
- Test files are exempt from the 500-line limit
- Test module naming: `tests/cli_test.rs`, `tests/verifier_test.rs`

## Gotchas

- `Cargo.lock` is committed (binary crate) — but exempt from diff limits in commit-rules
- `mod.rs` is only needed for directory-based modules; prefer `verifier.rs` over `verifier/mod.rs` for simple modules
- Clippy runs with `-D warnings` in CI — fix all warnings before committing
- Edition 2024 uses the new `use` import style; `extern crate` is unnecessary
- `#[derive]` macros (Clone, Debug, Serialize, etc.) add visual bulk but are zero-cost — don't count them as "complexity"

## Validation

After writing or modifying source files:

```bash
cargo fmt --all -- --check
cargo clippy --all-targets -- -D warnings
cargo test --all
```

If any source file exceeds 500 lines, propose a split before committing.
