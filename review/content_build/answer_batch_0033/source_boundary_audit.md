# Answer Batch 0033 — source boundary audit

## cq_q_742b944807ccd957a6deaa5416e47617

- Exact repository source: `note_structured/663b7649000000001e038251.json`
- Preserved wording: `算法：给定数组找众数及其众数中的中位数`
- Source-preserved facts: the input is an array; the task involves the mode(s) and the median among the mode values.
- Not preserved by the source and therefore answer-side contracts only: integer element type, empty/null behavior, whether all tied modes must be returned, the definition of median when the mode count is even, output API shape, mutation policy, and implementation language.
- Candidate policy for this batch slice: treat all values tied at maximum frequency as the mode set; sort that set numerically; for an odd mode count return the middle value, for an even mode count return the arithmetic mean of the two middle values as `double`; reject null/empty input; do not mutate the input.
- Promotion remains blocked until isolated independent review verifies that the candidate keeps these answer-side choices explicit and that the executable fixture matches the fenced implementation.

## cq_q_74466a9b0dc9f7c95566f1f3641dc7b0

- Exact repository source: `note_tagged/67fcfada000000001c00fe70.json`
- Preserved wording: `算法实现：求最长连续序列（LeetCode 128）。`
- Source-preserved facts: this is the Longest Consecutive Sequence algorithm task identified as LeetCode 128.
- Not preserved by the repository source and therefore answer-side contracts only: Java method signature, null-input behavior, whether the input may be mutated, exact integer bounds, and whether the interviewer requires a specific data structure.
- Candidate policy for this batch slice: use an `int[]` Java API, return 0 for empty input, reject null input, do not mutate the input, use a HashSet and expand only from values with no representable predecessor, and guard integer-boundary arithmetic explicitly.
- Promotion remains blocked until isolated independent review verifies source boundaries, exact fenced-code execution, evidence, and repository gates.

## cq_q_7531e07d0f1e21e2eb6dab2bae97c0e9

- Exact repository projections: `note_structured/682bc94900000000220258d7.json` and `note_tagged/682bc94900000000220258d7.json`.
- Stronger raw source: `note_json/682bc94900000000220258d7.json` says the HR round assessed the interviewee's soft qualities (communication and stress resistance) and also asked some questions about personal experience; it does not preserve any concrete soft-skill question and contains no quick-sort coding task at this position.
- Current projected wording: `软素质、沟通能力、抗压能力考察`.
- Disposition: fail closed as `incomplete_or_unreadable`. The phrase is an assessment-category summary, not a recoverable interview Question; the current Coding/quick-sort metadata is unsupported derived contamination.
- Required remediation: mark the tagged row invalid with an explicit reason, record the validity-audit exclusion, retire singleton Canonical `cq_q_7531e07d0f1e21e2eb6dab2bae97c0e9`, remove its ReviewProgress, archive its placeholder baseline Answer, rebuild Question/index/type projections, and keep the invalid Question as an explained non-Canonical projection.
- No Coding candidate may be authored from the unsupported `快排` entity.

## cq_q_754f6f2262137c4a1450a526c68c6553

- Exact repository projections: `note_structured/67e14815000000001b025250.json` and `note_tagged/67e14815000000001b025250.json`.
- Stronger raw source: `note_json/67e14815000000001b025250.json` preserves only `一道动态规划（忘了，有点难，没做出来）`.
- Current projected wording: `算法：关于动态规划 (DP) 的难题。`.
- Disposition: fail closed as `incomplete_or_unreadable`. Neither the raw note nor the structured projection preserves the DP state, input/output, constraints, examples, recurrence, or problem identity, so no deterministic Coding contract can be recovered.
- Required remediation: mark the tagged row invalid with an explicit reason, record the validity-audit exclusion, retire singleton Canonical `cq_q_754f6f2262137c4a1450a526c68c6553`, remove its ReviewProgress, archive its placeholder baseline Answer, rebuild Question/index/type projections, and keep the invalid Question as an explained non-Canonical projection.
- No generic DP answer may be promoted as a substitute for the forgotten source question.

## cq_q_7560e894f762ce0a02c9838d710a0b25

- Exact repository projections: `note_structured/67ee3c15000000001c0327c9.json` and `note_tagged/67ee3c15000000001c0327c9.json`.
- Stronger OCR source: `note_img_txt/67ee3c15000000001c0327c9.txt` preserves only `最后代码题给一段代码回答是在实现什么, 并且有哪些问题`; it does not preserve the code body.
- Raw note JSON has only the generic post description and image metadata; the missing code is not recoverable there either.
- Current projected wording: `代码理解：给一段代码，分析其实现功能及潜在问题？`.
- Disposition: fail closed as `incomplete_or_unreadable`. Without the actual code, neither its behavior nor its potential defects can be reviewed deterministically.
- Required remediation: mark the tagged row invalid with an explicit reason, record the validity-audit exclusion, retire singleton Canonical `cq_q_7560e894f762ce0a02c9838d710a0b25`, remove its ReviewProgress, archive its placeholder baseline Answer, rebuild Question/index/type projections, and preserve the invalid row as an explained non-Canonical projection.
- A generic code-review checklist must not be promoted as if it answered the missing code sample.

## cq_q_7642700411d0977839a2cd01a41e50ad

- Exact repository source: `note_tagged/663bb0e8000000001e027dad.json`.
- Preserved wording: `编程题：计算二维空间中点到直线的距离（C++实现）。`
- Source-preserved facts: this is a two-dimensional point-to-line distance coding task and the requested implementation language is C++.
- Not preserved by the repository source and therefore answer-side contracts only: how the infinite line is represented, the function signature, coordinate type/range, finite-value policy, degenerate-line behavior, required C++ standard, output precision, and whether distance to a segment rather than an infinite line is intended.
- Candidate policy for this slice: represent the infinite line by two distinct points A and B, use finite `long double` coordinates, reject A==B, return non-negative perpendicular distance to the infinite line, and compile the exact displayed implementation as C++20.
- Promotion remains blocked until an isolated independent reviewer verifies source boundaries, exact fenced-code execution, numerical/degenerate cases, evidence, and repository gates.

## cq_q_768f8eb71596f7b6824861aae95d9f08

- Exact repository source: `note_tagged/663b7649000000001e038251.json`.
- Preserved wording: `算法/手撕：N分钱换成1/2/3分硬币的所有组合方式 (动态规划/递归)`
- Source-preserved facts: an amount N cents is to be exchanged using 1/2/3-cent coins; the source asks for all combination ways and explicitly mentions dynamic programming / recursion.
- Not preserved by the repository source and therefore answer-side contracts only: whether "all combinations" means enumerate combinations or return only their count, whether coin supply is unlimited, whether order matters, the programming language/API, N's range, the N=0 convention, negative-input behavior, and output ordering.
- Candidate policy for this slice: treat coin supply as unlimited and order-insensitive; enumerate each combination as counts of 1/2/3-cent coins, return one empty combination for N=0 and none for N<0; additionally give a combination-count DP because the source explicitly mentions DP. Java 17 syntax is an answer-side implementation choice and the exact displayed code is compiled on JDK 21.
- Promotion remains blocked until an isolated independent reviewer verifies exact source boundaries, enumeration uniqueness/completeness, DP combination semantics versus permutation overcounting, exact fenced-code execution, evidence, and repository gates.

## cq_q_779e5c61c5f999e26fabf2ab777035b1

- Stronger raw OCR source: `note_img_txt/67ee3c15000000001c0327c9.txt` preserves `sql题找出成绩前十的学生`.
- Tagged projection: `note_tagged/67ee3c15000000001c0327c9.json` preserves `SQL：找出成绩排名前十的学生？`.
- Source-preserved facts: this is an SQL task asking for the students whose grades/scores are in the top ten; the tagged projection classifies it as MySQL practice and carries SQL/LIMIT entities.
- Not preserved by either source: table/column names, whether each student has one score or many course-grade rows, the exact ranking metric, whether "top ten" means exactly ten rows or top-ten rank levels including ties, tie-break policy, NULL/no-score behavior, output columns, MySQL version, and index/schema constraints.
- Candidate policy for this slice: use `students(student_id,name)` plus exactly one non-NULL final row `scores(student_id,score)` per scored student; interpret top ten as at most ten rows, sort by score descending and student_id ascending for deterministic tie breaking, and exclude students without a score via INNER JOIN. The primary query uses portable MySQL LIMIT syntax; window-function and multi-course aggregation variants remain explicit follow-ups rather than recovered requirements.
- Promotion remains blocked until isolated independent review verifies source boundaries, deterministic tie behavior, exact SQL execution against fixtures, alternatives for ties/multiple grades, evidence, and repository gates.

## cq_q_7a75022f873e722084923cc7db60e1bb

- Exact repository source: `note_tagged/689455070000000023019aa8.json`.
- Preserved wording: `编程：单线程调用一个函数，实现一个限流器，当函数调用频率超过阈值时返回false，否则True。`
- Source-preserved facts: this is a single-thread coding task; repeated calls are admitted or rejected by returning true/false according to a rate threshold.
- Not preserved by the source: fixed vs sliding window, whether rejected attempts count, the threshold/window units, clock API, exact boundary semantics, language/API, invalid-clock behavior, and concurrency semantics beyond the explicit single-thread condition.
- Candidate policy: implement an admission sliding-window limiter in Java with an injected non-negative non-decreasing millisecond clock; permit at most maxCalls accepted calls in the half-open interval (now-windowMillis, now]; rejected attempts do not consume capacity; exact-boundary accepted timestamps expire.
- Promotion remains blocked until isolated independent review verifies source boundaries, exact fenced-code behavior, evidence, and repository gates.

## cq_q_7b1c9751da7c787b856440f7bc4088c8

- Exact repository source: `note_tagged/67e12cfa000000001d02777a.json`.
- Preserved wording: `算法：删除链表所有重复数字（不允许用map或者set）`
- Source-preserved facts: this is a linked-list coding task asking to delete duplicate numbers and explicitly forbidding Map/Set in the solution.
- Not preserved by the source: whether the list is sorted, whether duplicate means keep one copy or remove every occurrence of any repeated value, node/API shape, mutation policy, value range, language, and cycle behavior.
- Candidate policy: do not assume sorting; interpret “删除所有重复数字” as removing every node whose value occurs more than once anywhere in the original acyclic list; use no Map/Set in the solution, relink in place, preserve the relative order of values that occur exactly once, and return the new head.
- Promotion remains blocked until isolated independent review verifies source boundaries, exact fenced-code behavior, evidence, and repository gates.
