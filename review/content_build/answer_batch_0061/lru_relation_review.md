# Batch 0061 LRU Source-First Relation Review

## Primary-source facts

- Survivor-side repository source occurrences ask only to implement an LRU cache: “算法：实现 LRU 缓存？”；“算法：实现一个 LRU 缓存？”。
- Duplicate-side repository source occurrences ask the same LRU-cache implementation operation: “算法：LRU缓存”；“算法：LRU 缓存”。
- The duplicate-side normalized Question ID occurs in two source notes with whitespace-equivalent wording; both occurrences were verified independently against their primary repository notes.
- No preserved source distinguishes capacity semantics, API shape, language, concurrency contract, TTL, persistence, or a different eviction policy. All preserved occurrences are Coding prompts for the same LRU-cache operation.

No historical relation/remediation record was consulted before this conclusion.

## Decision

Relation: `same`. Consolidate `cq_q_5fec9f875255be5ae3fa636523b24956` into survivor `cq_q_35c2d83b04a38c71b4cca1e3ed3f401b`; preserve every valid source occurrence under the survivor.

## Content consequence

Do not write two independent LRU answers. Regenerate Batch 0061 source inventory after normalization and write one source-bounded candidate for the survivor. This relation decision does not promote an Answer.
