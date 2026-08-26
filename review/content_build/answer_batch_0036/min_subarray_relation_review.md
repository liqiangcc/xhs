# Minimum Subarray Source-First Relation Review

## Primary-source facts

- `85dca72d93b635bce7ae1bf0a34a4d6a`: raw source preserves “大于目标值的最短子数组”; current normalized Question is “算法：大于目标值的最短子数组？”.
- `c9140120c502ec6ff9bb5b3a272a7cc7`: raw source preserves “和大于等于目标值的最短连续子数组”.
- `f59bce25182f9cab55ea413875396272`: a second raw source independently preserves the same “和大于等于目标值的最短连续子数组” wording.
- corpus-wide active source-near enumeration for target-value minimum subarrays returns exactly these three Questions.
- none of the three raw source fragments preserves the element-sign domain, target domain, exact API, examples, or empty/no-solution output convention.

No historical relation/remediation decision was consulted before this conclusion.

## Decisions

1. `c9140120c502ec6ff9bb5b3a272a7cc7` and `f59bce25182f9cab55ea413875396272`: relation `same`. Both preserve the same >= target contiguous-minimum-subarray contract; wording differences are presentation only. Preserve `cq_q_c9140120c502ec6ff9bb5b3a272a7cc7` as survivor and retire duplicate `cq_q_f59bce25182f9cab55ea413875396272`.
2. `85dca72d93b635bce7ae1bf0a34a4d6a` versus the >= pair: relation `related`, not `same`. The strict > versus >= comparator changes equality-boundary outputs, so source-first normalization must not erase that distinction absent stronger evidence that the strict source is a transcription error. Preserve `cq_q_85dca72d93b635bce7ae1bf0a34a4d6a` independently.
3. Content consequence: both surviving Answers remain `needs_update`. A sliding-window implementation is only conditionally valid when the element domain gives the needed monotonicity (for example positive/nonnegative inputs); the raw sources do not preserve that constraint. Rebuild/review must label any adopted executable domain rather than presenting it as source fact.
