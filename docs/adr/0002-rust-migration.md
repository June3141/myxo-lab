# 2. Migrate Application Layer from Python to Rust

Date: 2026-03-25

## Status

Accepted

## Context

The application layer (CLI, verifier, syncer) was initially written in Python. At ~2.6k LOC source + ~9.4k LOC tests, the codebase is small enough that migration cost is minimal. Key drivers:

- **Type safety**: Compile-time guarantees that Python's type hints + ty cannot fully provide
- **Binary distribution**: Single binary simplifies container images and deployment
- **Async runtime**: tokio provides native async without GIL constraints
- **Orchestration**: Restate has native Rust support; Temporal also offers a Rust SDK

## Decision

Migrate the application layer to Rust while keeping Pulumi IaC in Python. The Rust binary becomes the deployment artifact; Python remains only for infrastructure-as-code.

## Consequences

- Rust toolchain (1.85+) required for development
- CI runs both Python (Pulumi) and Rust (application) checks
- Existing Python modules are replaced incrementally, then removed
- Container images switch to multi-stage Rust builds
