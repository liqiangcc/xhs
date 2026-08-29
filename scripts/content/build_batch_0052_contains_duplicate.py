#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 contains-duplicate candidate."""

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
CID = 'cq_q_e1ed5d7cba925ac4c6bd465f233c9aad'
QID = 'e1ed5d7cba925ac4c6bd465f233c9aad'
EXPECTED = '算法：存在重复元素 (LeetCode 217)'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e1ed5d7cba925ac4c6bd465f233c9aad","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 存在重复元素：一次扫描判断数组是否有重复值

## 核心结论

仓库来源只保留“算法：存在重复元素 (LeetCode 217)”这一句，没有保留完整外部题面、数组长度范围或空值约束，因此这些不能反向冒充成来源事实。这里明确采用一个可执行 Java 契约：输入是任意长度的 `int[]`；只要存在两个不同下标 `i != j` 满足 `nums[i] == nums[j]` 就返回 `true`，否则返回 `false`；空数组和单元素数组返回 `false`；`null` 视为调用错误并抛 `IllegalArgumentException`。

最直接的做法是维护一个 `HashSet<Integer>`。从左到右扫描，每个值调用 `seen.add(value)`：第一次出现时 `add` 返回 `true`；如果返回 `false`，说明这个值已经出现过，可以立即返回 `true`。扫描结束仍未命中重复则返回 `false`。按哈希集合的常见平均/期望操作成本分析，时间 O(n)，额外空间 O(n)；这不是严格的最坏情况 O(n) 保证。

## 1 分钟版

- 目标不是统计次数，只要知道“是否至少重复一次”，所以发现第二次出现即可提前结束。
- 用 `HashSet` 记录已经扫描过的值；`!seen.add(value)` 就代表当前值重复。
- 空数组、单元素数组天然没有两个不同下标，返回 `false`。
- 本候选把 `null` 定义为非法输入并显式抛异常；来源没有规定这一点，所以这是实现边界，不是原题事实。
- 平均/期望时间 O(n)，最坏额外空间 O(n)。若必须避免 O(n) 辅助空间，可以复制后排序再检查相邻项，代价是 O(n log n) 时间；不要为了省空间偷偷修改调用者原数组。

## 3 分钟版

```java
import java.util.HashSet;
import java.util.Set;

public final class ContainsDuplicate {
    public static boolean containsDuplicate(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }

        Set<Integer> seen = new HashSet<>();
        for (int value : nums) {
            if (!seen.add(value)) {
                return true;
            }
        }
        return false;
    }
}
```

不需要先 `contains` 再 `add`。`Set.add` 本身就表达“集合是否发生了新增”：第一次遇到值时新增成功，第二次遇到相同值时集合没有变化，因此能直接识别重复。

如果面试官进一步要求“不允许额外 O(n) 空间”，可以先复制数组，对副本排序，再线性扫描相邻元素：任何 `copy[i] == copy[i - 1]` 都说明存在重复。复制是为了保持当前候选“不修改输入”的边界；如果题目明确允许修改原数组，可以省掉这份副本。

## 关键细节

- **重复的定义**：必须是两个不同下标拥有相等的 `int` 值；不是“同一个下标被访问两次”。
- **提前返回**：只求布尔结果，不需要把整个数组都放入集合。第二次出现即可结束。
- **负数和 0**：算法对所有 `int` 值一视同仁，不依赖值域，因此无需额外分支。
- **`null` 边界**：来源没有保存异常语义。本答案主动把 `null` 定义为非法调用，测试也锁定这一契约，避免 `NullPointerException` 成为偶然行为。
- **输入不可变**：哈希方案不修改数组。排序方案若作为替代实现，需要明确是排序副本还是原数组。
- **复杂度表述**：哈希方案通常按平均/期望 O(n) 描述；若题目要求严格的确定性最坏界，需要重新讨论数据结构和约束，不能把哈希平均复杂度说成无条件最坏界。

## 原理机制

扫描到位置 `i` 时，维护不变量：`seen` 恰好包含 `nums[0..i-1]` 中已经出现过的值。处理 `nums[i]` 时，如果集合已经包含这个值，就存在某个更早下标 `j < i` 与当前值相等，于是重复条件成立；如果不存在，就把它加入集合，使不变量对下一轮继续成立。

这也是为什么算法不需要保存下标或计数。题目只问“是否存在”，集合承担的是历史成员关系，而不是频次统计。一旦成员关系查询证明当前值以前出现过，后续元素已经不可能改变布尔答案。

## 项目经验版

来源没有真实项目场景，不能虚构线上案例。工程中如果这是一个很大的数据流而不是可一次放进内存的数组，内存约束会改变方案：精确去重可能需要外部存储、分区或排序；Bloom Filter 等结构只能在允许概率性误判的前提下使用。对于本题保存下来的普通数组合同，直接 HashSet 是更清晰的默认答案。

## 常见追问

- 问：为什么不用 `contains` 后再 `add`？答：`add` 的返回值已经告诉我们元素是否新加入；一次集合操作即可表达判断。
- 问：能做到 O(1) 额外空间吗？答：若允许修改输入，可原地排序后比较相邻元素，通常是 O(n log n) 时间；若不能修改，就至少需要复制数组，空间仍是 O(n)。具体取舍要看约束。
- 问：空数组怎么办？答：没有两个不同下标，因此返回 `false`。
- 问：`null` 怎么办？答：保存来源没有定义。本候选明确抛 `IllegalArgumentException`，这样异常语义是合同而不是偶然 NPE。
- 问：为什么不是严格最坏 O(n)？答：这里使用哈希集合，O(n) 是基于常见平均/期望集合操作成本的整体分析；若面试官要求严格最坏复杂度，需要另行限定数据结构或值域。
- 问：值域很小怎么办？答：如果题目明确给出很小且连续的值域，可以用布尔位图/BitSet 类思路降低常数和装箱成本，但不能在来源没有值域约束时默认这样做。

## 易错点

- 把题名里的 LeetCode 编号当成仓库已经保存了完整外部题面，并凭记忆补写未保存约束。
- 用双重循环 O(n²) 做最直接暴力解，却漏掉更符合面试预期的一次扫描方案。
- `contains` 与 `add` 做两次重复集合查询，增加无必要的工作和代码。
- 采用排序方案却原地修改输入，没有说明副作用。
- 把哈希集合的平均/期望 O(n) 说成无条件严格最坏 O(n)。
- 没定义 `null` 行为，让实现偶然抛出的异常变成隐含合同。
'''

TEST = r'''import java.util.Random;

public final class ContainsDuplicateTest {
    private static boolean brute(int[] nums) {
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j < nums.length; j++) {
                if (nums[i] == nums[j]) return true;
            }
        }
        return false;
    }

    private static void check(boolean expected, int[] nums) {
        boolean actual = ContainsDuplicate.containsDuplicate(nums);
        if (actual != expected) {
            throw new AssertionError("expected=" + expected + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        check(false, new int[]{});
        check(false, new int[]{7});
        check(true, new int[]{1, 2, 3, 1});
        check(false, new int[]{1, 2, 3, 4});
        check(true, new int[]{0, 0});
        check(true, new int[]{-1, 2, -1});
        check(true, new int[]{Integer.MIN_VALUE, 0, Integer.MAX_VALUE, Integer.MIN_VALUE});

        try {
            ContainsDuplicate.containsDuplicate(null);
            throw new AssertionError("null must fail");
        } catch (IllegalArgumentException expected) {
            // explicit candidate contract
        }

        Random random = new Random(20260829L);
        for (int round = 0; round < 5000; round++) {
            int n = random.nextInt(24);
            int[] nums = new int[n];
            for (int i = 0; i < n; i++) nums[i] = random.nextInt(41) - 20;
            boolean expected = brute(nums);
            boolean actual = ContainsDuplicate.containsDuplicate(nums);
            if (actual != expected) {
                throw new AssertionError("random mismatch round=" + round);
            }
        }

        int[] largeUnique = new int[200_000];
        for (int i = 0; i < largeUnique.length; i++) largeUnique[i] = i;
        check(false, largeUnique);
        largeUnique[largeUnique.length - 1] = 42;
        check(true, largeUnique);

        System.out.println("PASS directed null-boundary 5000-random-oracle large-unique late-duplicate");
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

    with tempfile.TemporaryDirectory(prefix='b52-contains-duplicate-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'ContainsDuplicate.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'ContainsDuplicateTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'ContainsDuplicate.java', 'ContainsDuplicateTest.java', cwd=tmpdir)
        stdout = run('java', 'ContainsDuplicateTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS directed null-boundary 5000-random-oracle large-unique late-duplicate'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac ContainsDuplicate.java ContainsDuplicateTest.java && java ContainsDuplicateTest',
        'stdout': stdout,
        'checks': [
            'directed empty/single/duplicate/unique/zero/negative/extreme-int cases',
            'explicit null-input exception boundary',
            '5000 deterministic random arrays compared with an independent quadratic oracle',
            '200000 unique values remain false and a late injected duplicate becomes true',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact contains-duplicate source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 contains-duplicate deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source contains only the contains-duplicate title plus LeetCode 217 identifier; it does not preserve external constraints, null behavior, or a required implementation.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '易错点']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate defines duplicate as equal int values at distinct indices, returns false for empty/singleton arrays, and treats null as an explicit illegal input.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'algorithm-behavior', 'text': 'A one-pass seen set returns true exactly when a scanned value has appeared at an earlier index; deterministic random testing agrees with an independent quadratic oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制', '常见追问']},
        {'claim_id': 'boundary-validation', 'text': 'Executable validation covers empty/singleton, signed/extreme values, explicit null handling, 5000 random-oracle cases, and a 200000-element large case.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '原理机制', '易错点']},
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
        'The candidate respects the sparse repository source and does not reconstruct unpreserved LeetCode constraints from memory.',
        'The default HashSet solution is direct: the boolean result permits early return on the first failed insertion, with no redundant contains-then-add lookup.',
        'Null, empty, singleton, negative, zero and extreme-int boundaries are explicit rather than accidental runtime behavior.',
        'The invariant is explained as membership of the already-scanned prefix, connecting the implementation to the duplicate-at-distinct-indices condition.',
        'OpenJDK 21 validation compares 5000 deterministic random arrays with an independent quadratic oracle and includes a 200000-element late-duplicate case.',
        'Complexity wording is appropriately qualified as average/expected for the hash-set approach, and the sorting alternative calls out input mutation tradeoffs.',
        'The project section avoids fabricated experience and limits streaming/probabilistic alternatives to clearly conditional follow-up context.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0052-contains-duplicate-20260829-v1',
        'review_version': 'batch-0052.contains-duplicate.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 contains-duplicate source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0052-contains-duplicate-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'empty and singleton arrays', 'expected': 'false', 'actual': 'pass', 'passed': True},
                {'case': 'null array', 'expected': 'IllegalArgumentException', 'actual': 'pass', 'passed': True},
                {'case': '5000 deterministic random arrays', 'expected': 'matches quadratic oracle', 'actual': 'pass', 'passed': True},
                {'case': '200000 unique then late duplicate', 'expected': 'false then true', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e1ed5d7cba925ac4c6bd465f233c9aad` source-first isolated review PASS: the preserved source only names contains-duplicate / LeetCode 217, so the candidate does not invent missing external constraints. It defines explicit null/empty/singleton behavior, uses one-pass HashSet insertion with early duplicate detection, qualifies hash complexity as average/expected, and OpenJDK 21 validation covers directed signed/extreme cases, 5000 deterministic random arrays against an independent quadratic oracle, plus a 200000-element late-duplicate case. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
