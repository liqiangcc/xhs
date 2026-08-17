# Domain

This directory contains pure business concepts, invariants, and policies.

Rules:
- no filesystem, database, GitHub, AI SDK, CLI, Actions, or transport dependencies;
- no persistence format knowledge;
- deterministic behavior must be testable with in-memory values;
- domain code may depend only on other domain code and standard language primitives.

Business rules are migrated here incrementally from legacy commands. Do not move code here merely to make files smaller.
