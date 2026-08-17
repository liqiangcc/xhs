# Infrastructure

This directory contains concrete technical adapters such as JSONL/filesystem, GitHub, AI, and future SQLite implementations.

Rules:
- implement outbound Ports;
- contain persistence/SDK/transport-specific details;
- do not define canonical merge semantics, answer quality semantics, review policy, or other business rules;
- infrastructure replacement must not require Domain changes.
