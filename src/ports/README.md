# Outbound Ports

This directory contains narrow abstractions required by Application.

Rules:
- model capabilities needed by use cases, not generic ORM-style CRUD by default;
- do not expose JSONL paths, filesystem layout, GitHub payloads, or SDK types;
- keep business decisions out of repository and service ports;
- adapters implementing the same port should be contract-testable.

Expected areas include repositories, mutation boundaries, clock/evidence services, and external integrations.
