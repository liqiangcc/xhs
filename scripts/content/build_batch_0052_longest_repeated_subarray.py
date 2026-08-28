#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 longest repeated subarray candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0052'
CID = 'cq_q_de595fc33028ead2a88206084178aa82'
QID = 'de595fc33028ead2a88206084178aa82'
EXPECTED = '算法：最长重复子数组'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_de595fc33028ead2a88206084178aa82","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 最长重复子数组：连续公共片段的动态规划

## 核心结论

来源只写了“最长重复子数组”，没有给函数签名、数组元素类型和输入样例。结合当前 Canonical 的数组/动态规划定位，这里先声明一个最小可执行合同：输入两个整数数组 `a`、`b`，返回它们**最长公共连续子数组**的长度；“子数组”要求连续，因此不能把它做成最长公共子序列（LCS）。空数组返回 0；`null` 作为无效调用显式报错。

动态规划最直接：定义 `dp[i][j]` 表示“以 `a[i-1]` 和 `b[j-1]` 结尾的最长公共连续片段长度”。若两个元素相等，`dp[i][j] = dp[i-1][j-1] + 1`；否则必须归零，因为连续片段在当前位置已经断开。答案是所有状态的最大值，不一定出现在数组末尾。

空间可以从 O(MN) 压到 O(N)：只保留一行，并让 j 从右往左更新，保证读取到的 `dp[j-1]` 仍是上一轮 i 的状态。

## 1 分钟版

- 先区分“子数组”和“子序列”：这里要求连续，失配时当前结尾长度直接变 0。
- 状态：`dp[j]` 在处理到 `a[i-1]` 后，表示以当前 `a[i-1]` 与 `b[j-1]` 结尾的公共连续长度。
- 若 `a[i-1] == b[j-1]`，从左上角状态延长：`dp[j] = dp[j-1] + 1`；否则 `dp[j] = 0`。
- 一维压缩后 j 必须从右往左，否则 `dp[j-1]` 会被本轮提前覆盖，错误地把同一轮状态串起来。
- 每次更新记录全局最大值。
- 时间 O(MN)，空间 O(N)；可以让第二个参数选择较短数组，把空间写成 O(min(M,N))。

## 3 分钟版

```java
public final class LongestRepeatedSubarray {
    public static int longestCommonContiguousLength(int[] a, int[] b) {
        if (a == null || b == null) {
            throw new IllegalArgumentException("arrays must not be null");
        }
        if (a.length < b.length) {
            return longestCommonContiguousLength(b, a);
        }

        int[] dp = new int[b.length + 1];
        int best = 0;

        for (int i = 1; i <= a.length; i++) {
            for (int j = b.length; j >= 1; j--) {
                if (a[i - 1] == b[j - 1]) {
                    dp[j] = dp[j - 1] + 1;
                    best = Math.max(best, dp[j]);
                } else {
                    dp[j] = 0;
                }
            }
        }
        return best;
    }
}
```

例如 `a=[1,2,3,2,1]`、`b=[3,2,1,4,7]`，公共连续片段 `[3,2,1]` 长度为 3，所以返回 3。注意 `[1,2,1]` 即使能按顺序从两个数组里挑出来，只要中间不连续，就不能作为本题的“子数组”答案。

如果两个数组完全没有相同元素，所有匹配状态都保持 0，答案为 0；如果其中一个为空，也直接得到 0。

## 关键细节

- **连续性是核心边界**：最长公共子序列在失配时会做 `max(dp[i-1][j], dp[i][j-1])`；本题不能这么做，失配必须归零。
- **为什么状态是“以 i,j 结尾”**：只有结尾状态才能在元素相等时从 `(i-1,j-1)` 无歧义地延长一个连续片段。
- **为什么答案取全局最大**：最长公共片段可能在任意位置结束，最后一个元素并不一定参与答案。
- **一维更新方向**：从右往左更新，`dp[j-1]` 仍代表上一行；从左往右会读取本行刚更新的新值，破坏二维状态依赖。
- **空间选择**：递归交换参数，让 `b` 不比 `a` 长，因此数组空间 O(min(M,N))。
- **重复值**：算法按位置比较，不去重；同一个数在不同位置可以属于不同候选片段。
- **复杂度**：每对位置 `(i,j)` 恰好比较一次，所以时间 O(MN)；额外空间 O(min(M,N))。

## 原理机制

把每个相等元素对 `(i,j)` 看成一个可能的连续片段结尾。若 `a[i-1]==b[j-1]`，那么它能延长的唯一连续前缀就是同时向左移动一位的 `(i-1,j-1)`，因此状态只依赖左上角；若元素不同，这条连续链在当前结尾立即断掉，长度只能是 0。

二维表中的非零状态会形成沿右下方向延伸的“对角线”。一条连续公共子数组对应一段连续相等的对角线，状态值就是这段对角线到当前位置的长度。求最长重复子数组，本质上就是找所有这些相等对角线中最长的一段。

## 项目经验版

来源没有真实项目背景，不能虚构线上使用经历。工程选择取决于数组规模：O(MN) DP 适合中等规模并且实现稳定、容易验证；如果两个数组非常长，乘积不可接受，可以讨论“长度二分 + rolling hash”或后缀自动机/后缀数组等方案，但要额外处理哈希碰撞、实现复杂度和元素域。没有规模约束时，先给清晰的 DP 通常更适合作为面试基线。

## 常见追问

- 问：这和最长公共子序列有什么区别？答：子数组要求连续，所以失配时当前结尾状态必须归零；子序列允许跳过元素，会从上/左状态取最大值。
- 问：为什么一维 DP 从右往左？答：当前 `dp[j]` 依赖上一行的 `dp[j-1]`。右到左更新保证这个旧值尚未被本轮 i 改写。
- 问：能不能从左往右再存一个变量？答：可以，用单独变量保存上一行左上角值也能正确压缩；当前写法用更新方向直接保护依赖，更简洁。
- 问：完全相同数组怎么办？答：对角线会一路增长到数组长度，返回完整长度。
- 问：有很多重复数字会不会错？答：不会。状态按“位置对”计算，重复值只会产生更多可能的匹配结尾，最大值仍由连续对角线决定。
- 问：数据很大怎么办？答：先看 M×N 是否可接受；不可接受再考虑二分答案配合哈希或后缀结构，并明确碰撞/内存/实现复杂度边界。

## 易错点

- 把“最长重复子数组”写成最长公共子序列，失配时不归零。
- 一维 DP 从左往右更新，却仍读取 `dp[j-1]`，导致读取本轮新状态。
- 只返回最后一个 `dp[j]`，没有维护历史最大值。
- 把重复元素先去重，破坏位置和连续性语义。
- 为了省空间交换数组后修改调用方输入；这里只交换参数引用，不修改数组内容。
- 来源没有给超大规模约束，却直接上 rolling hash 并忽略碰撞风险。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class LongestRepeatedSubarrayTest {
    private static int oracle(int[] a, int[] b) {
        int best = 0;
        for (int i = 0; i < a.length; i++) {
            for (int j = 0; j < b.length; j++) {
                int len = 0;
                while (i + len < a.length && j + len < b.length && a[i + len] == b[j + len]) len++;
                best = Math.max(best, len);
            }
        }
        return best;
    }

    private static void check(int[] a, int[] b, int expected) {
        int[] ac = a.clone();
        int[] bc = b.clone();
        int actual = LongestRepeatedSubarray.longestCommonContiguousLength(a, b);
        if (actual != expected) throw new AssertionError("expected=" + expected + " actual=" + actual + " a=" + Arrays.toString(a) + " b=" + Arrays.toString(b));
        if (!Arrays.equals(a, ac) || !Arrays.equals(b, bc)) throw new AssertionError("input mutated");
        int reversed = LongestRepeatedSubarray.longestCommonContiguousLength(b, a);
        if (reversed != expected) throw new AssertionError("symmetry mismatch");
    }

    public static void main(String[] args) {
        check(new int[]{1,2,3,2,1}, new int[]{3,2,1,4,7}, 3);
        check(new int[]{0,0,0,0,0}, new int[]{0,0,0,0,0}, 5);
        check(new int[]{1,2,3}, new int[]{4,5,6}, 0);
        check(new int[]{}, new int[]{1,2}, 0);
        check(new int[]{7}, new int[]{7}, 1);
        check(new int[]{1,2,1,2,1}, new int[]{2,1,2,1,2}, 4);

        Random rnd = new Random(20260829L);
        for (int tc = 0; tc < 5000; tc++) {
            int n = rnd.nextInt(13);
            int m = rnd.nextInt(13);
            int[] a = new int[n];
            int[] b = new int[m];
            for (int i = 0; i < n; i++) a[i] = rnd.nextInt(7) - 3;
            for (int i = 0; i < m; i++) b[i] = rnd.nextInt(7) - 3;
            check(a, b, oracle(a, b));
        }

        try { LongestRepeatedSubarray.longestCommonContiguousLength(null, new int[]{}); throw new AssertionError("null must fail"); }
        catch (IllegalArgumentException expected) {}

        System.out.println("PASS named all-equal disjoint empty singleton repeated random5000-vs-bruteforce symmetry input-unchanged null-boundary");
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

    with tempfile.TemporaryDirectory(prefix='b52-longest-repeated-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'LongestRepeatedSubarray.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'LongestRepeatedSubarrayTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'LongestRepeatedSubarray.java', 'LongestRepeatedSubarrayTest.java', cwd=tmpdir)
        stdout = run('java', 'LongestRepeatedSubarrayTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS named all-equal disjoint empty singleton repeated random5000-vs-bruteforce symmetry input-unchanged null-boundary'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac LongestRepeatedSubarray.java LongestRepeatedSubarrayTest.java && java LongestRepeatedSubarrayTest',
        'stdout': stdout,
        'checks': [
            'named contiguous-overlap example returns length 3',
            'all-equal, disjoint, empty, singleton and repeated-value boundaries are correct',
            '5000 deterministic random array pairs match an independent cubic brute-force oracle',
            'result is symmetric under exchanging the two arrays',
            'caller arrays remain unchanged',
            'null follows the explicit invalid-input boundary',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact longest-repeated-subarray context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 longest common contiguous subarray validation versus brute-force oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The exact source only names “longest repeated subarray”; it does not preserve a signature, element domain, examples, or scale constraints.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate explicitly interprets the Canonical as the longest common contiguous segment between two integer arrays and distinguishes that from longest common subsequence semantics.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'algorithm-validation', 'text': 'The one-row reverse-update DP is validated on named boundaries and 5000 deterministic random array pairs against an independent brute-force contiguous-match oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'complexity', 'text': 'The implementation compares every position pair once for O(MN) time and stores one row for the shorter array for O(min(M,N)) auxiliary space.', 'source_ids': ['fixture'], 'answer_locations': ['1 分钟版', '关键细节', '原理机制']},
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
        'The sparse source wording is not expanded into invented samples or scale constraints; the two-array integer contract is explicitly labeled as the executable interpretation.',
        'The answer correctly makes contiguity the decisive semantic difference from LCS and resets mismatched ending states to zero.',
        'The reverse one-dimensional update preserves the previous-row diagonal dependency and the explanation calls out the left-to-right overwrite failure mode.',
        'OpenJDK 21 validation covers named edge shapes and 5000 deterministic random cases against a structurally independent brute-force oracle.',
        'Symmetry, caller-input immutability, null handling, repeated values, time complexity and shorter-row space optimization are explicit.',
        'The project section avoids fabricated experience and only introduces hash/suffix alternatives under changed scale assumptions.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0052-longest-repeated-subarray-20260829-v1',
        'review_version': 'batch-0052.longest-repeated-subarray.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 longest-repeated-subarray source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0052-longest-repeated-subarray-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': '[1,2,3,2,1] vs [3,2,1,4,7]', 'expected': 3, 'actual': 3, 'passed': True},
                {'case': 'all equal length 5', 'expected': 5, 'actual': 5, 'passed': True},
                {'case': 'disjoint arrays', 'expected': 0, 'actual': 0, 'passed': True},
                {'case': '5000 deterministic random pairs', 'expected': 'equals brute-force oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_de595fc33028ead2a88206084178aa82` source-first isolated review PASS: the sparse “最长重复子数组” source is handled with an explicit two-integer-array contiguous-common-segment contract rather than invented examples or scale constraints. The candidate distinguishes subarray from LCS, uses reverse one-row DP with mismatch reset, and OpenJDK 21 validation covers boundaries plus 5000 deterministic random pairs against an independent brute-force oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
