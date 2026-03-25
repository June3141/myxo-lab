# 1. Record Architecture Decisions

Date: 2026-03-25

## Status

Accepted

## Context

As the project grows, we need to document key architectural decisions so future contributors understand why things are the way they are. Without a lightweight record, decisions are lost in PRs, Slack threads, or tribal knowledge.

## Decision

We will use Architecture Decision Records (ADRs) as described by Michael Nygard. ADRs are stored in `docs/adr/` and numbered sequentially (e.g., `0001-title.md`).

## Consequences

- New architectural decisions must be documented as ADRs
- ADRs are immutable once accepted; superseded ADRs link to their replacement
- Low overhead: each ADR is a short markdown file
