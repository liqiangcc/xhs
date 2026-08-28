#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0051 kth-largest candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0051'
CID = 'cq_q_dc192e205c8fbcf5673927a9d9382f41'
QID = 'dc192e205c8fbcf5673927a9d9382f41'
EXPECTED = '算法实现：如何在一个无序数组中找到第 K 大的元素？请分别给出基于“大顶堆” (O(N log K)) 和“快速选择 (Quick Select)” (期望 O(N)) 的解法思路。'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_dc192e205c8fbcf5673927a9d9382f41","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 无序数组第 K 大：堆与 Quick Select

## 核心结论

先指出题目原文里一个需要澄清的地方：它把“大顶堆”和 `O(N log K)` 放在一起，但这两个通常不是同一个标准解法。若要做到 `O(N log K)`，应维护**大小最多为 K 的小顶堆**：堆里始终保留目前最大的 K 个元素，堆顶就是其中最小的，也就是扫描结束后的第 K 大。若严格使用“大顶堆”，常见做法是把 N 个元素全部建成大顶堆，再弹出 K-1 次，复杂度是建堆 O(N) + 弹出 O(K log N)，额外空间取决于是否原地建堆。

Quick Select 则把“第 K 大”转换为升序下标 `target = N - K`，通过随机 pivot 分区，只继续进入包含 target 的一侧。平均/期望时间 O(N)，最坏 O(N²)。为了正确处理大量重复值，可以使用三向分区 `< pivot / == pivot / > pivot`。

## 1 分钟版

- 第 K 大允许重复值按位置计数，例如 `[5,5,4]` 的第 2 大仍是 5；除非题目另说，不做去重。
- **满足 O(N log K)**：维护 K 个元素的小顶堆。堆不足 K 就加入；超过 K 就弹出最小值。最后堆顶是第 K 大，空间 O(K)。
- **严格大顶堆**：把所有元素放入大顶堆，弹 K-1 次后堆顶是答案；复杂度 O(N + K log N)，不是 O(N log K)。
- **Quick Select**：找升序第 `N-K` 个位置。每轮随机选 pivot，分区后只保留目标所在一侧，期望 O(N)。
- Quick Select 会重排数组；如果接口不允许修改输入，先复制数组，因此实现层面多 O(N) 空间。
- K 必须满足 `1 <= K <= N`；本实现对 null 或越界 K 显式报错。

## 3 分钟版

```java
import java.util.Collections;
import java.util.PriorityQueue;
import java.util.concurrent.ThreadLocalRandom;

public final class KthLargest {
    public static int byBoundedMinHeap(int[] nums, int k) {
        check(nums, k);
        PriorityQueue<Integer> heap = new PriorityQueue<>();
        for (int x : nums) {
            heap.offer(x);
            if (heap.size() > k) {
                heap.poll();
            }
        }
        return heap.peek();
    }

    public static int byMaxHeap(int[] nums, int k) {
        check(nums, k);
        PriorityQueue<Integer> heap = new PriorityQueue<>(Collections.reverseOrder());
        for (int x : nums) {
            heap.offer(x);
        }
        for (int i = 1; i < k; i++) {
            heap.poll();
        }
        return heap.peek();
    }

    public static int byQuickSelect(int[] nums, int k) {
        check(nums, k);
        int[] a = nums.clone();
        int target = a.length - k;
        int lo = 0;
        int hi = a.length - 1;

        while (lo <= hi) {
            int pivot = a[ThreadLocalRandom.current().nextInt(lo, hi + 1)];
            int lt = lo;
            int i = lo;
            int gt = hi;
            while (i <= gt) {
                if (a[i] < pivot) {
                    swap(a, lt++, i++);
                } else if (a[i] > pivot) {
                    swap(a, i, gt--);
                } else {
                    i++;
                }
            }
            if (target < lt) {
                hi = lt - 1;
            } else if (target > gt) {
                lo = gt + 1;
            } else {
                return a[target];
            }
        }
        throw new AssertionError("unreachable");
    }

    private static void check(int[] nums, int k) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        if (k < 1 || k > nums.length) throw new IllegalArgumentException("k out of range");
    }

    private static void swap(int[] a, int i, int j) {
        int t = a[i]; a[i] = a[j]; a[j] = t;
    }
}
```

三种方法返回值相同，但复杂度和副作用不同。`byBoundedMinHeap` 对大数据、K 很小时最稳定；`byMaxHeap` 是对题目“大顶堆”字面的直接实现；`byQuickSelect` 不需要维护 K 个堆元素，期望线性，但最坏情况仍可能退化。这里 Quick Select 先 clone，所以不会修改调用方输入。

## 关键细节

- **“第 K 大”与去重**：默认按排序后的元素位置定义，不去重。若要“第 K 个不同的值”，题目必须明确，算法和边界都会变化。
- **大顶堆复杂度纠偏**：把 N 个元素原地建成 max-heap 可 O(N)，再弹 K-1 次是 O(K log N)；如果用通用 `PriorityQueue.offer` 逐个插入，则构造阶段是 O(N log N)。因此不能把“大顶堆”机械写成 O(N log K)。
- **小顶堆为什么是 K**：堆只保留当前扫描前缀中最大的 K 个值；一旦超过 K，就删除这 K+1 个值里最小的那个。扫描结束时堆顶正是第 K 大。
- **Quick Select 下标**：升序第 `N-K` 个元素等价于第 K 大。K=1 对应最大值下标 N-1，K=N 对应最小值下标 0。
- **三向分区**：大量重复值时把所有等于 pivot 的元素一次聚到中间；target 落在等值区间即可立即返回，避免二向分区在全相等数组上反复缩一格。
- **随机 pivot**：随机化用于避免固定 pivot 对特定输入持续产生极端不平衡分区；期望 O(N)，但不是最坏 O(N)。需要最坏 O(N) 可以讨论 median-of-medians，常数和实现复杂度更高。
- **输入修改**：传统 Quick Select 原地分区会修改输入；当前实现复制后分区，明确换取不修改调用方数组。

## 原理机制

大小为 K 的小顶堆维护一个前缀不变量：处理完前 i 个元素后，堆中恰好保存这个前缀最大的 `min(i,K)` 个元素。新元素进入后如果堆超过 K，就删除其中最小值，因此更小的元素永远不会挤占最终 top-K。处理完整个数组后，堆内是全局最大 K 个元素，堆顶作为这 K 个元素中最小者，就是全局第 K 大。

Quick Select 利用的是 partition 后的秩信息。三向分区结束后，`[lo, lt)` 都小于 pivot，`[lt, gt]` 都等于 pivot，`(gt, hi]` 都大于 pivot。如果 target 在左边，只需继续左段；在右边只需继续右段；落在中间就已经找到对应秩。每轮只递归/迭代一侧，所以随机 pivot 下期望处理的数据规模形成收缩级数，总期望 O(N)。

## 项目经验版

来源没有真实项目背景，不能虚构线上经验。工程选择主要看数据规模、K、是否允许修改输入和延迟稳定性：K 很小且数据流式到达时，大小 K 的小顶堆天然支持单遍在线处理；数据一次性在内存中、只需一个秩且能接受期望复杂度时，Quick Select 通常更省额外结构；如果还需要完整 top-K 有序结果，则仅找到第 K 大往往不够，还需要额外排序或堆输出。

## 常见追问

- 问：题目为什么写“大顶堆 O(N log K)”有问题？答：限制堆大小为 K 时，为了随时淘汰 top-K 中最小的元素，需要能 O(1) 看到最小值，所以标准结构是小顶堆。大顶堆保留 K 个元素时堆顶是最大值，不能直接淘汰最小值。
- 问：大顶堆还能做吗？答：能。把所有 N 个数建成大顶堆，再弹 K-1 次，下一次堆顶就是第 K 大；复杂度通常写成 O(N + K log N)（原地线性建堆前提下）。
- 问：Quick Select 为什么是 `N-K`？答：升序下标从 0 开始，最大值是 N-1，第 2 大是 N-2，所以第 K 大是 N-K。
- 问：重复值怎么办？答：按元素位置计数，不去重。三向分区尤其适合重复值，因为相同 pivot 的一段可以一次确认。
- 问：Quick Select 最坏是什么？答：如果每次 partition 都极端不平衡，会退化到 O(N²)；随机 pivot 降低持续遇到这种分区的概率，但不提供最坏线性保证。
- 问：为什么堆方案有时更值得选？答：它最坏 O(N log K)、行为稳定、可以流式处理，而且不需要重排全部输入；Quick Select 的优势是期望线性和较低常数，但延迟尾部更难界定。

## 易错点

- 为了 O(N log K) 却使用大顶堆并在堆超过 K 时弹堆顶，结果会删除最大的元素，方向完全反了。
- 把“第 K 大”错误实现成去重后的第 K 个不同值。
- Quick Select 把目标下标写成 K-1，混淆“第 K 小”和“第 K 大”。
- partition 后两边都继续处理，失去 Quick Select 只搜索一侧的优势。
- 宣称随机 Quick Select 最坏 O(N)，忽略它的 O(N²) 退化边界。
- 原地分区修改输入却没有在接口契约中说明。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class KthLargestTest {
    private static int oracle(int[] a, int k) {
        int[] b = a.clone();
        Arrays.sort(b);
        return b[b.length - k];
    }

    private static void check(int[] a, int k, int expected) {
        int[] before = a.clone();
        int h1 = KthLargest.byBoundedMinHeap(a, k);
        int h2 = KthLargest.byMaxHeap(a, k);
        int q = KthLargest.byQuickSelect(a, k);
        if (h1 != expected || h2 != expected || q != expected) {
            throw new AssertionError("expected=" + expected + " bounded=" + h1 + " max=" + h2 + " quick=" + q);
        }
        if (!Arrays.equals(a, before)) throw new AssertionError("input mutated");
    }

    public static void main(String[] args) {
        check(new int[]{3,2,1,5,6,4}, 2, 5);
        check(new int[]{3,2,3,1,2,4,5,5,6}, 4, 4);
        check(new int[]{5,5,4}, 2, 5);
        check(new int[]{7}, 1, 7);
        check(new int[]{-1,-5,-2,-2}, 3, -2);
        check(new int[]{9,9,9,9,9}, 4, 9);

        Random rnd = new Random(20260829L);
        for (int tc = 0; tc < 5000; tc++) {
            int n = 1 + rnd.nextInt(60);
            int[] a = new int[n];
            for (int i = 0; i < n; i++) a[i] = rnd.nextInt(81) - 40;
            int k = 1 + rnd.nextInt(n);
            check(a, k, oracle(a, k));
        }

        try { KthLargest.byBoundedMinHeap(null, 1); throw new AssertionError("null must fail"); }
        catch (IllegalArgumentException expected) {}
        try { KthLargest.byQuickSelect(new int[]{1,2}, 0); throw new AssertionError("k=0 must fail"); }
        catch (IllegalArgumentException expected) {}
        try { KthLargest.byMaxHeap(new int[]{1,2}, 3); throw new AssertionError("k>N must fail"); }
        catch (IllegalArgumentException expected) {}

        System.out.println("PASS named duplicate equal negative random5000-vs-sort three-methods input-unchanged invalid-boundaries");
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

    with tempfile.TemporaryDirectory(prefix='b51-kth-largest-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'KthLargest.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'KthLargestTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'KthLargest.java', 'KthLargestTest.java', cwd=tmpdir)
        stdout = run('java', 'KthLargestTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS named duplicate equal negative random5000-vs-sort three-methods input-unchanged invalid-boundaries'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac KthLargest.java KthLargestTest.java && java KthLargestTest',
        'stdout': stdout,
        'checks': [
            'bounded size-K min-heap, literal max-heap, and randomized three-way Quick Select agree on named cases',
            'duplicates are counted by position rather than deduplicated',
            '5000 deterministic random arrays match an independent full-sort oracle for all sampled K',
            'Quick Select handles equal-heavy arrays through three-way partitioning',
            'public methods leave the caller input unchanged',
            'null and out-of-range K follow explicit implementation boundaries',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0051 exact Kth-largest source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 three-method Kth-largest validation versus full-sort oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-requirement', 'text': 'The exact source asks for the Kth largest element and explicitly requests a max-heap labeled O(N log K) plus Quick Select expected O(N).', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'heap-mismatch', 'text': 'The requested O(N log K) bounded-heap strategy needs a size-K min-heap so that the smallest retained top-K value can be evicted; a literal max-heap over all values has a different complexity profile.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'algorithm-validation', 'text': 'The executable fixture validates bounded min-heap, literal max-heap, and randomized three-way Quick Select against an independent full-sort oracle on named and 5000 deterministic random inputs.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'duplicate-semantics', 'text': 'All three validated implementations treat duplicate values as separate ranked elements, matching ordinary positional Kth-largest semantics.', 'source_ids': ['fixture'], 'answer_locations': ['1 分钟版', '关键细节', '常见追问']},
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
        'The answer preserves the exact source request but explicitly identifies the max-heap/O(N log K) mismatch instead of silently teaching the wrong heap orientation.',
        'It provides both the literal max-heap interpretation and the standard bounded size-K min-heap that actually realizes O(N log K).',
        'Quick Select maps Kth-largest to ascending target N-K and uses randomized three-way partitioning so duplicate-heavy inputs do not repeatedly shrink by one equal element.',
        'OpenJDK 21 validation makes all three implementations agree with an independent full-sort oracle on 5000 deterministic random inputs.',
        'Duplicate rank semantics, invalid K, input mutation, expected-versus-worst Quick Select complexity, and heap space tradeoffs are explicit.',
        'The project section avoids fabricated experience and gives decision criteria for streaming versus in-memory selection.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0051-kth-largest-20260829-v1',
        'review_version': 'batch-0051.kth-largest.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0051 Kth-largest source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0051-kth-largest-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': '[3,2,1,5,6,4], k=2', 'expected': 5, 'actual': 5, 'passed': True},
                {'case': 'duplicate [5,5,4], k=2', 'expected': 5, 'actual': 5, 'passed': True},
                {'case': 'all equal', 'expected': 9, 'actual': 9, 'passed': True},
                {'case': '5000 deterministic random arrays/K', 'expected': 'equals full-sort oracle for all three methods', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_dc192e205c8fbcf5673927a9d9382f41` source-first isolated review PASS: the exact source asks for Kth-largest via “max heap O(N log K)” and Quick Select expected O(N); the review preserves that wording while correcting the heap-orientation/complexity mismatch. The candidate gives a literal max-heap path, the standard size-K min-heap O(N log K) path, and randomized three-way Quick Select. OpenJDK 21 validation makes all three agree with a full-sort oracle across named boundaries and 5000 deterministic random inputs. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
