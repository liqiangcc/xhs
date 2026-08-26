# C System Bitness Source-First Boundary Audit

## Primary-source facts

- `8759fdb2629c78e7f847052e43922d24`: “如何用 C 语言判断当前 system 是 32 位还是 64 位？”

- Current Canonical ownership: ["8759fdb2629c78e7f847052e43922d24"].
- Corpus near-neighborhood candidates under the narrow 32/64 + C/system/pointer query: 2.

## Boundary conclusion

- The source is recoverable as a conceptual/C-code question, but the word `system` is not defined precisely enough to equate “32/64-bit system” with one C object size.
- A source-bounded answer must separate the current compiled program/ABI pointer representation from OS-kernel bitness and CPU capability.
- The source does not preserve a required function signature, output format, compiler family, predefined-macro policy, or platform API.
- Therefore any executable sample must label its interpretation explicitly and must not claim that standard C alone portably identifies host OS or CPU bitness.

No historical answer/remediation record was consulted before this conclusion.
