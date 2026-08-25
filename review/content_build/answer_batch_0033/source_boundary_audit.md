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
