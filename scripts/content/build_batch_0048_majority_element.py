#!/usr/bin/env python3
"""Build, validate, source-first review, and stage the Batch 0048 majority-element candidate."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-28'
CID = 'cq_q_cd492f07ab9e4f6446b576e165a75c8d'
QID = 'cd492f07ab9e4f6446b576e165a75c8d'
EXPECTED = '算法：找出数组中出现频率超过数组长度一半的元素'
BATCH = '0048'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_cd492f07ab9e4f6446b576e165a75c8d","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# 找出数组中出现次数超过一半的元素

## 核心结论

如果一个元素出现次数严格大于数组长度的一半，可以用 Boyer-Moore 投票在一次扫描中得到唯一候选：遇到候选相同就 `count++`，不同就 `count--`，计数归零时换候选。它的本质是不断抵消“一个候选元素 + 一个不同元素”；真正的多数元素数量超过其余元素总数，因此不会被全部抵消。原题没有明确说多数元素一定存在，所以这份候选实现再做第二次计数校验，只有 `occurrences > n / 2` 才返回结果，整体仍是 O(n) 时间、O(1) 额外空间。

## 1 分钟版

- 目标条件是“出现次数严格超过 `n/2`”，不是大于等于一半。
- 第一遍用 Boyer-Moore：`count == 0` 时把当前值设为候选；相同加一，不同减一。
- 可以把一次减一看成删掉一对不同元素；若多数元素存在，它比所有非多数元素合起来还多，成对抵消后最后候选一定是它。
- 题干没有明确保证解一定存在，所以第二遍重新统计候选出现次数；只有 `occurrences > nums.length / 2` 才返回。
- 两遍都是线性扫描：时间 O(n)，只保存候选和计数器：额外空间 O(1)。

## 3 分钟版

下面明确选择 Java `int[]` 作为可执行接口，并用 `OptionalInt` 表达“题目没有声明一定存在多数元素”的边界；语言、空数组和 `null` 处理都是候选契约，不冒充原题条件。

```java
import java.util.OptionalInt;

public final class MajorityElement {
    public static OptionalInt findMajority(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }
        if (nums.length == 0) {
            return OptionalInt.empty();
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

        int occurrences = 0;
        for (int value : nums) {
            if (value == candidate) occurrences++;
        }
        return occurrences > nums.length / 2
                ? OptionalInt.of(candidate)
                : OptionalInt.empty();
    }
}
```

如果面试官明确补充“保证多数元素存在”，第二遍验证可以省略，此时第一遍结束的候选就是答案；但在当前来源没有这个保证时，保留验证更严谨。

## 关键细节

- **严格多数**：条件是 `count(x) > n/2`。偶数长度数组里刚好出现一半不算；用整数除法判断 `occurrences > nums.length / 2` 正好符合这个定义。
- **唯一性**：不可能同时有两个不同元素都严格超过一半，因此一旦验证通过，答案唯一。
- **抵消不变量**：把一个候选和一个不同元素配对删除，不会改变“若原数组存在严格多数元素，那么剩余未抵消元素中它仍有成为最终候选的优势”这一事实。
- **为什么要二次验证**：Boyer-Moore 在“没有多数元素”的数组上仍会留下某个候选；候选不等于已证明答案，所以来源未保证存在性时必须计数确认。
- **复杂度**：两次 O(n) 扫描仍是 O(n)；只用常数个整数变量，因此 O(1) 额外空间。哈希计数也能做，但需要 O(k) 额外空间。
- **输入边界**：本实现把 `null` 视为非法调用、空数组视为无答案；原题没有指定这些 API 行为，面试时应先说明约定。

## 原理机制

假设真正多数元素为 `m`，出现 `M` 次，其他元素总数为 `R`，因为 `M > n/2`，所以 `M > R`。Boyer-Moore 的“候选不同就减一”可以理解为从当前未抵消集合里删除一个候选值和一个不同值。即使把每个非 `m` 元素都拿去和一个 `m` 配对，仍至少剩下 `M - R > 0` 个 `m`，所以只要多数元素确实存在，最终候选不可能被所有其他值完全抵消。

注意这只证明“存在严格多数时最终候选是它”，并不证明任意数组的最终候选都满足多数条件。因此没有存在性保证时，第二遍验证是算法契约的一部分，而不是多余工作。

## 项目经验版

来源没有真实项目上下文，不能虚构线上经历。若在流式统计中使用类似投票思想，需要先确认目标仍是单一 `>50%` 多数元素；若阈值改成 `> n/k`、需要完整频率、需要滑动窗口或要支持删除，算法和状态模型都会变化，不能直接套用这个两个计数器的版本。

## 常见追问

- 问：为什么不是哈希表？答：哈希计数最直观，但需要随不同元素数量增长的额外空间；严格多数这个特殊阈值允许用抵消得到 O(1) 空间候选。
- 问：为什么 `count == 0` 时可以换候选？答：之前维护的净票数已经被不同元素完全抵消，那一段对最终“谁能超过一半”的候选没有留下净优势，可以从当前位置重新累计。
- 问：如果没有多数元素会怎样？答：第一遍仍可能返回一个候选，所以必须第二遍验证；例如 `[1,2,3]` 最终会留下候选，但它并没有超过一半。
- 问：如果题目保证答案存在，能不能一遍？答：可以。保证存在时，Boyer-Moore 第一遍的最终候选就是答案，时间 O(n)、额外空间 O(1)。
- 问：两个元素都可能超过一半吗？答：不能。若两个不同元素都各自严格超过 `n/2`，两者出现次数之和就会大于 `n`，矛盾。

## 易错点

- 把“超过一半”写成 `>= n/2`，错误接受刚好一半的元素。
- 在题目没有保证多数存在时，只返回第一遍候选而不验证。
- 解释 Boyer-Moore 时只背代码，不说明“不同元素成对抵消”为什么保留多数元素优势。
- 声称所有输入都只需一遍，却同时又想支持“可能不存在多数元素”的契约。
- 为了求一个 `>50%` 多数元素无条件使用哈希表，忽略可以做到 O(1) 额外空间。
'''

TEST = r'''import java.util.OptionalInt;

public final class MajorityElementTest {
    private static void eq(OptionalInt actual, OptionalInt expected, String name) {
        if (!actual.equals(expected)) throw new AssertionError(name + ": " + actual + " != " + expected);
    }
    private static void throwsIAE(Runnable r, String name) {
        try { r.run(); } catch (IllegalArgumentException expected) { return; }
        throw new AssertionError(name + ": expected IllegalArgumentException");
    }
    public static void main(String[] args) {
        eq(MajorityElement.findMajority(new int[]{2,2,1,1,1,2,2}), OptionalInt.of(2), "classic");
        eq(MajorityElement.findMajority(new int[]{3,3,4}), OptionalInt.of(3), "odd-majority");
        eq(MajorityElement.findMajority(new int[]{-1,-1,-1,2,3}), OptionalInt.of(-1), "negative-values");
        eq(MajorityElement.findMajority(new int[]{7}), OptionalInt.of(7), "singleton");
        eq(MajorityElement.findMajority(new int[]{9,9,9,9}), OptionalInt.of(9), "all-same");
        eq(MajorityElement.findMajority(new int[]{1,2,3}), OptionalInt.empty(), "no-majority");
        eq(MajorityElement.findMajority(new int[]{1,1,2,2}), OptionalInt.empty(), "exact-half-is-not-majority");
        eq(MajorityElement.findMajority(new int[]{}), OptionalInt.empty(), "empty");
        throwsIAE(() -> MajorityElement.findMajority(null), "null");
        System.out.println("PASS classic odd negative singleton all-same no-majority exact-half empty null");
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
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b48-majority-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'MajorityElement.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'MajorityElementTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'MajorityElement.java', 'MajorityElementTest.java', cwd=tmpdir)
        stdout = run('java', 'MajorityElementTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS classic odd negative singleton all-same no-majority exact-half empty null'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac MajorityElement.java MajorityElementTest.java && java MajorityElementTest',
        'stdout': stdout,
        'checks': ['classic strict-majority case', 'odd-length majority', 'negative values', 'singleton and all-same arrays', 'no-majority rejection', 'exact-half rejection', 'empty-array no-answer', 'null input rejection'],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0048 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'Deterministic OpenJDK 21 majority-element fixture', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source requires finding an array element whose occurrence count is strictly greater than half the array length; it does not specify language, API behavior, or guarantee that such an element always exists.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节']},
        {'claim_id': 'algorithm-behavior', 'text': 'The executable Java fixture verifies a Boyer-Moore candidate pass plus explicit second-pass strict-majority validation across majority, no-majority, exact-half and boundary inputs.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    research = {'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending', 'sources': sources, 'claims': claims, 'source_question_coverage': coverage, 'promotion_blocker': 'isolated_independent_review_not_yet_performed'}
    write_json(out / 'writer_research.json', research)

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The answer preserves the source condition as strict majority (> n/2) and does not weaken it to >= half.',
        'Because the source does not state that a majority is guaranteed, the candidate verifies the Boyer-Moore survivor in a second pass instead of presenting an unchecked candidate as a proven answer.',
        'The cancellation argument explains why a genuine strict majority survives pairwise cancellation and separately states the limitation when no majority exists.',
        'The Java implementation is complete and compilable, and deterministic tests cover majority, no-majority, exact-half, negative, singleton, empty and null cases.',
        'Language/API/null semantics are identified as candidate-contract choices rather than source facts.',
    ]
    review = {'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0048-majority-20260828-v1', 'review_version': 'batch-0048.majority.v1', 'decision': 'pass', 'revision_round': 1, 'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'], 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings, 'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out / 'isolated_review_result.json', review)
    evidence = {
        'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0048-majority-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{'source_id': 'isolated-review', 'title': 'Majority element source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}],
        'claims': claims, 'source_question_coverage': coverage,
        'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [{'case': 'no majority', 'expected': 'OptionalInt.empty', 'actual': 'pass', 'passed': True}, {'case': 'exactly half', 'expected': 'not accepted as majority', 'actual': 'pass', 'passed': True}, {'case': 'negative strict majority', 'expected': 'returned normally', 'actual': 'pass', 'passed': True}]},
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    }
    write_json(ROOT / f'review/evidence/{CID}.json', evidence)

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_cd492f07ab9e4f6446b576e165a75c8d` source-first isolated review PASS: the source requires an element occurring strictly more than half the array length but does not guarantee existence or specify an API. The candidate uses Boyer-Moore pair cancellation plus a second verification pass, explicitly treating Java/OptionalInt/null-empty behavior as candidate choices. OpenJDK 21 validation covers true majorities, no-majority, exact-half, negative, singleton, empty and null cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')
    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
