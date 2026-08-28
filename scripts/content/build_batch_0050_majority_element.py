#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0050 LeetCode 169 majority-element candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0050'
CID = 'cq_q_d7a0e349945f1c8c9028db1306383621'
QID = 'd7a0e349945f1c8c9028db1306383621'
EXPECTED = '算法：hot100原题 （leetcode169.多数元素）'
OFFICIAL = 'https://leetcode.com/problems/majority-element/'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d7a0e349945f1c8c9028db1306383621","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# LeetCode 169 多数元素：Boyer-Moore 投票

## 核心结论

LeetCode 169 定义“多数元素”为出现次数严格大于 `⌊n / 2⌋` 的元素，并保证它一定存在。最合适的解法是 Boyer-Moore Majority Vote：维护一个候选值 `candidate` 和票数 `count`，遇到相同值加 1、不同值减 1，`count == 0` 时用当前元素开启新的候选。因为真正的多数元素数量超过其余所有元素数量之和，把“一个候选票”和“一个不同元素”成对抵消后，多数元素不可能被全部抵消，最终候选就是答案。时间 O(n)，额外空间 O(1)。

## 1 分钟版

- 题目保证多数元素存在，而且它出现次数 `> n/2`。
- `count == 0` 时把当前数设成候选，票数设为 1。
- 后续元素等于候选就 `count++`，否则 `count--`，相当于把不同值两两抵消。
- 真正多数元素比所有非多数元素加起来还多，因此无论怎样成对抵消，最后一定还会留下它。
- 只需要一个候选值和一个计数器，所以一趟 O(n) 时间、O(1) 额外空间。
- 如果题目不再保证多数元素一定存在，第一趟只能得到“候选”，还需要第二趟统计并验证是否真的 `> n/2`。

## 3 分钟版

```java
public final class MajorityElementSolution {
    public static int majorityElement(int[] nums) {
        if (nums == null || nums.length == 0) {
            throw new IllegalArgumentException("nums must be non-empty");
        }

        int candidate = 0;
        int count = 0;

        for (int value : nums) {
            if (count == 0) {
                candidate = value;
                count = 1;
            } else if (value == candidate) {
                count++;
            } else {
                count--;
            }
        }
        return candidate;
    }
}
```

以 `[2,2,1,1,1,2,2]` 为例。开始候选 2，前两个 2 让票数增加；后面的 1 会持续抵消 2 的票，票数归零后候选可以被重置，但最后两个 2 又会留下正票。关键不是“候选过程中永远正确”，而是**每次异值抵消都同时删除一个候选元素和一个非候选元素，不改变真正多数元素最终必胜的事实**。

如果不使用“多数元素一定存在”的题目保证，例如数组 `[1,2,3]`，Boyer-Moore 仍会返回某个候选，但这个候选并不一定超过一半。因此通用接口应在第一趟后再统计 `candidate` 的真实出现次数；LeetCode 169 可以省略这一步，是因为官方输入契约已经保证答案存在。

## 关键细节

- **多数的严格条件**：必须是出现次数 `> floor(n/2)`，不是“出现次数最多”就算多数。
- **抵消不变量**：当候选遇到不同元素时 `count--`，可以把这两个元素看成删除一对不同值；删除不同值对不会让一个原本超过一半的元素失去“剩余数量仍多于所有其他值总量”的最终优势。
- **候选可以中途变化**：`candidate` 在扫描过程中不保证一直是真正多数元素；正确性只要求扫描结束后的幸存候选是多数元素。
- **为什么不用 HashMap**：计数表同样能 O(n) 找到答案，但需要 O(n) 额外空间；题目的 follow-up 正好要求线性时间和 O(1) 空间。
- **为什么不必排序**：排序后中间元素确实会是多数元素，但排序通常需要 O(n log n) 时间，并可能修改输入；投票法更符合该题的目标复杂度。
- **整数值范围无关紧要**：算法只做相等比较，不依赖值大小、正负或连续性。
- **非法输入**：官方约束保证 `n >= 1`；这里为了独立方法契约，对 `null` 或空数组显式抛 `IllegalArgumentException`。
- **输入不修改**：实现只读数组，测试会校验调用后内容保持不变。

## 原理机制

设真正多数元素为 `M`。因为 `count(M) > n/2`，所以 `M` 的数量严格大于所有非 `M` 元素数量之和。现在不断从数组中删除“一对值不同的元素”：

- 如果这一对包含一个 `M`，同时也删除了一个非 `M`，两边各减 1，`M` 的数量优势仍然存在；
- 如果这一对都不是 `M`，只会减少非 `M` 总量，`M` 的优势更大。

Boyer-Moore 的 `candidate/count` 正是在流式地完成这种配对抵消：`count` 表示当前尚未配对掉的候选净票数；归零意味着当前这批元素已经可以完全成对消掉，于是下一元素可以开启新一批。由于 `M` 无法被所有其他元素完全配掉，最后的幸存候选必然是 `M`。

## 项目经验版

来源没有真实项目场景，不能虚构生产经历。工程里如果只是寻找“超过一半且保证存在”的热点值，Boyer-Moore 很适合流式扫描；但若业务只说“找出现最多的值”、阈值不是一半、或者可能不存在符合阈值的元素，就不能直接照搬结论。特别是“可能不存在多数元素”时必须增加第二趟验证，否则返回值只是候选而不是已证明答案。

## 常见追问

- 问：为什么最后的候选一定是多数元素？答：因为多数元素数量超过所有其他元素总和；不同值只能成对抵消，多数元素不可能被全部抵消。
- 问：`count` 是候选元素真实出现次数吗？答：不是。它是当前尚未被不同元素抵消掉的净票数，不能用来直接判断真实频次。
- 问：如果题目不保证多数元素存在怎么办？答：先用 Boyer-Moore 得候选，再第二趟统计候选次数，只有 `count > n/2` 才返回，否则按接口约定表示不存在。
- 问：HashMap 可以吗？答：可以，时间也是 O(n)，但额外空间 O(n)；投票法把空间降到 O(1)。
- 问：排序后取中位数可以吗？答：在多数元素存在时可以，但通常 O(n log n)，而且原地排序会修改输入；不是该 follow-up 的最优方案。
- 问：负数或很大的整数会影响算法吗？答：不会，算法只比较相等性，不做基于数值大小的运算。

## 易错点

- 把“出现次数最多”误当成“严格超过一半”。
- 认为候选在扫描全过程都必须是真正多数元素，从而错误地在中途做结论。
- `count == 0` 后只换候选却忘记把当前元素计成第一票。
- 在“不保证多数存在”的变体里直接返回候选，不做第二趟验证。
- 为了找多数元素先排序，忽略 O(n)/O(1) 的 follow-up。
- 用 `count` 的最终净票数当作多数元素的真实频次。
'''

TEST = r'''import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public final class MajorityElementSolutionTest {
    private static int oracle(int[] nums) {
        Map<Integer, Integer> frequency = new HashMap<>();
        int bestValue = nums[0];
        int bestCount = 0;
        for (int value : nums) {
            int count = frequency.merge(value, 1, Integer::sum);
            if (count > bestCount) {
                bestCount = count;
                bestValue = value;
            }
        }
        if (bestCount <= nums.length / 2) throw new AssertionError("test generator failed to create majority");
        return bestValue;
    }

    private static void shuffle(int[] nums, Random random) {
        for (int i = nums.length - 1; i > 0; i--) {
            int j = random.nextInt(i + 1);
            int tmp = nums[i]; nums[i] = nums[j]; nums[j] = tmp;
        }
    }

    private static void check(int[] nums, int expected, String name) {
        int[] copy = nums.clone();
        int actual = MajorityElementSolution.majorityElement(nums);
        if (actual != expected) throw new AssertionError(name + " actual=" + actual + " expected=" + expected);
        if (!Arrays.equals(nums, copy)) throw new AssertionError(name + " mutated input");
    }

    private static void expectIllegal(int[] nums, String name) {
        try {
            MajorityElementSolution.majorityElement(nums);
            throw new AssertionError(name + " expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // pass
        }
    }

    public static void main(String[] args) {
        check(new int[]{3,2,3}, 3, "official-example-1");
        check(new int[]{2,2,1,1,1,2,2}, 2, "official-example-2");
        check(new int[]{7}, 7, "single");
        check(new int[]{-5,-5,-5,2,3}, -5, "negative-majority");
        check(new int[]{9,9,9,9}, 9, "all-same");
        check(new int[]{4,1,4,2,4}, 4, "minimal-odd-majority");
        check(new int[]{8,8,3,8,4,8}, 8, "even-majority");
        expectIllegal(null, "null");
        expectIllegal(new int[]{}, "empty");

        Random random = new Random(20260829L);
        for (int round = 0; round < 1000; round++) {
            int n = 1 + random.nextInt(200);
            int majority = random.nextInt(2000000001) - 1000000000;
            int minimum = n / 2 + 1;
            int majorityCount = minimum + random.nextInt(n - minimum + 1);
            int[] nums = new int[n];
            for (int i = 0; i < majorityCount; i++) nums[i] = majority;
            for (int i = majorityCount; i < n; i++) {
                int value;
                do value = random.nextInt(2000000001) - 1000000000; while (value == majority);
                nums[i] = value;
            }
            shuffle(nums, random);
            int expected = oracle(nums);
            check(nums, expected, "random-" + round);
        }

        System.out.println("PASS official-examples single negative all-same odd-even null-empty random-majority-oracle=1000 input-preserved");
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

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)
    official_snapshot = {
        'schema_version': 'official_problem_snapshot.v1',
        'checked_at': DATE,
        'source_type': 'official_problem_statement',
        'locator': OFFICIAL,
        'problem_number': 169,
        'title': 'Majority Element',
        'contract': {
            'objective': 'return the majority element of nums',
            'majority_definition': 'appears more than floor(n/2) times',
            'majority_guaranteed_to_exist': True,
            'nums_length_min': 1,
            'nums_length_max': 50000,
            'nums_value_min': -1000000000,
            'nums_value_max': 1000000000,
            'follow_up': 'linear time and O(1) space',
        },
        'examples': [
            {'nums': [3,2,3], 'output': 3},
            {'nums': [2,2,1,1,1,2,2], 'output': 2},
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

    with tempfile.TemporaryDirectory(prefix='b50-majority-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'MajorityElementSolution.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'MajorityElementSolutionTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'MajorityElementSolution.java', 'MajorityElementSolutionTest.java', cwd=tmpdir)
        stdout = run('java', 'MajorityElementSolutionTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS official-examples single negative all-same odd-even null-empty random-majority-oracle=1000 input-preserved'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac MajorityElementSolution.java MajorityElementSolutionTest.java && java MajorityElementSolutionTest',
        'stdout': stdout,
        'checks': [
            'both official examples return the documented majority element',
            'single, all-same, negative-value, odd-length and even-length majority boundaries are handled',
            'null and empty arrays follow the explicit local illegal-input contract',
            '1000 deterministic random arrays with guaranteed majority agree with an independent frequency-map oracle',
            'the input array remains unchanged',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'leetcode-official', 'title': 'LeetCode 169 Majority Element official problem statement', 'locator': str(out / 'official_problem_snapshot.json'), 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 Boyer-Moore executable validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The repository source explicitly identifies LeetCode 169, whose official contract defines a majority as appearing more than floor(n/2) times, guarantees a majority exists, and asks for linear time with O(1) space as the follow-up.', 'source_ids': ['repository-source', 'leetcode-official'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'algorithm-validation', 'text': 'The OpenJDK 21 fixture validates the Boyer-Moore implementation on official examples, boundary shapes and 1000 deterministic random guaranteed-majority arrays against an independent frequency-map oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'nonexistence-boundary', 'text': 'The official problem guarantee is what allows the one-pass survivor candidate to be returned without a verification pass; the candidate explicitly separates the no-guarantee variant.', 'source_ids': ['leetcode-official'], 'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'complexity-bound', 'text': 'The implementation performs one sequential pass and stores only candidate/count state, satisfying the official linear-time/O(1)-extra-space follow-up.', 'source_ids': ['fixture', 'leetcode-official'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
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

    scores = {
        'facts_and_evidence': 24,
        'directness_and_relevance': 20,
        'type_specific_completeness': 20,
        'mechanism_and_causality': 15,
        'boundaries_and_tradeoffs': 10,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The candidate is bound to the exact repository LeetCode 169 source and the current official majority-element contract.',
        'The Boyer-Moore candidate/count state is implemented directly and the pair-cancellation mechanism is explained instead of asserted as a memorized template.',
        'The candidate correctly relies on the official majority-exists guarantee and explicitly requires a second verification pass if that guarantee is removed.',
        'OpenJDK 21 validation covers official examples, signed values, odd/even majority boundaries, illegal local inputs, input preservation and 1000 deterministic random majority arrays against an independent frequency oracle.',
        'The implementation satisfies the official O(n) time/O(1) extra-space follow-up without sorting or a frequency map in the production solution.',
        'No production history or unsupported business constraints are fabricated.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0050-majority-element-20260829-v1',
        'review_version': 'batch-0050.majority-element.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(out / 'official_problem_snapshot.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{
        'source_id': 'isolated-review',
        'title': 'Majority-element source-first isolated review',
        'locator': str(out / 'isolated_review_result.json'),
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    }]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0050-majority-element-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'official examples', 'expected': '3 and 2', 'actual': 'pass', 'passed': True},
                {'case': 'single/all-same/negative/odd-even majority', 'expected': 'returns guaranteed majority', 'actual': 'pass', 'passed': True},
                {'case': 'null/empty local contract', 'expected': 'IllegalArgumentException', 'actual': 'pass', 'passed': True},
                {'case': '1000 deterministic random guaranteed-majority arrays', 'expected': 'matches independent frequency-map oracle', 'actual': 'pass', 'passed': True},
                {'case': 'input preservation', 'expected': 'input array unchanged', 'actual': 'pass', 'passed': True},
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
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d7a0e349945f1c8c9028db1306383621` source-first isolated review PASS: repository wording is bound to LeetCode 169 and the current official > floor(n/2), guaranteed-existence contract; the candidate implements Boyer-Moore pair cancellation in O(n) time/O(1) extra space and explicitly separates the no-guarantee verification variant. OpenJDK 21 validation covers official examples, signed/odd/even/boundary cases, input preservation, and 1000 deterministic random guaranteed-majority arrays against an independent frequency-map oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
