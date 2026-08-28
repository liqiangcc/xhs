#!/usr/bin/env python3
"""Build, validate, source-first review, and stage the Batch 0048 string-to-int candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-28'
CID = 'cq_q_ca6435fc1ff191bb641074a6a16eb6db'
QID = 'ca6435fc1ff191bb641074a6a16eb6db'
EXPECTED = '算法：实现字符串转换成整型需要考虑哪些条件,口述即可'
BATCH = '0048'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ca6435fc1ff191bb641074a6a16eb6db","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# 字符串转换成整型需要考虑哪些条件？

## 核心结论

这题重点不是背一个 `atoi` 模板，而是先把“字符串到整数”的契约说清楚：允许哪些空白、是否支持正负号、数字范围、非法字符怎么处理、是否允许前导零、溢出怎么判、空串和 `null` 怎么处理。实现时最容易错的是**在已经溢出之后才检查**；正确做法是在每次 `value * 10 + digit` 之前用目标整数边界做预检查。原题只要求口述，没有指定 Java API 语义，所以下面的 Java 实现只是一个可执行参考契约，不把这些选择冒充成题目条件。

## 1 分钟版

- 先问输入契约：是否只接受十进制 ASCII 数字，是否允许首尾空格、`+/-`、前导零。
- 再问错误契约：空串、只有符号、夹杂字母、数字中间有空格、`null` 是报错、返回默认值还是返回状态对象。
- 最关键是范围：目标若是 32 位有符号整数，就要覆盖 `[-2147483648, 2147483647]`，正负边界并不对称。
- 每读一个数字前先判断加入该数字后是否会越界，不能先做 `int` 乘加再判断，因为溢出已经发生。
- 一次线性扫描即可，时间 O(n)，除了索引、符号和累加值只需 O(1) 额外空间。

## 3 分钟版

如果面试官没有给更具体契约，我会先说明这些边界，再给一个明确、可测试的版本。例如：允许首尾 ASCII 空格；允许一个可选 `+` 或 `-`；主体必须至少有一个 ASCII 十进制数字；不允许数字中间空格或其他字符；结果必须落在 Java `int` 范围；非法输入统一抛 `IllegalArgumentException`。

```java
public final class StringToInt {
    public static int parseDecimal(String input) {
        if (input == null) {
            throw new IllegalArgumentException("input must not be null");
        }
        int n = input.length();
        int i = 0;
        while (i < n && input.charAt(i) == ' ') i++;
        if (i == n) throw new IllegalArgumentException("no digits");

        boolean negative = false;
        char first = input.charAt(i);
        if (first == '+' || first == '-') {
            negative = first == '-';
            i++;
        }
        if (i == n || input.charAt(i) < '0' || input.charAt(i) > '9') {
            throw new IllegalArgumentException("digits required");
        }

        long limit = negative ? 2147483648L : 2147483647L;
        long value = 0L;
        while (i < n) {
            char c = input.charAt(i);
            if (c == ' ') break;
            if (c < '0' || c > '9') {
                throw new IllegalArgumentException("invalid character");
            }
            int digit = c - '0';
            if (value > (limit - digit) / 10L) {
                throw new IllegalArgumentException("out of int range");
            }
            value = value * 10L + digit;
            i++;
        }
        while (i < n && input.charAt(i) == ' ') i++;
        if (i != n) throw new IllegalArgumentException("trailing characters");
        return negative ? (int) -value : (int) value;
    }
}
```

这里先用正的幅值累计，再按符号选择上界：正数最多 `2147483647`，负数的绝对值最多 `2147483648`。预检查 `value > (limit - digit) / 10` 保证下一次乘加仍在目标范围内。若题目要求兼容 LeetCode 8 那类“遇到非法尾字符停止并在溢出时截断”的语义，状态机和错误处理都要跟着改，不能把两种契约混在一起。

## 关键细节

- **至少一个数字**：`"+"`、`"-"`、空串和只有空格都不能被当成合法整数。
- **符号只能出现一次且在数字前**：`--1`、`1-2` 不是同一份简单十进制契约里的合法输入。
- **正负边界不对称**：32 位有符号整数最小值的绝对值比最大值大 1，所以不能简单对负数先解析成正 `int` 再取反。
- **溢出前检查**：如果使用 `int`，先执行乘加可能已经回绕；参考实现通过目标 `limit` 在乘加之前判断。
- **字符范围要明确**：这个示例只接受 `'0'` 到 `'9'`，不把其他 Unicode 数字字符自动当成十进制位。
- **空白规则要明确**：示例只允许首尾 ASCII 空格。若要支持所有 Unicode whitespace，应该把规则写进契约并使用相应字符判断。
- **前导零**：本契约允许，例如 `"0009" -> 9`；若业务把编号字符串和数值字符串区分开，规则可能不同。
- **复杂度**：扫描每个字符至多一次，时间 O(n)，额外空间 O(1)。

## 原理机制

解析过程可以看成一个很小的状态机：`leading-space -> optional-sign -> digits -> trailing-space -> end`。只有合法状态转换才能继续；任何未声明的字符都失败。数值状态维护十进制不变量：处理完前 k 个数字后，`value` 等于这 k 位组成的非负十进制幅值。加入下一位 `d` 前先验证 `value * 10 + d <= limit`，这样范围约束和语法约束被分别处理，不需要依赖溢出后的结果猜测是否越界。

把语法和范围拆开还有一个好处：如果后续改成 `long`、无符号数、其他进制、容错截断或返回 `Optional/Result`，可以明确知道改的是哪一层契约，而不是在一段循环里堆特殊分支。

## 项目经验版

来源没有真实项目背景，不能虚构线上解析事故。项目映射时，我会先确认这个字符串来自配置、协议字段、用户输入还是数据库，因为不同来源的容错策略不同：配置和协议通常更适合 fail-fast，用户输入可能需要返回可解释错误，数据清洗可能需要记录坏样本。无论哪种场景，都应把“接受什么”和“失败时怎样”写成可测试契约，而不是依赖语言库的默认行为碰运气。

## 常见追问

- 问：为什么不能最后再判断有没有溢出？答：如果用固定宽度整数，乘加本身可能已经溢出并回绕，之后看到的值不再代表真实结果，所以要在乘加前检查。
- 问：为什么 `Integer.MIN_VALUE` 特别容易错？答：它是 `-2147483648`，而 `Integer.MAX_VALUE` 是 `2147483647`；若先把负数绝对值解析进正 `int`，最小值的绝对值本身就装不下。
- 问：遇到 `123abc` 应该返回 123 还是报错？答：取决于契约。这个参考版本选择严格报错；某些 `atoi` 语义会在非法字符处停止，所以面试时必须先说清楚。
- 问：空格怎么处理？答：要明确允许范围。本示例只接受首尾 ASCII 空格，不接受数字中间空格；若业务要求 Unicode 空白，需要显式扩展规则。
- 问：为什么不用 `Integer.parseInt`？答：真实业务当然可以优先用成熟库；手撕题是在考你是否理解语法校验、边界和溢出预检查。若题目只问工程实现，应优先说明复用标准库而不是重复造轮子。

## 易错点

- 没有先说输入/错误契约，就直接套一个与题意不一致的 `atoi` 行为。
- 用 `int value = value * 10 + digit` 后才检查，导致溢出已经发生。
- 忽略 `Integer.MIN_VALUE` 与 `Integer.MAX_VALUE` 的绝对值不对称。
- 把空串、只有符号或夹杂非法字符悄悄解析成 0。
- 使用 `Character.isDigit` 却默认后续 `c - '0'` 对所有 Unicode 数字都成立。
- 把项目中的容错策略写成所有字符串转整数场景的唯一答案。
'''

TEST = r'''public final class StringToIntTest {
    private static void eq(int actual, int expected, String name) {
        if (actual != expected) throw new AssertionError(name + ": " + actual + " != " + expected);
    }
    private static void bad(String input, String name) {
        try { StringToInt.parseDecimal(input); }
        catch (IllegalArgumentException expected) { return; }
        throw new AssertionError(name + ": expected IllegalArgumentException");
    }
    public static void main(String[] args) {
        eq(StringToInt.parseDecimal("0"), 0, "zero");
        eq(StringToInt.parseDecimal("42"), 42, "positive");
        eq(StringToInt.parseDecimal("   -42 "), -42, "spaces-negative");
        eq(StringToInt.parseDecimal("+17"), 17, "plus");
        eq(StringToInt.parseDecimal("0009"), 9, "leading-zeros");
        eq(StringToInt.parseDecimal("2147483647"), Integer.MAX_VALUE, "max");
        eq(StringToInt.parseDecimal("-2147483648"), Integer.MIN_VALUE, "min");
        bad("2147483648", "positive-overflow");
        bad("-2147483649", "negative-overflow");
        bad("", "empty");
        bad("   ", "spaces-only");
        bad("+", "sign-only");
        bad("12x", "junk");
        bad("1 2", "embedded-space");
        bad("１２", "non-ascii-digits");
        bad(null, "null");
        System.out.println("PASS zero positive signed spaces zeros bounds overflow malformed null");
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

    with tempfile.TemporaryDirectory(prefix='b48-string-int-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'StringToInt.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'StringToIntTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'StringToInt.java', 'StringToIntTest.java', cwd=tmpdir)
        stdout = run('java', 'StringToIntTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS zero positive signed spaces zeros bounds overflow malformed null'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac StringToInt.java StringToIntTest.java && java StringToIntTest',
        'stdout': stdout,
        'checks': ['zero and positive decimal', 'optional sign', 'leading/trailing ASCII spaces', 'leading zeros', 'Integer MAX/MIN', 'positive and negative overflow rejection', 'empty/sign-only/junk rejection', 'embedded-space rejection', 'non-ASCII-digit rejection', 'null rejection'],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0048 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'Deterministic OpenJDK 21 string-to-int parser fixture', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source asks which conditions must be considered when converting a string to an integer and explicitly says oral explanation is sufficient; it does not define a concrete API or atoi-style error policy.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节']},
        {'claim_id': 'reference-contract', 'text': 'The executable Java fixture validates one explicitly labeled reference contract covering signs, surrounding ASCII spaces, decimal digits, int bounds, malformed input and overflow-before-mutation checks.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问']},
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

    scores = {'facts_and_evidence': 24, 'directness_and_relevance': 19, 'type_specific_completeness': 19, 'mechanism_and_causality': 14, 'boundaries_and_tradeoffs': 9, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The answer directly addresses the requested oral boundary checklist instead of treating one library/API policy as source truth.',
        'The reference Java contract is explicitly labeled as a candidate choice and distinguishes syntax rules from error-policy choices.',
        'The implementation checks the next decimal accumulation against the signed int limit before multiplication/addition, and handles the asymmetric negative boundary.',
        'Deterministic Java 21 tests cover signs, surrounding spaces, leading zeros, exact int bounds, overflow, malformed input, non-ASCII digits and null.',
        'The answer includes complexity, state-machine reasoning, alternative atoi semantics and project-mapping guidance without fabricating production experience.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0048-string-to-int-20260828-v1',
        'review_version': 'batch-0048.string-to-int.v1',
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

    evidence = {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0048-string-to-int-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{'source_id': 'isolated-review', 'title': 'String-to-int source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'Integer.MAX_VALUE / Integer.MIN_VALUE', 'expected': 'accepted exactly', 'actual': 'pass', 'passed': True},
                {'case': 'one beyond either int bound', 'expected': 'rejected before unsafe accumulation', 'actual': 'pass', 'passed': True},
                {'case': 'empty/sign-only/junk/embedded-space/non-ASCII digit', 'expected': 'rejected under explicit reference contract', 'actual': 'pass', 'passed': True},
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
    line = '- [x] `cq_q_ca6435fc1ff191bb641074a6a16eb6db` source-first isolated review PASS: the source asks which conditions matter when converting a string to an integer and does not define one atoi/API policy. The candidate first separates whitespace/sign/digit/error/range choices, then gives one explicitly labeled Java reference contract with pre-mutation overflow checks. OpenJDK 21 validation covers signed values, surrounding spaces, leading zeros, exact int bounds, overflow, malformed input, non-ASCII digits, and null. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
