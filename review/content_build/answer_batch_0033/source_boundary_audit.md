# Answer Batch 0033 — source boundary audit

## cq_q_742b944807ccd957a6deaa5416e47617

- Exact repository source: `note_structured/663b7649000000001e038251.json`
- Preserved wording: `算法：给定数组找众数及其众数中的中位数`
- Source-preserved facts: the input is an array; the task involves the mode(s) and the median among the mode values.
- Not preserved by the source and therefore answer-side contracts only: integer element type, empty/null behavior, whether all tied modes must be returned, the definition of median when the mode count is even, output API shape, mutation policy, and implementation language.
- Candidate policy for this batch slice: treat all values tied at maximum frequency as the mode set; sort that set numerically; for an odd mode count return the middle value, for an even mode count return the arithmetic mean of the two middle values as `double`; reject null/empty input; do not mutate the input.
- Promotion remains blocked until isolated independent review verifies that the candidate keeps these answer-side choices explicit and that the executable fixture matches the fenced implementation.
