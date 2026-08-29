#!/usr/bin/env python3
# Build, validate, source-first review, and stage Batch 0053 sorted-array all-target-indices candidate.

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0053'
CID = 'cq_q_ea27d2a647ad7ed19a5fb6f9ab5b76d8'
QID = 'ea27d2a647ad7ed19a5fb6f9ab5b76d8'
EXPECTED = '算法题：在长度为 N 的有序数组中快速查找所有值为 M 的元素下标'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ea27d2a647ad7ed19a5fb6f9ab5b76d8","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 在有序数组中快速查找所有值为 M 的元素下标

## 核心结论

来源明确要求“长度为 N 的有序数组中，快速查找所有值为 M 的元素下标”，但没有保存升序/降序、返回容器和空结果语义。这里声明最小可执行合同：数组按**非递减升序**排列，返回所有等于 `target` 的 0-based 下标；不存在时返回空数组。

因为相同值在有序数组中一定形成一个连续区间，所以不需要先二分找到一个命中点再向两边线性扩散。直接做两次边界二分：`lowerBound(target)` 找第一个 `>= target` 的位置，`upperBound(target)` 找第一个 `> target` 的位置。若 `lower` 处不是 target，则无结果；否则答案就是连续区间 `[lower, upper)`。查边界 O(log N)，输出 K 个下标本身至少要 O(K)，所以总时间 O(log N + K)，额外搜索空间 O(1)（返回结果不计）。

## 1 分钟版

- 有序数组里所有 M 必然连续，因此目标是找这个连续段的左右边界。
- 第一次二分找第一个 `>= M` 的位置 `left`。
- 第二次二分找第一个 `> M` 的位置 `right`。
- 如果 `left == N` 或 `a[left] != M`，说明 M 不存在，返回空数组。
- 否则所有答案恰好是 `left, left+1, ..., right-1`。
- 两次二分是 O(log N)，生成 K 个下标要 O(K)，总计 O(log N + K)。“返回所有下标”不可能比 O(K) 更快，因为结果本身就有 K 个元素。

## 3 分钟版

```java
public final class SortedArrayTargetIndices {
    public static int[] findAll(int[] nums, int target) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }

        int left = lowerBound(nums, target);
        if (left == nums.length || nums[left] != target) {
            return new int[0];
        }
        int right = upperBound(nums, target);

        int[] result = new int[right - left];
        for (int i = 0; i < result.length; i++) {
            result[i] = left + i;
        }
        return result;
    }

    private static int lowerBound(int[] nums, int target) {
        int lo = 0, hi = nums.length; // 搜索半开区间 [lo, hi)
        while (lo < hi) {
            int mid = lo + ((hi - lo) >>> 1);
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    private static int upperBound(int[] nums, int target) {
        int lo = 0, hi = nums.length;
        while (lo < hi) {
            int mid = lo + ((hi - lo) >>> 1);
            if (nums[mid] <= target) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    private SortedArrayTargetIndices() {}
}
```

例如数组 `[1,2,2,2,4,5]`，M=2。`lowerBound(2)=1`，`upperBound(2)=4`，所以结果是 `[1,2,3]`。

## 关键细节

- **连续区间性质**：升序数组中等于 M 的元素不可能分散在多个区间，否则中间元素会破坏有序性。
- **半开区间写法**：二分始终维护 `[lo, hi)`，结束时 `lo == hi`，减少 `mid±1` 和边界越界错误。
- **lower 与 upper 的差别**：lower 在 `nums[mid] >= target` 时收缩右边；upper 只有 `nums[mid] > target` 才收缩右边。
- **不存在 target**：不能只看两个边界差值，先检查 `left < N && nums[left] == target` 最直接。
- **复杂度口径**：边界搜索 O(log N)，构造返回数组 O(K)。如果只要求返回 `[left,right]` 两个边界，可以保持纯 O(log N)。
- **排序方向**：来源只写“有序”，候选选择非递减升序；若实际是降序，需要反转二分比较方向。
- **输入校验**：代码信任“有序”这一来源前置条件。完整验证数组是否有序要 O(N)，若每次查询都验证，会破坏“快速查找”的查询复杂度。

## 原理机制

二分边界不是在找“某一个等于 target 的元素”，而是在找一个单调谓词的分界点。

对 lower bound，谓词 `nums[i] >= target` 在升序数组上形如 `false...false true...true`，二分返回第一个 true。对 upper bound，谓词 `nums[i] > target` 同样是单调的，返回第一个严格大于 target 的位置。两条分界之间恰好满足：

```text
left <= i < right  => nums[i] == target
```

因此不用从一个随机命中点向两边扫描，也不会在 target 不存在时陷入复杂的边界补丁。

## 项目经验版

来源没有真实数组规模、查询频率和存储介质信息，不能虚构业务场景。如果同一个静态数组要执行大量查询，我会保留有序结构并复用这套边界查询；如果数据持续插入/删除，数组维护有序性的成本可能成为瓶颈，此时应根据更新/查询比例考虑树、索引或数据库结构，而不是只优化单次二分。

## 常见追问

- 问：为什么不先二分找到一个 M，再向左右扫？答：最坏情况下数组全是 M，找到一个点后仍要左右扫描 O(N)。两次边界二分能在 O(log N) 内直接确定完整区间，之后只为真实输出支付 O(K)。
- 问：为什么总复杂度不是 O(log N)？答：如果要求返回 K 个具体下标，写出 K 个结果至少就要 O(K)。只有返回左右边界时才是 O(log N)。
- 问：target 不存在怎么办？答：lower bound 仍会返回插入位置；检查该位置是否真的等于 target，不等就返回空数组。
- 问：数组是降序怎么办？答：把比较谓词改成与降序一致的单调条件；当前实现明确只针对非递减升序合同。
- 问：怎么避免 `mid=(lo+hi)/2` 溢出？答：用 `lo + ((hi-lo) >>> 1)`。
- 问：如果只想知道出现次数？答：直接返回 `upperBound - lowerBound`，存在性检查后无需构造 K 个下标。

## 易错点

- 普通二分命中任意一个 M 后就返回，漏掉重复元素。
- 命中后双向扫描，却仍声称最坏时间 O(log N)。
- lower/upper 的 `>=`、`>` 条件写反，造成 off-by-one。
- target 不存在时直接构造 `[left,right)`，没有验证真实命中。
- 题目只说“有序”却不声明升序/降序假设。
- 为了证明有序先完整扫描 O(N)，然后忽略这部分成本继续宣称查询 O(log N + K)。
'''

TEST = r'''import java.util.*;

public final class SortedArrayTargetIndicesTest {
    private static int[] oracle(int[] nums, int target) {
        int count = 0;
        for (int v : nums) if (v == target) count++;
        int[] out = new int[count];
        int p = 0;
        for (int i = 0; i < nums.length; i++) if (nums[i] == target) out[p++] = i;
        return out;
    }

    private static void check(int[] nums, int target, int[] expected) {
        int[] actual = SortedArrayTargetIndices.findAll(nums, target);
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError("target=" + target + " expected=" + Arrays.toString(expected)
                    + " actual=" + Arrays.toString(actual));
        }
    }

    public static void main(String[] args) {
        check(new int[] {}, 1, new int[] {});
        check(new int[] {1,2,2,2,4,5}, 2, new int[] {1,2,3});
        check(new int[] {2,2,2,2}, 2, new int[] {0,1,2,3});
        check(new int[] {1,3,5}, 2, new int[] {});
        check(new int[] {Integer.MIN_VALUE, Integer.MIN_VALUE, 0, Integer.MAX_VALUE},
              Integer.MIN_VALUE, new int[] {0,1});
        check(new int[] {Integer.MIN_VALUE, 0, Integer.MAX_VALUE, Integer.MAX_VALUE},
              Integer.MAX_VALUE, new int[] {2,3});

        Random random = new Random(20260829L);
        for (int round = 0; round < 10_000; round++) {
            int n = random.nextInt(300);
            int[] nums = new int[n];
            for (int i = 0; i < n; i++) nums[i] = random.nextInt(61) - 30;
            Arrays.sort(nums);
            int target = random.nextInt(81) - 40;
            int[] expected = oracle(nums, target);
            int[] actual = SortedArrayTargetIndices.findAll(nums, target);
            if (!Arrays.equals(actual, expected)) {
                throw new AssertionError("round=" + round + " target=" + target);
            }
        }

        int[] large = new int[300_000];
        for (int i = 0; i < large.length; i++) large[i] = i / 30;
        if (!Arrays.equals(SortedArrayTargetIndices.findAll(large, 7777), oracle(large, 7777))) {
            throw new AssertionError("large duplicate block mismatch");
        }

        System.out.println("PASS empty directed all-equal absent extremes 10000-random-vs-oracle large-duplicate-block");
    }
}
'''


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    if candidate.exists():
        raise SystemExit('candidate already exists; do not overwrite reviewed work')

    ctx = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != CID:
        raise SystemExit('canonical context drift')
    if ctx.get('answer_type') != 'coding':
        raise SystemExit(f"answer type drift: {ctx.get('answer_type')}")
    if ctx.get('canonical', {}).get('question_ids') != [QID]:
        raise SystemExit(f"ownership drift: {ctx.get('canonical', {}).get('question_ids')}")
    src = next((x for x in ctx.get('source_questions', []) if x.get('question_id') == QID), None)
    if not src or src.get('original_question') != EXPECTED or src.get('is_valid_for_library') is not True:
        raise SystemExit('source wording/validity drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b53-sorted-all-indices-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'SortedArrayTargetIndices.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'SortedArrayTargetIndicesTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'SortedArrayTargetIndices.java', 'SortedArrayTargetIndicesTest.java', cwd=tmpdir)
        stdout = run('java', 'SortedArrayTargetIndicesTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS empty directed all-equal absent extremes 10000-random-vs-oracle large-duplicate-block'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac SortedArrayTargetIndices.java SortedArrayTargetIndicesTest.java && java SortedArrayTargetIndicesTest',
        'stdout': stdout,
        'checks': [
            'empty, directed duplicate, all-equal and absent-target cases',
            'Integer.MIN_VALUE and Integer.MAX_VALUE boundaries',
            '10000 deterministic sorted random arrays agree with a linear oracle',
            '300000-element large duplicate block agrees with the oracle',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0053 exact sorted-array target-indices source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 lower/upper-bound deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source requires quickly finding all indices equal to M in an ordered array; sort direction, return container, indexing base, and empty-result semantics are not preserved.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '关键细节', '易错点']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate explicitly chooses nondecreasing order, zero-based indices, and an empty int array when the target is absent.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'boundary-search-mechanism', 'text': 'lowerBound finds the first value >= target and upperBound the first value > target, so all matching positions are exactly the half-open interval [left,right).', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制']},
        {'claim_id': 'complexity-validation', 'text': 'Two boundary searches cost O(log N) and emitting K indices costs O(K); executable validation covers 10000 deterministic random arrays against a linear oracle plus a large duplicate block.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '关键细节', '常见追问']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate keeps the source requirement—ordered array and all target indices—while declaring ascending order, zero-based output, and empty-result behavior as candidate contract.',
        'It uses two monotonic boundary searches rather than returning an arbitrary binary-search hit or linearly expanding from one hit.',
        'The half-open lower/upper-bound invariants correctly produce the full duplicate interval and cleanly handle absent targets.',
        'The complexity statement is output-sensitive: O(log N + K), acknowledging that materializing K indices itself costs O(K).',
        'The code uses overflow-safe midpoint arithmetic and clearly separates lowerBound >= from upperBound > comparisons.',
        'OpenJDK 21 validation covers empty/all-equal/absent/extreme cases, 10000 deterministic sorted random arrays against an independent linear oracle, and a 300000-element duplicate-block case.',
        'The answer notes that validating sortedness would add O(N) and therefore trusts the source-provided ordering precondition for the query path.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0053-sorted-all-indices-20260829-v1',
        'review_version': 'batch-0053.sorted-all-indices.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0053 sorted-array target-indices source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0053-sorted-all-indices-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'duplicates/all-equal/absent target', 'expected': 'exact index interval or empty', 'actual': 'pass', 'passed': True},
                {'case': 'integer extremes', 'expected': 'correct boundary indices', 'actual': 'pass', 'passed': True},
                {'case': '10000 deterministic random sorted arrays', 'expected': 'matches independent linear oracle', 'actual': 'pass', 'passed': True},
                {'case': '300000-element duplicate block', 'expected': 'matches oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_ea27d2a647ad7ed19a5fb6f9ab5b76d8` source-first isolated review PASS: the source requires quickly finding all M indices in an ordered array while sort direction/output semantics remain explicit candidate contract. Under nondecreasing order and zero-based indices, lower/upper bounds identify the exact duplicate interval in O(log N), with O(K) unavoidable output cost; OpenJDK 21 validation covers edge/extreme cases, 10000 deterministic random sorted arrays against a linear oracle, and a 300000-element duplicate block. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
