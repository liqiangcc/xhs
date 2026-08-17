# Interfaces

This directory contains inbound adapters such as CLI, GitHub Actions entry points, and future MCP transport adapters.

Rules:
- parse transport/argv input and perform syntax-level validation;
- convert input to Application DTOs;
- invoke Application use cases and format results;
- do not implement business rules or directly coordinate repositories.

The existing `scripts/xhs.js` CLI remains authoritative during incremental migration.
