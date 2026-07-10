# C4 Controlled Review Trial

Completed: 2026-07-10. This was an agent-led closed-book content rehearsal used to test answer recallability and scheduler writes. It is deliberately labeled `C4内容验收试跑` and must not be interpreted as the user's personal mastery history.

## Outcome

| Metric | Result |
|---|---:|
| Distinct Canonical reviewed | 5 |
| Review marks recorded | 10 |
| Answer types represented | 5 |
| First-pass `hard` results | 5 |
| Second-pass `good` results | 5 |
| Feedback items written back to answers | 5 |
| Session events persisted | 10 |

Each card followed the same controlled loop:

```text
closed-book one-minute recall
  -> record a concrete omission as hard
  -> compare with the answer and add a recall guardrail
  -> repeat the one-minute recall
  -> record the corrected answer as good
```

## Trial Cards And Feedback

| Type | Canonical | First-pass gap | Answer feedback added |
|---|---|---|---|
| Concept | `cq_arraylist_9d3444a1` | repeated “LinkedList insert is fast” without including node-location cost | split indexed access, location and mutation complexity |
| Mechanism | `cq_aqs_f718305c` | omitted the Condition queue to synchronization queue transition | state that `signal` transfers only; the thread still reacquires the lock |
| Scenario | `cq_topic_fe047aa4` | started with components, without capacity assumptions; mixed qualification with final order success | require capacity assumptions and separate qualification, order and payment states |
| Coding | `cq_merge_intervals_866286e5` | initially stated O(n) and skipped endpoint semantics | state sorting O(n log n) first and clarify closed versus half-open intervals |
| Troubleshooting | `cq_jvm_oom_5adc3ce1` | jumped directly to heap dump | branch first by heap, metaspace, direct buffer, native thread and cgroup OOMKill |

## Scheduler Evidence

- `review/progress.json` now has five records with `review_count=2`, `mistake_count=1` and a next review date.
- `review/sessions/2026-07-10.json` contains ten durable events with the exact omissions and corrected recalls.
- `review weak` returns the five trial cards, so a first-pass miss remains discoverable even after the second `good` mark.

The five cards remain `weak` because the scheduler intentionally retains mistake history. This is useful behavior: one corrected recall does not erase a recorded gap.

## Content Decision

The trial showed that the eight-section answer structure is recallable when `易错点` contains a short, actionable guardrail. C5 and later answers should therefore preserve:

1. one explicit opening order for scenario/troubleshooting questions;
2. a single invariant plus complexity sentence for coding questions;
3. a “do not say the absolute shortcut” bullet for concept questions;
4. queue/state transition language for mechanism questions.

## Verification

- Review session count and per-card progress were read back from the repository.
- All five edited answers still pass strict validation.
- Full repository CI is recorded in the C4 stage commit.
