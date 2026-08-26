# Sliding Window Maximum Source-First Relation Review

## Primary-source facts

- `86a4c030e736e3eea9fed1f6b739694d` preserves only the algorithm title “滑动窗口的最大值”.
- `b55a6649e9e0b7e2351c5d1f3d5f167c` preserves the fuller contract: “给定一个数组和滑动窗口大小K，返回每个滑动窗口的最大值。”
- corpus-wide active Question enumeration for sliding-window maximum returns exactly these two source Questions.
- both refer to the same observable problem contract; neither source preserves exact method signature, k validity rules, null behavior, or complexity requirement.

No historical relation/remediation record was consulted before this conclusion.

## Decision

Relation: `same`. Retain source-explicit survivor `cq_q_b55a6649e9e0b7e2351c5d1f3d5f167c` owning both Questions; retire shorthand singleton `cq_q_86a4c030e736e3eea9fed1f6b739694d`. The survivor Answer remains needs-update until rebuilt and independently reviewed against both source Questions, preserving the explicit array + window-size-K → each-window maximum contract without inventing missing edge conventions.
