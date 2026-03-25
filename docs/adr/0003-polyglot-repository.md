# 3. Polyglot Repository Structure

Date: 2026-03-25

## Status

Accepted

## Context

With the Rust migration (ADR-0002), the repository contains both Python (Pulumi IaC) and Rust (application) code. We need to decide whether to split into separate repositories or keep a single polyglot repository.

## Decision

Keep a single repository with both languages. Rust code lives in `crates/` (Cargo workspace), Python code in `src/myxo/` and `infra/`. CI workflows use path filters to avoid unnecessary cross-language builds.

## Consequences

- Developers need both Rust and Python toolchains
- CI is split by path filters: `crates/**` triggers Rust CI, `src/**` triggers Python CI
- Taskfile.yml provides unified `task lint`, `task test` commands across both languages
- Atomic commits can span both IaC and application changes
