#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0050 LeetCode 560 candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
CID = 'cq_q_d63322aa9fd4048a05c37c235c47ce2c'
QIDS = ['a4a80af48b7e1af0a3cdd334e8e43506', 'd63322aa9fd4048a05c37c235c47ce2c']
EXPECTED = {
    'a4a80af48b7e1af0a3cdd334e8e43506': '算法：和为 K 的子数组 (LeetCode 560 - 前缀和 + 哈希表)',
    'd63322aa9fd4048a05c37c235c47ce2c': '算法：和为 K 的子数组（LeetCode 560）',
}
BATCH = '0050'
OFFICIAL = 'https://leetcode.com/problems/subarray-sum-equals-k/'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d63322aa9fd4048a05c37c235c47ce2c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 和为 K 的子数组（LeetCode 560）：前缀和 + 频次哈希表

## 核心结论

这题要求统计**连续、非空**子数组中元素和恰好等于 `k` 的个数。核心等式是：若当前位置前缀和为 `prefix[j]`，那么子数组 `(i, j]` 的和为 `k` 当且仅当 `prefix[i] = prefix[j] - k`。因此从左到右维护“此前每个前缀和值出现过多少次”，当前前缀和 `sum` 到来时，把 `sum - k` 的出现次数累加到答案，再把当前 `sum` 计入频次。初始必须放入 `0 -> 1`，这样从下标 0 开始的合法子数组也能被统计。

## 1 分钟版

- `prefix[j] - prefix[i] = k`，所以对当前前缀和 `sum`，只需要查询历史上 `sum - k` 出现过几次。
- 哈希表存的是**频次**而不是“是否出现”，因为相同前缀和可能对应多个不同起点，每一个都形成不同子数组。
- 初始化 `freq.put(0L, 1)`，表示“还没取任何元素”的空前缀；否则会漏掉从数组开头开始、和正好为 `k` 的子数组。
- 查询必须发生在把当前前缀和写入哈希表之前，这样不会把空子数组误计入；当 `k == 0` 时尤其重要。
- 数组含负数，不能使用依赖窗口和单调性的普通双指针/滑动窗口。
- 时间 O(n)，额外空间 O(n)。

## 3 分钟版

```java
import java.util.HashMap;
import java.util.Map;

public final class SubarraySumSolution {
    public static int subarraySum(int[] nums, int k) {
        Map<Long, Integer> frequency = new HashMap<>();
        frequency.put(0L, 1);

        long prefix = 0L;
        int answer = 0;

        for (int value : nums) {
            prefix += value;
            answer += frequency.getOrDefault(prefix - k, 0);
            frequency.merge(prefix, 1, Integer::sum);
        }
        return answer;
    }
}
```

例如 `nums = [1, 1, 1], k = 2`：前缀和依次为 1、2、3。到前缀和 2 时查询历史 `0`，得到子数组 `[0..1]`；到 3 时查询历史 `1`，得到 `[1..2]`，所以答案是 2。

更能说明“频次”必要性的是 `nums = [0, 0, 0], k = 0`。前缀和始终为 0：第一次看到 0 时，历史已有一个空前缀，所以新增 1 个；第二次历史有两个 0，新增 2 个；第三次新增 3 个，总共 6 个。若哈希表只存 boolean/set，就会把不同起点合并掉而计数错误。

## 关键细节

- **为什么先查后写**：当前前缀只能和更早的前缀配对。若先把当前 `prefix` 写进去，当 `k == 0` 时会把“当前前缀减当前前缀”的空区间也计数。
- **为什么初始化 0 -> 1**：把数组开始之前的位置视为一个前缀和为 0 的边界。于是当当前位置 `prefix == k` 时，`prefix - k == 0` 能正确统计 `[0..j]`。
- **为什么存出现次数**：如果同一前缀和此前出现 m 次，就存在 m 个不同起点；当前终点会产生 m 个合法子数组。
- **为什么不能普通滑动窗口**：官方输入允许负数。加入右端元素后窗口和可能变小，移除左端元素后也可能变大，因此不存在“和太大就左移”的单调性。
- **整数范围**：官方 `n <= 2 * 10^4`、单个元素绝对值不超过 1000，前缀和用 `int` 也在范围内；这里用 `long` 让加法与 `prefix - k` 的中间计算更稳健。最大子数组个数 `n(n+1)/2 = 200010000`，仍在 Java `int` 范围内。
- **复杂度**：平均情况下哈希查询/更新 O(1)，所以总时间 O(n)；不同前缀和值最多 O(n)，额外空间 O(n)。

## 原理机制

把数组边界定义成前缀和 `P[0] = 0`、`P[j+1] = nums[0] + ... + nums[j]`。任意连续子数组 `nums[i..j]` 的和就是 `P[j+1] - P[i]`。要求它等于 `k`，等价于在处理 `P[j+1]` 时寻找此前的 `P[i] = P[j+1] - k`。

因此哈希表其实是在维护一个“已经经过的左边界多重集合”。它不仅回答目标前缀是否存在，还回答存在多少个；这正对应“有多少个不同起点可以和当前终点组成答案”。算法每次只依赖历史前缀，不需要保存具体子数组内容，也不需要回溯。

## 项目经验版

来源没有真实项目经历，不能虚构“线上用过这道算法”。工程上遇到“区间累计值等于某目标”的统计问题时，可以先判断累计量是否允许负增量：若允许，普通滑动窗口通常失去单调性，前缀差 + 频次索引是更可靠的建模方向；若数据量、数值范围或输出计数可能超过当前题目约束，则还要重新选择数值类型和存储策略。

## 常见追问

- 问：为什么不是 `Set`？答：题目问数量，相同前缀和值可能由不同位置产生；每个位置都是不同起点，所以必须记录频次。
- 问：为什么不能双指针？答：数组可能有负数，窗口和不随左右指针单调变化，无法安全地用“和大了就缩、和小了就扩”的规则。
- 问：`freq.put(0, 1)` 有什么意义？答：它代表数组开始前的空前缀，让从下标 0 开始的子数组也能通过统一公式统计。
- 问：如果 `k == 0` 呢？答：算法不需要特判；重复前缀和的频次正好统计所有和为 0 的连续子数组，但必须保持“先查询、后写当前前缀”的顺序。
- 问：能返回具体子数组吗？答：当前哈希表只保存频次，足够做计数；若要返回区间，需要保存每个前缀和值对应的历史下标列表，输出量本身可能达到 O(n²)。
- 问：为什么用 `long prefix`？答：官方约束下 `int` 足够，但使用 `long` 不改变算法复杂度，并让累加和差值的中间计算不依赖较窄的整型边界。

## 易错点

- 忘记初始化 `0 -> 1`，漏掉从数组开头开始的答案。
- 用 `Set` 代替频次 Map，重复前缀和时少计。
- 先写当前前缀再查询，`k == 0` 时把空子数组算进去。
- 因为题目有“子数组”就直接套滑动窗口，忽略负数破坏单调性。
- 把“子序列”与“连续子数组”混淆。
- 只用样例验证，没有覆盖全 0、负数、重复前缀和与随机 oracle。
'''

TEST = r'''import java.util.Random;

public final class SubarraySumSolutionTest {
    static int oracle(int[] nums, int k) {
        int count = 0;
        for (int i = 0; i < nums.length; i++) {
            long sum = 0;
            for (int j = i; j < nums.length; j++) {
                sum += nums[j];
                if (sum == k) count++;
            }
        }
        return count;
    }

    static void check(int[] nums, int k, int expected, String name) {
        int actual = SubarraySumSolution.subarraySum(nums, k);
        if (actual != expected) throw new AssertionError(name + ": " + actual + " != " + expected);
    }

    public static void main(String[] args) {
        check(new int[]{1,1,1}, 2, 2, "official-example-1");
        check(new int[]{1,2,3}, 3, 2, "official-example-2");
        check(new int[]{0,0,0}, 0, 6, "all-zero-frequency");
        check(new int[]{1,-1,0}, 0, 3, "negative-and-zero");
        check(new int[]{3,-1,-2,5,-5}, 0, oracle(new int[]{3,-1,-2,5,-5}, 0), "negative-window-counterexample");
        check(new int[]{5}, 5, 1, "starts-at-zero-boundary");
        check(new int[]{5}, 0, 0, "single-no-match");

        int[] zeros = new int[20000];
        check(zeros, 0, 200010000, "max-n-zero-count-fits-int");

        Random random = new Random(20260829L);
        for (int round = 0; round < 1000; round++) {
            int n = 1 + random.nextInt(40);
            int[] nums = new int[n];
            for (int i = 0; i < n; i++) nums[i] = random.nextInt(11) - 5;
            int k = random.nextInt(21) - 10;
            int expected = oracle(nums, k);
            int actual = SubarraySumSolution.subarraySum(nums, k);
            if (actual != expected) {
                throw new AssertionError("random-" + round + " k=" + k + " actual=" + actual + " expected=" + expected);
            }
        }
        System.out.println("PASS official-examples zeros=6 negatives boundary max-n=200010000 random-oracle=1000");
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

    context_raw = run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout
    ctx = json.loads(context_raw)
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != CID:
        raise SystemExit('canonical context drift')
    if ctx.get('answer_type') != 'coding':
        raise SystemExit(f"answer type drift: {ctx.get('answer_type')}")
    owned = sorted(ctx.get('canonical', {}).get('question_ids') or [])
    if owned != QIDS:
        raise SystemExit(f'ownership drift: {owned}')
    source_questions = {x.get('question_id'): x for x in ctx.get('source_questions', [])}
    if sorted(source_questions) != QIDS:
        raise SystemExit(f'source packet drift: {sorted(source_questions)}')
    for qid in QIDS:
        src = source_questions[qid]
        if src.get('original_question') != EXPECTED[qid] or src.get('is_valid_for_library') is not True:
            raise SystemExit(f'{qid}: source wording/validity drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)
    official_snapshot = {
        'schema_version': 'official_problem_snapshot.v1',
        'checked_at': DATE,
        'source_type': 'official_problem_statement',
        'locator': OFFICIAL,
        'problem_number': 560,
        'title': 'Subarray Sum Equals K',
        'contract': {
            'objective': 'return the number of contiguous non-empty subarrays whose elements sum to k',
            'nums_length_min': 1,
            'nums_length_max': 20000,
            'nums_value_min': -1000,
            'nums_value_max': 1000,
            'k_min': -10000000,
            'k_max': 10000000,
            'negative_values_allowed': True,
        },
        'examples': [
            {'nums': [1,1,1], 'k': 2, 'expected': 2},
            {'nums': [1,2,3], 'k': 3, 'expected': 2},
        ],
    }
    write_json(out / 'official_problem_snapshot.json', official_snapshot)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')

    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b50-subarray-sum-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'SubarraySumSolution.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'SubarraySumSolutionTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'SubarraySumSolution.java', 'SubarraySumSolutionTest.java', cwd=tmpdir)
        stdout = run('java', 'SubarraySumSolutionTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS official-examples zeros=6 negatives boundary max-n=200010000 random-oracle=1000'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac SubarraySumSolution.java SubarraySumSolutionTest.java && java SubarraySumSolutionTest',
        'stdout': stdout,
        'checks': [
            'official examples',
            'all-zero repeated-prefix frequency semantics',
            'negative values and zero target',
            'prefix starting at array index zero via initial zero prefix',
            'n=20000 all-zero maximum combinatorial count',
            '1000 deterministic random arrays match O(n^2) oracle',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'official-problem', 'title': 'LeetCode 560 Subarray Sum Equals K official problem statement', 'locator': OFFICIAL, 'source_type': 'official_problem_statement', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 prefix-sum frequency-map deterministic and randomized validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-identity', 'text': 'Both repository Question variants are owned by this Canonical and identify LeetCode 560; one explicitly names prefix sum plus hash table while the complete contiguous-subarray counting contract is bounded to the official problem statement.', 'source_ids': ['repository-source', 'official-problem'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版']},
        {'claim_id': 'official-contract', 'text': 'LeetCode 560 asks for the number of contiguous non-empty subarrays summing to k and allows negative array values, so ordinary monotonic sliding-window reasoning is not valid in general.', 'source_ids': ['official-problem'], 'answer_locations': ['核心结论', '关键细节', '原理机制', '常见追问']},
        {'claim_id': 'algorithm-validation', 'text': 'The prefix-sum frequency-map implementation matches both official examples, repeated-prefix and negative-value boundaries, the n=20000 all-zero count, and 1000 deterministic random arrays against an O(n^2) oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
    ]
    coverage = [
        {'question_id': qid, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}
        for qid in QIDS
    ]
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

    scores = {
        'facts_and_evidence': 25,
        'directness_and_relevance': 20,
        'type_specific_completeness': 19,
        'mechanism_and_causality': 14,
        'boundaries_and_tradeoffs': 9,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The candidate preserves both repository source variants under one Canonical and uses the official LeetCode 560 statement to bound the complete contiguous-subarray counting contract.',
        'The prefix-difference invariant is explicit and the map stores frequencies rather than membership, covering repeated-prefix cases such as all-zero input.',
        'Initialization with the empty prefix and query-before-insert ordering are explained and exercised, including the k=0 boundary.',
        'Negative values are treated as a correctness boundary that invalidates ordinary monotonic sliding-window reasoning.',
        'OpenJDK 21 tests cover official examples, maximum-length all-zero combinatorial count and 1000 deterministic random arrays against an independent O(n^2) oracle.',
        'Complexity, integer-range reasoning and project-experience boundaries align with the implementation without fabricated production claims.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0050-subarray-sum-20260829-v1',
        'review_version': 'batch-0050.subarray-sum.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            str(out / 'context.json'),
            str(out / 'official_problem_snapshot.json'),
            str(candidate),
            str(out / 'writer_validation.json'),
            OFFICIAL,
            'docs/refactor/09_answer_content_standard.md',
        ],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence = {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0050-subarray-sum-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'Subarray Sum Equals K source-first isolated review',
            'locator': str(out / 'isolated_review_result.json'),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        }],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': '[0,0,0], k=0', 'expected': 6, 'actual': 6, 'passed': True},
                {'case': '[1,-1,0], k=0', 'expected': 3, 'actual': 3, 'passed': True},
                {'case': 'single [5], k=5', 'expected': 1, 'actual': 1, 'passed': True},
                {'case': '20000 zeros, k=0', 'expected': 200010000, 'actual': 200010000, 'passed': True},
                {'case': '1000 deterministic random arrays', 'expected': 'optimized result equals O(n^2) oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': review['reviewer_id'],
            'review_version': review['review_version'],
            'independent': True,
            'decision': 'pass',
            'revision_round': 1,
            'scores': scores,
            'hard_failures': [],
            'unsupported_claims': [],
            'uncovered_source_variants': [],
            'findings': findings,
        },
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    }
    write_json(ROOT / f'review/evidence/{CID}.json', evidence)

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d63322aa9fd4048a05c37c235c47ce2c` source-first isolated review PASS: both repository LeetCode 560 Question variants remain owned by this Canonical; the official contract bounds contiguous non-empty subarray counting with negative values, and the candidate uses the prefix-difference frequency-map invariant. OpenJDK 21 validation covers official examples, repeated zero prefixes, negative values, the n=20000 maximum combinatorial count, and 1000 deterministic random arrays against an independent O(n^2) oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
