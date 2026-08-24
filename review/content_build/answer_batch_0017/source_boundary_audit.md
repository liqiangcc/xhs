# Answer Batch 0017 — Source Boundary Audit

Date: 2026-08-23

This audit is intentionally source-first. It records only facts recoverable from repository source material before candidate generation. Missing contracts remain explicit; familiar LeetCode names, inferred schemas, or generic coding templates must not be imported as if they were present in the source. This audit covers **10/10 Canonicals** in answer batch 0017 and performs **no formal promotion**.

## `cq_q_23224fdbc8bddfe239dc7f0da36fd480`

- Source: `note_desc/68b154a8000000001c032fa1.txt` plus matching structured/tagged records.
- Raw wording/context: `手撕，从行升序列升序的二维数组中判断target数是否存在`.
- Boundary result: **recoverable**. The source preserves the essential contract: a two-dimensional array whose rows and columns are ascending, and a membership query for `target`.
- Missing source details: primitive type, whether “升序” is strict or nondecreasing, empty/ragged-matrix behavior, and whether the interviewer expects the top-right/bottom-left linear walk specifically are not stated.
- Required candidate boundary: state a rectangular `int[][]` API and empty-input behavior explicitly, treat duplicate values as allowed unless a stricter source is recovered, and prove/test the monotone corner-walk invariant instead of substituting an unrelated sliding-window template.
- Disposition: `candidate_allowed_with_explicit_matrix_api_assumptions`.

## `cq_q_2366a87ab109eca0a9aac3ebad1db2f9`

- Source: `note_desc/67fc9e5b000000001b03d02e.txt` plus matching structured/tagged records.
- Raw wording/context: `一上来就手撕：矩阵螺旋输出（给15分钟，超时就叫停）`.
- Boundary result: **recoverable as spiral traversal/output**, not matrix generation. The source explicitly says to output an existing matrix in spiral order.
- Missing source details: element type, empty/ragged input, clockwise direction/start corner, and concrete return/output API are not stated.
- Required candidate boundary: choose and label a conventional rectangular API (for example clockwise from top-left), validate one-row/one-column/rectangular cases, and do not silently turn the problem into LeetCode 59 matrix generation.
- Disposition: `candidate_allowed_with_explicit_spiral_output_api_assumptions`.

## `cq_q_240610761d28b1bf39c0dc3ff65a01f7`

- Source: `note_desc/68b83bdb000000001d02e1fa.txt`, compared with `note_structured/68b83bdb000000001d02e1fa.json` and matching tagged data.
- Raw wording/context: `一道算法题，给了一个场景，然后需要完成这道题，不是力扣上面的，这里怕被开盒，我就不说了。（写了差不多一小时，有点难）`.
- Source-widening finding: the structured/current Question rewrites this intentionally withheld problem as `算法手撕：特定场景复杂算法（自定义业务逻辑）`, but the repository still contains **no input, output, constraints, examples, or business rule** from which a coding task can be reconstructed.
- Boundary result: **not recoverable enough for a strict answer**. Any implementation would fabricate the missing problem.
- Required remediation: classify the Question as incomplete/unrecoverable (with the explicit source reason that the author withheld the scenario), then retire or remap the unsupported singleton Canonical/Answer/ReviewProgress through the supported normalization flow. Do not generate a generic “complex algorithm” answer.
- Disposition: `normalization_and_question_remediation_required_unrecoverable_source`.

## `cq_q_24dba68ff950ae9989f218f7f4e3d55d`

- Source: `note_desc/678bb5fd000000001b008919.txt` plus matching structured/tagged records.
- Raw wording/context: `给你一个数，每次可以进行加或减2的n次方操作，最少多少次操作把该数变为0？把你所说的思路用代码实现一下`.
- Boundary result: **recoverable with exponent/input-domain choices**. The operation family and optimization target are explicit: repeatedly add or subtract a power of two and minimize the number of operations until zero.
- Missing source details: whether the input may be negative/zero, whether `n` ranges over all nonnegative integers on every move, integer width/overflow behavior, and required language/API are not stated.
- Required candidate boundary: state those choices explicitly, avoid an unbounded search, justify the signed-binary/nearest-power recurrence used, and differential-test small magnitudes against an independent shortest-path or exhaustive oracle.
- Disposition: `candidate_allowed_with_explicit_power_and_integer_domain_assumptions`.

## `cq_q_25996ab2beb9a70091998ac5eb0063aa`

- Source: `note_desc/67da6aa8000000000603d035.txt`, compared with `note_structured/67da6aa8000000000603d035.json` and existing spiral-matrix Canonicals.
- Raw wording/context: the retained caption says only `补充 lc 螺旋矩阵`.
- Ambiguity finding: “lc 螺旋矩阵” does not identify whether the source means spiral traversal (commonly LeetCode 54), spiral matrix generation (commonly LeetCode 59), or another variant. The repository already contains distinct Canonicals including `cq_q_2366a87ab109eca0a9aac3ebad1db2f9` for source-recoverable spiral output and `cq_q_6dfc45bd535b894c5de755254b01ca58` labelled Spiral Matrix II.
- Boundary result: **not deterministic enough to author a separate strict coding answer** from this source alone.
- Required remediation: recover stronger source evidence identifying the intended variant. If none exists, classify this Question as ambiguous/incomplete and remove the unsupported singleton Canonical rather than guessing or duplicating one of the existing spiral variants.
- Disposition: `normalization_required_ambiguous_spiral_variant`.

## `cq_q_26cf490d9490e9cd7962dbe074fdc06d`

- Source: `note_desc/67bc01b9000000002900bc29.txt`, compared with `note_structured/67bc01b9000000002900bc29.json` and matching tagged data.
- Raw wording/context: `出了一道sql题，花了有5分钟才写出来，提交的时候多写了个")"然后报错了，面试官人很好给了提醒`.
- Source-widening finding: the current Question claims `特定的复杂 SQL 查询场景 (业务多表关联与聚合)`, but the raw source does not preserve tables, columns, joins, aggregation requirements, expected result, or even whether the SQL involved multiple tables.
- Boundary result: **not recoverable enough for a strict SQL answer**.
- Required remediation: remove the unsupported “多表关联与聚合” widening and classify the source Question as incomplete/unrecoverable unless stronger original material is found. Do not manufacture a schema/CTE and present it as the interview answer.
- Disposition: `normalization_and_question_remediation_required_unrecoverable_sql_contract`.

## `cq_q_271d5e7c97e9f51b7b5ab4fdc1331411`

- Source: `note_desc/67ee9898000000000900e85f.txt` plus matching structured/tagged records; a second repository note (`note_desc/6661b50a0000000006006ab3.txt`) also records `LeetCodel15不同的子序列(dp)`.
- Raw wording/context: the first source explicitly records LeetCode 115, strings `s` and `t`, counting subsequences of `s` equal to `t`, time-complexity analysis, space optimization, and the `rabbbit`/`rabbit` → `3` example.
- Duplicate finding: the repository already has `cq_q_6c3e7f9d826622bce0c25df5beee24a0` titled `算法：不同的子序列 (LeetCode 115 - DP)`. These are the same underlying task, not two independent concepts that need separate strict answers.
- Boundary result: **source is recoverable, but this singleton Canonical should not be independently answered until normalization resolves the duplicate**.
- Required remediation: attach all source Question IDs for the LeetCode 115 task to one surviving Canonical, retire the duplicate Canonical through the supported maintenance flow, then build one strict-valid answer with the 2-D DP and reverse-order 1-D space optimization contract.
- Disposition: `normalization_merge_required_before_answer_generation`.

## `cq_q_271dea4873c463bfe83f5ef2f5d26004`

- Source: `note_img_txt/680e66cb0000000023012aa3.txt` plus matching structured/tagged records.
- Raw wording/context: Tencent WXG third-round coding list includes exactly `用rand39生成rand51`.
- Boundary result: **recoverable only under an explicit randN convention**. The source identifies the transformation but does not define whether `rand39` is uniform, independent across calls, or returns `[0,38]` versus `[1,39]`; without uniformity there is no justified uniform `rand51` construction.
- Required candidate boundary: explicitly define the conventional API assumption (independent uniform integers over a stated 39-value range, target uniform over a stated 51-value range), use rejection sampling over an equiprobable product space, prove that accepted states partition uniformly, and validate the implementation with deterministic source injection plus distribution/property checks. Do not claim the range convention itself came from the source.
- Disposition: `candidate_allowed_with_explicit_uniform_randn_contract_assumption`.

## `cq_q_27d7a2728feaeca0d6b67a1e7ba30f68`

- Source: `note_desc/630e2e22000000001103c490.txt` plus matching structured/tagged records.
- Raw wording/context: `一个数组中是否能找到一个数大于其他数字的2倍，找到返回它的索引，否则返回-1`.
- Boundary result: **recoverable with numeric-domain and comparison-policy gaps**. The task asks for an index only when one element is greater than twice every other element; otherwise `-1`.
- Important source boundary: the retained wording says `大于` (strictly greater), not “at least twice”. A familiar LeetCode “dominant index” statement must not silently change this to `>=`.
- Missing source details: integer type/range, negative-number policy, empty/singleton behavior, uniqueness/tie behavior, and overflow handling are not stated.
- Required candidate boundary: state an `int[]` contract explicitly, compare in a widened numeric type to avoid `2*x` overflow, preserve the source’s strict comparison unless stronger evidence says otherwise, and test negatives/duplicates/singletons in addition to ordinary positive arrays.
- Disposition: `candidate_allowed_with_explicit_numeric_and_strict_comparison_assumptions`.

## `cq_q_27f9476e6f17473bae89a7a3c05db42f`

- Source: `note_desc/6661b50a0000000006006ab3.txt` plus matching structured/tagged records.
- Raw wording/context: `创建两个线程交替打印 AB`.
- Duplicate finding: the repository already contains `cq_q_8f04cfa510fe868afcf072c93499a8ea` titled `两个线程交替打印 abababab 如何实现（wait/notify 或 Semaphore）？`. The core behavioral requirement is the same two-thread alternation problem; the generic source does not justify a second independent Canonical.
- Missing source details: number of repetitions, which thread starts, allowed synchronization primitive, interruption behavior, and whether output must be captured versus printed to stdout are not stated.
- Boundary result: **normalization review is required before answer generation**. A single surviving Canonical can expose the repetition count as an API parameter and discuss multiple valid coordination mechanisms without duplicating the concept.
- Required remediation: compare all source variants attached to both Canonicals, merge when no incompatible requirement is found, then author/test one strict answer. Do not create a second strict answer merely because one source says `AB` and another spells out `abababab`.
- Disposition: `normalization_merge_review_required_before_answer_generation`.

## Batch disposition

The source-first pass covers all 10 Canonicals in batch 0017:

- source-qualified candidate path with explicit boundaries: `cq_q_23224fdbc8bddfe239dc7f0da36fd480`, `cq_q_2366a87ab109eca0a9aac3ebad1db2f9`, `cq_q_24dba68ff950ae9989f218f7f4e3d55d`, `cq_q_271dea4873c463bfe83f5ef2f5d26004`, `cq_q_27d7a2728feaeca0d6b67a1e7ba30f68`;
- normalization / Question remediation rather than fabricated answer generation: `cq_q_240610761d28b1bf39c0dc3ff65a01f7`, `cq_q_25996ab2beb9a70091998ac5eb0063aa`, `cq_q_26cf490d9490e9cd7962dbe074fdc06d`, `cq_q_271d5e7c97e9f51b7b5ab4fdc1331411`, `cq_q_27f9476e6f17473bae89a7a3c05db42f`.

Counts alone do not complete the batch. No candidate is promoted by this audit. Candidate-path items still require candidate content, schema-valid evidence, isolated review, executable tests, and the repository's human/promotion gates. Remediation items must be resolved against the Question/Canonical SSOT first so that final content closure does not preserve fabricated, ambiguous, or duplicate Canonicals.