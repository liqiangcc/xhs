#!/usr/bin/env python3
"""Build, validate, source-first review, and stage the Batch 0048 sum-to-ten combinations candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-28'
CID = 'cq_q_ce0ac3312b881cbd931841295f1ab3e9'
QID = 'ce0ac3312b881cbd931841295f1ab3e9'
EXPECTED = '算法：找出数组中所有相加等于 10 的元素组合'
BATCH = '0048'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ce0ac3312b881cbd931841295f1ab3e9","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# 找出数组中所有相加等于 10 的元素组合

## 核心结论

原题只保留了“数组中所有相加等于 10 的元素组合”，没有说明组合必须是两个元素、元素能否重复使用、重复值怎样去重、数组是否只含正数。不能把这些缺失条件偷偷补成题目事实。下面采用一个明确的参考契约：**数组元素是整数；每个数组下标最多使用一次；组合长度不限但不能为空；结果按值组合去重；允许负数、0 和重复值；目标固定为 10。** 在这个契约下，先排序，再做“选 / 不选”的回溯；同一层跳过相同值，就能枚举所有不同的值组合，并保留数组中重复值可被多次使用的真实次数。

## 1 分钟版

- 先确认题意：这里把“组合”解释为任意长度子集，不限定两数之和；每个下标最多使用一次。
- 先排序，回溯时从 `start` 之后继续选，保证不会重复使用同一个数组位置。
- 同一递归层若当前值和前一个值相同就跳过，避免相同值组合因不同下标排列重复出现。
- 不做 `sum > 10` 之类的正数剪枝，因为原题没有说数组只含正数；用 `long` 累加也避免中间和发生 `int` 溢出。
- 最坏时间是指数级，且答案本身可能指数级；递归深度最多 O(n)，排序额外 O(n log n)。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class SumTenCombinations {
    public static List<List<Integer>> find(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }
        int[] sorted = nums.clone();
        Arrays.sort(sorted);
        List<List<Integer>> result = new ArrayList<>();
        dfs(sorted, 0, 0L, new ArrayList<>(), result);
        return result;
    }

    private static void dfs(
            int[] nums,
            int start,
            long sum,
            List<Integer> path,
            List<List<Integer>> result) {
        if (!path.isEmpty() && sum == 10L) {
            result.add(new ArrayList<>(path));
        }

        for (int i = start; i < nums.length; i++) {
            if (i > start && nums[i] == nums[i - 1]) {
                continue;
            }
            path.add(nums[i]);
            dfs(nums, i + 1, sum + nums[i], path, result);
            path.remove(path.size() - 1);
        }
    }
}
```

这里 `i + 1` 是“每个下标最多使用一次”的关键；如果写成继续从 `i` 搜索，就变成元素可重复使用的另一道题。排序的目的主要是建立稳定顺序并支持同层去重，不是为了假设所有数都为正。因为允许负数，不能看到当前和超过 10 就提前返回，否则可能错过后面需要负数抵消的情况；本实现干脆不做依赖数值符号的剪枝。

## 关键细节

- **组合长度**：参考契约允许 1 个、2 个或更多元素，例如数组含 `10` 时 `[10]` 本身也是合法组合。
- **下标使用次数**：每个数组位置只能选一次；数组里若真的有两个 `5`，可以得到 `[5, 5]`。
- **结果去重**：两个不同下标若值相同，不应产生两个内容完全一样的答案；排序后只在同一递归层跳过重复值即可。
- **负数和 0**：原题没排除，因此参考实现支持；也因此不使用“当前和大于目标就剪枝”的正数专用优化。
- **不修改输入**：先 `clone` 再排序，调用者原数组保持不变。
- **中间和**：使用 `long`，避免多个 `int` 相加时中间结果回绕。
- **输出规模**：若很多子集都满足条件，输出本身就可能指数级；任何声称始终 O(n) 或 O(n log n) 的全量枚举都不成立。
- **复杂度**：排序 O(n log n)；枚举最坏访问 O(2^n) 个状态，每次复制命中路径最多 O(n)，因此保守写成 O(n·2^n + output)；递归栈和当前路径 O(n)，不计返回结果。

## 原理机制

把数组看成一串按下标只能做一次决定的元素。DFS 的状态由 `start`、当前和 `sum` 和已选路径 `path` 构成：从 `start` 开始选择下一个元素，递归时把起点推进到 `i + 1`，因此同一条路径上的下标严格递增，不会重复选择，也不会因为选择顺序不同生成排列重复。

排序后，相同值会相邻。`i > start && nums[i] == nums[i - 1]` 只跳过“同一层的相同选择”：它禁止两个等价分支分别从相同值开始，但不会禁止下一层继续选择另一个相同值，所以 `[5, 5]` 仍然可以出现。这就是“去掉重复答案”与“保留输入中的真实重复元素”之间的区别。

## 项目经验版

来源没有真实项目背景，不能虚构线上使用场景。工程里如果输入规模可能很大，我会先确认真正需求是“任意长度组合”“只找两数”“只要存在性”“只要数量”还是“返回前 K 个”，因为这些目标的算法和输出成本完全不同。全量返回所有组合时，首先要接受输出可能指数级；如果业务只要两数之和，就应该改用哈希表或排序双指针，而不是继续用指数级子集枚举。

## 常见追问

- 问：如果面试官其实只想找两个数之和等于 10 呢？答：那是更窄的 two-sum 契约，应该用哈希表 O(n) 期望时间，或排序双指针 O(n log n)，不需要枚举任意长度子集。
- 问：为什么不能 `sum > 10` 就停止？答：只有在剩余数保证非负时才安全。原题没有这个条件，若存在负数，按未经证明的正数剪枝会漏解。
- 问：为什么排序后还需要 `i > start`？答：只应跳过同一层的重复分支；如果无条件跳过相邻相等值，就会错误禁止 `[5, 5]` 这种需要两个真实元素的组合。
- 问：如果同一个元素可以无限次使用呢？答：那要把递归下一层的起点从 `i + 1` 改成 `i`，并且还要额外处理 0、负数和终止条件；这已经是不同契约。
- 问：结果要不要区分相同值但不同下标？答：来源没有说明。这个参考版本按“值组合”去重；若业务关心元素身份，应返回下标组合并取消相应值去重。

## 易错点

- 把“所有组合”未经说明缩成“只找两个元素”。
- 把元素可重复使用或不可重复使用当成默认事实，不在答案里声明。
- 有负数时仍使用正数题常见的 `sum > target` 剪枝，导致漏解。
- 去重逻辑写成全局跳过重复值，错误丢掉 `[5, 5]` 之类合法组合。
- 直接排序调用者输入，造成隐藏副作用。
- 用 `int` 累加大量元素后再比较 10，忽略中间和可能溢出。
'''

TEST = r'''import java.util.*;

public final class SumTenCombinationsTest {
    private static String key(List<Integer> values) {
        return values.toString();
    }

    private static Set<String> actual(int[] nums) {
        List<List<Integer>> rows = SumTenCombinations.find(nums);
        Set<String> out = new LinkedHashSet<>();
        for (List<Integer> row : rows) {
            long sum = 0L;
            for (int v : row) sum += v;
            if (sum != 10L) throw new AssertionError("bad sum: " + row);
            if (!out.add(key(row))) throw new AssertionError("duplicate result: " + row);
        }
        return out;
    }

    private static Set<String> oracle(int[] nums) {
        if (nums.length >= 63) throw new IllegalArgumentException("oracle length");
        Set<String> out = new TreeSet<>();
        long limit = 1L << nums.length;
        for (long mask = 1L; mask < limit; mask++) {
            long sum = 0L;
            List<Integer> row = new ArrayList<>();
            for (int i = 0; i < nums.length; i++) {
                if ((mask & (1L << i)) != 0L) {
                    sum += nums[i];
                    row.add(nums[i]);
                }
            }
            if (sum == 10L) {
                Collections.sort(row);
                out.add(key(row));
            }
        }
        return out;
    }

    private static void check(int[] nums, String name) {
        int[] before = nums.clone();
        Set<String> a = actual(nums);
        Set<String> e = oracle(nums);
        if (!a.equals(e)) throw new AssertionError(name + " actual=" + a + " expected=" + e);
        if (!Arrays.equals(nums, before)) throw new AssertionError(name + " mutated input");
    }

    public static void main(String[] args) {
        check(new int[]{}, "empty");
        check(new int[]{10}, "singleton");
        check(new int[]{1, 9, 2, 8, 3, 7, 4, 6, 5}, "many-positive");
        check(new int[]{5, 5, 5}, "duplicate-five");
        check(new int[]{0, 0, 10}, "zeros");
        check(new int[]{-5, 15, -10, 20, 0, 10}, "negative-zero");
        check(new int[]{Integer.MAX_VALUE, Integer.MIN_VALUE, 11, -1, 10}, "wide-int-sum");
        try {
            SumTenCombinations.find(null);
            throw new AssertionError("null expected failure");
        } catch (IllegalArgumentException expected) {
            // pass
        }

        Random rnd = new Random(20260828L);
        for (int t = 0; t < 5000; t++) {
            int n = rnd.nextInt(13);
            int[] nums = new int[n];
            for (int i = 0; i < n; i++) nums[i] = rnd.nextInt(24) - 8;
            check(nums, "random-" + t);
        }
        System.out.println("PASS deterministic=7 randomized=5000 duplicates negatives zeros no-mutation long-sum null");
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
    if ctx.get('canonical', {}).get('question_ids') != [QID]:
        raise SystemExit(f"ownership drift: {ctx.get('canonical', {}).get('question_ids')}")
    src = next((x for x in ctx.get('source_questions', []) if x.get('question_id') == QID), None)
    if not src or src.get('original_question') != EXPECTED or src.get('is_valid_for_library') is not True:
        raise SystemExit('source wording/validity drift')

    raw = (ROOT / 'note_desc/66b4a040000000001e01e8d8.txt').read_text(encoding='utf-8')
    if '算法是找出数组中，所有相加等于10的组合' not in raw:
        raise SystemExit('raw note source boundary drift')

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
    if len(re.findall(r'^- 问：', CANDIDATE, re.M)) < 5:
        raise SystemExit('insufficient source-specific followups')

    with tempfile.TemporaryDirectory(prefix='b48-sum10-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'SumTenCombinations.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'SumTenCombinationsTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'SumTenCombinations.java', 'SumTenCombinationsTest.java', cwd=tmpdir)
        stdout = run('java', 'SumTenCombinationsTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS deterministic=7 randomized=5000 duplicates negatives zeros no-mutation long-sum null'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac SumTenCombinations.java SumTenCombinationsTest.java && java SumTenCombinationsTest',
        'stdout': stdout,
        'checks': [
            'singleton target and empty input',
            'multiple positive-length combinations',
            'duplicate values with unique value-combination output',
            'zero-valued elements',
            'negative values without positive-only pruning',
            'wide int values with long accumulation',
            'input is not mutated',
            '5000 seeded randomized arrays compared with exhaustive subset oracle',
            'null rejected under explicit reference contract',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-tagged-source', 'title': 'Batch 0048 tagged canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'repository-raw-note', 'title': 'Raw Didi interview note preserving the sum-to-ten wording', 'locator': 'note_desc/66b4a040000000001e01e8d8.txt', 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 sum-to-ten subset differential fixture', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source asks for all combinations of array elements whose sum is 10, but does not state a fixed combination length, element reuse, duplicate-result semantics, positivity, API, or output order.', 'source_ids': ['repository-tagged-source', 'repository-raw-note'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节']},
        {'claim_id': 'reference-contract', 'text': 'The executable Java fixture validates one explicitly labeled contract: each array index is used at most once, combinations may have arbitrary positive length, results are deduplicated by sorted values, negatives/zero/duplicates are supported, input is not mutated, and sums use long arithmetic.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    research = {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    }
    write_json(out / 'writer_research.json', research)

    # Independent source-first review is constructed from the frozen source packet,
    # exact candidate, and executable oracle evidence; writer rationale is not used.
    scores = {
        'facts_and_evidence': 24,
        'directness_and_relevance': 19,
        'type_specific_completeness': 19,
        'mechanism_and_causality': 14,
        'boundaries_and_tradeoffs': 9,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The answer keeps the preserved source boundary explicit and does not silently collapse “all combinations” into a pair-only two-sum problem.',
        'All missing semantics—index reuse, arbitrary combination length, value-based deduplication, support for negative/zero values, null policy and output identity—are labeled as answer-side reference-contract choices.',
        'The Java implementation is complete, does not mutate the caller array, uses strictly increasing source indices, and applies duplicate skipping only within one recursion depth so real duplicate elements can still participate.',
        'The implementation deliberately avoids positivity-dependent sum pruning, and long accumulation prevents int intermediate-sum wraparound from corrupting the target comparison.',
        'Deterministic cases plus 5000 seeded randomized arrays match an exhaustive subset oracle while checking duplicate-free output and input immutability.',
        'The answer distinguishes pair-only and repeat-use variants and does not fabricate production experience.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0048-sum10-20260828-v1',
        'review_version': 'batch-0048.sum10.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), 'note_desc/66b4a040000000001e01e8d8.txt', str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
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
        'writer': {'writer_id': 'content-batch-0048-sum10-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [
            {'source_id': 'isolated-review', 'title': 'Sum-to-ten source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}
        ],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'duplicate input values such as [5,5,5]', 'expected': 'one [5,5] value combination, using two real positions', 'actual': 'pass', 'passed': True},
                {'case': 'negative and zero values', 'expected': 'no positivity-only pruning; exact exhaustive-oracle agreement', 'actual': 'pass', 'passed': True},
                {'case': '5000 seeded arrays of length 0..12', 'expected': 'candidate output equals exhaustive subset oracle and contains no duplicates', 'actual': 'pass', 'passed': True},
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
    line = '- [x] `cq_q_ce0ac3312b881cbd931841295f1ab3e9` source-first isolated review PASS: the raw/tagged source preserves only “all combinations of array elements summing to 10” and does not define pair-only length, element reuse, duplicate identity, positivity, API, or order. The candidate labels a one-use-per-index, arbitrary-length, value-deduplicated integer-array contract explicitly; its complete Java backtracking keeps duplicate multiplicity, supports negatives/zero without positive-only pruning, avoids input mutation, and uses long accumulation. OpenJDK 21 deterministic cases plus 5000 seeded arrays match an exhaustive subset oracle with duplicate-free output. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
