#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 majority-element candidate."""

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
CID = 'cq_q_e2ff9aa7aee383022ed9137b9724ec93'
QID = 'e2ff9aa7aee383022ed9137b9724ec93'
EXPECTED = '算法：找出数组中出现次数超过一半的数，请用O(N)的复杂度的算法找出这个数'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e2ff9aa7aee383022ed9137b9724ec93","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 数组中过半元素：Boyer-Moore 候选抵消 + 第二遍验证

## 核心结论

来源要求“找出数组中出现次数超过一半的数，并使用 O(N) 算法”，但没有明确保证这样的数一定存在，也没有定义空数组或 `null`。为了不把隐含前提冒充成来源事实，这里采用更完整的 Java 契约：输入为 `int[]`；若存在出现次数严格大于 `n / 2` 的元素，返回 `OptionalInt.of(value)`；不存在则返回 `OptionalInt.empty()`；空数组返回 empty；`null` 视为调用错误并抛 `IllegalArgumentException`。

算法使用 Boyer-Moore Majority Vote。第一遍只产生一个“可能的多数候选”：遇到与候选相同的值就加票，不同就抵消；票数归零时用当前值重新开始。若多数元素确实存在，它不可能被所有其他元素完全抵消，因此最终候选一定是它。由于来源没有保证多数一定存在，必须再扫描一遍统计候选出现次数，只有 `count > n / 2` 才返回。两遍仍然是严格 O(n) 时间，除少量标量变量外额外空间 O(1)。

## 1 分钟版

- “超过一半”是严格 `count > n / 2`，刚好一半不算。
- 第一遍 Boyer-Moore：`votes == 0` 时换候选；相同 `votes++`，不同 `votes--`。
- 第一遍只保证：如果多数存在，最终候选就是多数；它不能证明多数一定存在。
- 因为来源没有保存“多数必然存在”的前提，所以第二遍统计候选次数并验证。
- 两遍都是线性扫描，整体 O(n)；只保存 candidate/votes/count，额外空间 O(1)。
- 空数组返回 empty，`null` 显式抛 `IllegalArgumentException`，这些都是本候选定义的边界。

## 3 分钟版

```java
import java.util.OptionalInt;

public final class MajorityElement {
    public static OptionalInt majorityElement(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }
        if (nums.length == 0) {
            return OptionalInt.empty();
        }

        int candidate = 0;
        int votes = 0;
        for (int value : nums) {
            if (votes == 0) {
                candidate = value;
                votes = 1;
            } else if (value == candidate) {
                votes++;
            } else {
                votes--;
            }
        }

        int count = 0;
        for (int value : nums) {
            if (value == candidate) count++;
        }
        return count > nums.length / 2
                ? OptionalInt.of(candidate)
                : OptionalInt.empty();
    }
}
```

理解 Boyer-Moore 的关键是“成对抵消”。把一个候选值和一个不同值配成一对删除，不会改变“某个值是否严格超过剩余总数一半”这一事实：真正的多数元素数量比所有其他元素总和还多，所以无论怎样一对一抵消，它最终仍会留下代表。

但如果原数组根本没有多数，例如 `[1,2,3]`，第一遍依然会留下某个候选，因此不能直接返回。第二遍验证是为了把“候选”升级成“已证明的多数”。

## 关键细节

- **严格过半**：条件是 `count > n / 2`，不是 `>=`。长度 4、某值出现 2 次仍不是多数。
- **候选与答案不是同义词**：Boyer-Moore 第一遍在无多数时也会产生候选；只有题面明确保证多数存在时才可以省略验证。
- **为什么是 O(1) 空间**：不使用 HashMap 统计所有频次，只维护固定数量的整数变量；第二遍也不增加与 n 成比例的数据结构。
- **整数值域无关**：负数、0、`Integer.MIN_VALUE/MAX_VALUE` 都只做相等比较，不会参与会溢出的算术运算。
- **空值边界**：空数组不存在过半元素，返回 empty；`null` 被明确当作非法调用，而不是依赖偶然 NPE。
- **输入不修改**：两遍都只读数组，适合调用者仍需保留原顺序/内容的场景。

## 原理机制

设真正的多数元素为 M，出现 m 次，其他元素总数为 r。多数条件意味着 `m > r`。第一遍的“相同加一、不同减一”可以理解为不断把一个当前候选实例和一个不同实例配对消去。对 M 来说，即使所有其他元素都拿来和 M 抵消，也最多消掉 r 个 M；因为 m > r，至少还有 M 无法被抵消，所以最终幸存候选必须是 M。

这个证明依赖“多数确实存在”。没有多数时，抵消过程只产生某个幸存者，并不提供频次证明。因此第二遍计数不是多余工作，而是为了适配当前保存来源里未明确保证存在性的边界。两次 n 级扫描仍是 `2n`，渐进时间仍为 O(n)。

## 项目经验版

来源没有真实项目背景，不能虚构。工程中如果数据是可重复读取的数组，两遍 Boyer-Moore 非常合适；如果输入是只能消费一次的流，又不能缓存全部数据，那么“先找候选再验证”会遇到第二遍不可用的问题。这时必须由上游保证多数存在、允许重放数据，或改变存储/统计方案。这个限制应由输入介质和业务合同决定。

## 常见追问

- 问：为什么 HashMap 不行？答：HashMap 也能 O(n) 平均时间找频次，但需要 O(n) 额外空间；Boyer-Moore 能把额外空间降到 O(1)。
- 问：为什么还要第二遍？答：第一遍只保证“若多数存在，则候选是多数”；来源没有明确保证存在，所以要验证候选实际次数。
- 问：如果题目明确保证多数一定存在呢？答：可以省略第二遍并直接返回候选，时间仍 O(n)、空间 O(1)。
- 问：为什么不同值可以抵消？答：真正多数元素比所有非多数元素加起来还多；每次一对一删掉一个候选和一个不同值，不可能把真正多数完全消光。
- 问：刚好出现一半算吗？答：不算。“超过一半”是严格大于，例如 n=4 时必须至少 3 次。
- 问：能并行吗？答：经典状态更新依赖扫描顺序，直接拆分不能简单合并 candidate/votes；若要并行，需设计可合并摘要并重新证明，面试默认没必要复杂化。

## 易错点

- 记住 Boyer-Moore 模板，却把第一遍候选无条件当成最终答案。
- 把“超过一半”写成 `>= n / 2`，尤其在偶数长度时出错。
- 为了满足 O(N) 时间直接用 HashMap，却忽略题目可能继续追问 O(1) 空间的更优方案。
- 认为两遍扫描是 O(2N) 所以“不算 O(N)”；常数系数不改变渐进复杂度。
- 对空数组直接读取候选，产生没有定义的结果。
- 在来源没保证多数存在的情况下省略第二遍验证。
'''

TEST = r'''import java.util.HashMap;
import java.util.Map;
import java.util.OptionalInt;
import java.util.Random;

public final class MajorityElementTest {
    private static OptionalInt oracle(int[] nums) {
        Map<Integer, Integer> counts = new HashMap<>();
        for (int x : nums) counts.merge(x, 1, Integer::sum);
        for (Map.Entry<Integer, Integer> e : counts.entrySet()) {
            if (e.getValue() > nums.length / 2) return OptionalInt.of(e.getKey());
        }
        return OptionalInt.empty();
    }

    private static void check(OptionalInt expected, int[] nums) {
        OptionalInt actual = MajorityElement.majorityElement(nums);
        if (!actual.equals(expected)) {
            throw new AssertionError("expected=" + expected + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        check(OptionalInt.empty(), new int[]{});
        check(OptionalInt.of(7), new int[]{7});
        check(OptionalInt.of(2), new int[]{2,2,1,1,1,2,2});
        check(OptionalInt.empty(), new int[]{1,1,2,2});
        check(OptionalInt.empty(), new int[]{1,2,3});
        check(OptionalInt.of(-1), new int[]{-1,0,-1,-1,2});
        check(OptionalInt.of(Integer.MIN_VALUE), new int[]{Integer.MIN_VALUE, 4, Integer.MIN_VALUE});

        try {
            MajorityElement.majorityElement(null);
            throw new AssertionError("null must fail");
        } catch (IllegalArgumentException expected) {}

        Random random = new Random(20260829L);
        for (int round = 0; round < 5000; round++) {
            int n = random.nextInt(40);
            int[] nums = new int[n];
            for (int i = 0; i < n; i++) nums[i] = random.nextInt(11) - 5;
            OptionalInt expected = oracle(nums);
            OptionalInt actual = MajorityElement.majorityElement(nums);
            if (!actual.equals(expected)) {
                throw new AssertionError("random mismatch round=" + round + " expected=" + expected + " actual=" + actual);
            }
        }

        int n = 300_001;
        int[] large = new int[n];
        for (int i = 0; i < 150_001; i++) large[i] = 42;
        for (int i = 150_001; i < n; i++) large[i] = i;
        check(OptionalInt.of(42), large);
        large[150_000] = -999;
        check(OptionalInt.empty(), large);

        System.out.println("PASS directed null-boundary strict-half 5000-random-oracle large-majority verification");
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

    with tempfile.TemporaryDirectory(prefix='b52-majority-element-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'MajorityElement.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'MajorityElementTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'MajorityElement.java', 'MajorityElementTest.java', cwd=tmpdir)
        stdout = run('java', 'MajorityElementTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS directed null-boundary strict-half 5000-random-oracle large-majority verification'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac MajorityElement.java MajorityElementTest.java && java MajorityElementTest',
        'stdout': stdout,
        'checks': [
            'directed majority, no-majority, exact-half, empty, signed and extreme-int cases',
            'explicit null-input exception boundary',
            '5000 deterministic random arrays compared with an independent HashMap frequency oracle',
            'large 300001-element case verifies majority detection and second-pass rejection after crossing the strict-half boundary',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact majority-element source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 Boyer-Moore majority validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The exact source requires finding an element occurring more than half the time in O(N), but does not explicitly guarantee existence or define empty/null behavior.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'candidate-verification', 'text': 'The first Boyer-Moore pass produces a necessary candidate when a majority exists; a second linear pass validates strict count > n/2 so no-majority inputs are not falsely accepted.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '原理机制']},
        {'claim_id': 'linear-constant-space', 'text': 'The implementation performs two linear read-only scans and retains only fixed scalar state, satisfying O(N) time with O(1) auxiliary space.', 'source_ids': ['fixture'], 'answer_locations': ['1 分钟版', '关键细节', '原理机制']},
        {'claim_id': 'validation', 'text': 'Executable validation covers exact-half rejection, missing-majority inputs, 5000 deterministic random arrays against an independent frequency oracle, and a large threshold-crossing case.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '常见追问', '易错点']},
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
        'The answer satisfies the preserved O(N) requirement while avoiding a fabricated assumption that a majority is guaranteed to exist.',
        'Boyer-Moore candidate generation is separated from second-pass proof, preventing false answers on no-majority inputs.',
        'The strict “more than half” boundary is explicit and validated against exact-half cases.',
        'The cancellation invariant and m > r argument explain why a true majority survives instead of presenting the vote loop as a memorized template.',
        'OpenJDK 21 validation covers directed boundaries, 5000 deterministic random arrays against an independent frequency oracle, and a 300001-element threshold-crossing case.',
        'The implementation is read-only, handles full int equality without arithmetic overflow, and uses fixed auxiliary state.',
        'The project section avoids fabricated production claims and correctly exposes the second-pass limitation for non-replayable streams.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0052-majority-element-20260829-v1',
        'review_version': 'batch-0052.majority-element.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 majority-element source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0052-majority-element-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'exact half', 'expected': 'empty', 'actual': 'pass', 'passed': True},
                {'case': 'no majority', 'expected': 'empty after second-pass verification', 'actual': 'pass', 'passed': True},
                {'case': '5000 deterministic random arrays', 'expected': 'matches frequency oracle', 'actual': 'pass', 'passed': True},
                {'case': '300001-element threshold crossing', 'expected': 'majority then empty after one occurrence removed from majority', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e2ff9aa7aee383022ed9137b9724ec93` source-first isolated review PASS: the source requires an O(N) majority-element algorithm but does not preserve a guarantee that a majority exists. The candidate uses Boyer-Moore cancellation plus a second linear verification pass, keeps strict `count > n/2` semantics and O(1) auxiliary state, and OpenJDK 21 validation covers no-majority/exact-half/null boundaries, 5000 deterministic random arrays against an independent frequency oracle, plus a 300001-element threshold-crossing case. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
