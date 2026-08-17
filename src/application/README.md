# Application

This directory contains use-case orchestration and explicit mutation planning.

Rules:
- depend on Domain and outbound Ports only;
- do not parse JSONL or call `fs` directly;
- do not create concrete infrastructure adapters;
- coordinate workflows, but do not redefine domain correctness;
- cross-state mutations must go through an explicit mutation boundary.
