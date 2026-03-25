# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Cargo workspace with myxo-cli and myxo-core crates (#213)
- CI/CD hardening: SHA pinning, security scanning, coverage (#214, #215)
- Taskfile for unified task runner (#216)
- Pre-commit linters: yamllint, actionlint, shellcheck, hadolint, typos, markdownlint (#217)

## [0.1.0] - 2026-03-25

### Added
- Initial Python implementation of myxo CLI
- Pulumi IaC for AWS infrastructure
- GitHub Actions CI/CD pipeline
- Pre-commit hooks with ruff
