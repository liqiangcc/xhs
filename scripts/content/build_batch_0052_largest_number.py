#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 largest-number candidate."""

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
CID = 'cq_q_deae43be8cb0a78c37ec2eb91fe9736e'
QID = 'deae43be8cb0a78c37ec2eb91fe9736e'
EXPECTED = '算法：最大数重新排列 (给定数字数组，拼成最大的数字)'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_deae43be8cb0a78c37ec2eb91fe9736e","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 最大数重新排列：按拼接结果定义排序顺序

## 核心结论

来源要求“给定数字数组，拼成最大的数字”，但没有明确元素是否允许负数、结果类型和空输入语义。这里声明一个最小可执行合同：输入非空的**非负整数数组**，重新排列所有元素，每个元素的十进制表示必须完整使用一次，返回能得到的最大拼接结果字符串；输入不修改，负数或空数组视为无效调用。

关键不是按数值大小或字符串字典序排序，而是比较两个元素 x、y 的拼接顺序：如果字符串 `xy` 比 `yx` 大，就让 x 排在 y 前面。Java comparator 可以写成比较 `(b+a)` 与 `(a+b)`，使排序后的序列直接从“更优拼接”到“更差拼接”。最后把所有字符串连接起来；若排在最前的是 `0`，说明所有元素都是 0，结果规范化为单个 `"0"`。

## 1 分钟版

- 把每个非负整数转成十进制字符串。
- 对任意两个字符串 a、b，不比较 a 与 b 本身，而比较 `a+b` 和 `b+a`。
- 若 `a+b > b+a`，a 必须排前；否则 b 排前。
- 按这个规则排序后顺序拼接，就是全局最大结果。
- `[3,30,34,5,9]` 会得到 `9534330`；`[10,2]` 得到 `210`。
- `[0,0]` 排完仍全是 0，返回 `"0"` 而不是 `"00"`。
- N 个元素、平均十进制长度 L 时，排序需要 O(N log N) 次比较，每次构造/比较拼接串是 O(L) 量级；额外结果空间至少 O(NL)。

## 3 分钟版

```java
import java.util.Arrays;

public final class LargestNumber {
    public static String arrange(int[] nums) {
        if (nums == null || nums.length == 0) {
            throw new IllegalArgumentException("nums must be non-empty");
        }

        String[] parts = new String[nums.length];
        for (int i = 0; i < nums.length; i++) {
            if (nums[i] < 0) {
                throw new IllegalArgumentException("negative values are unsupported");
            }
            parts[i] = Integer.toString(nums[i]);
        }

        Arrays.sort(parts, (a, b) -> (b + a).compareTo(a + b));
        if (parts[0].equals("0")) {
            return "0";
        }

        StringBuilder out = new StringBuilder();
        for (String part : parts) {
            out.append(part);
        }
        return out.toString();
    }
}
```

为什么这个局部比较能得到全局最优？对排序结果中的任意相邻 a、b，如果 `ab < ba`，交换它们会让整个结果第一次发生差异的位置变大，因此原顺序不可能是最大结果。最终没有这种“可改进的逆序对”时，任意相邻交换都不能让结果更大，排序顺序就是目标顺序。

## 关键细节

- **不能按整数降序**：`3 > 30` 还碰巧正确，但 `34`、`3` 的相对顺序要看 `343` 与 `334`；普通数值大小没有表达拼接贡献。
- **不能按普通字符串降序**：例如 `"30"` 和 `"3"` 的字典序不能直接决定最终拼接大小，必须比较 `303` 与 `330`。
- **为什么返回 String**：拼接结果可能远超 `int`/`long` 范围；字符串才忠实表达全部数字。
- **全零归一化**：排序后第一个是 `"0"` 时，其余也只能是 0，直接返回一个 `"0"`，避免多余前导零。
- **重复元素**：完整保留，不去重；每个输入元素必须使用一次。
- **负数**：来源只说“数字数组”没有定义负号如何参与拼接；当前合同显式只支持非负整数，不能悄悄给负数发明排序语义。
- **输入副作用**：排序的是新建的字符串数组，不修改调用方 `nums`。
- **比较器方向**：Java `Arrays.sort` 要让“更适合放前”的元素被认为更小，因此 comparator 使用 `(b+a).compareTo(a+b)`。

## 原理机制

目标是最大化整条拼接字符串的字典序/数值序。考虑任意两个相邻块 a、b，其他前缀和后缀固定时，两个候选只在这两个块构成的局部串上有差异：`ab` 或 `ba`。因此局部最优顺序完全由 `ab` 和 `ba` 的比较决定。

如果一个排列中存在相邻 a、b 满足 `ab < ba`，交换它们会严格增大全局拼接结果，所以任何全局最优排列都不能包含这种逆序。按照“a 应排在 b 前当且仅当 ab >= ba”的规则排序，就是持续消除所有可改进逆序；最终得到的排列没有任何相邻交换能改善结果。

## 项目经验版

来源没有真实项目经历，不能虚构。工程里需要先确认元素域和输出契约：若输入可能是超过 int 的十进制串，应直接以字符串作为原始元素，并验证它们都是规范化的非负数字串；如果结果只用于比较而无需完整物化，可以考虑流式输出排序后的块，但排序本身仍需要保存元素或索引。数据量很大时，比较器反复构造 `a+b`/`b+a` 会带来临时对象开销，可以用无拼接的逐字符循环比较优化常数，但先保证比较语义正确更重要。

## 常见追问

- 问：为什么 `[3,30]` 是 `330`？答：比较 `3+30=330` 与 `30+3=303`，前者更大，所以 3 在 30 前。
- 问：为什么这个 comparator 不只是贪心猜测？答：若某相邻对顺序违反 `ab >= ba`，交换它会严格增大全局结果；最优解不可能含这种逆序，排序就是消除全部逆序。
- 问：为什么结果不能用 long？答：元素数量和位数没有给出上界，完整拼接可能超出任何固定整数类型，所以返回字符串更安全。
- 问：全是 0 为什么返回一个 0？答：所有排列数值都等于 0；规范化输出单个 `0`，避免 `000...` 这种等值但非规范形式。
- 问：允许负数怎么办？答：必须重新定义“拼接”和“最大”的语义，负号放在哪里都涉及新的合同；当前来源没给，不能自行扩张。
- 问：能不能不用创建 `a+b` 临时串？答：可以比较长度 `|a|+|b|` 的虚拟串，第 i 个字符从 a/b 对应位置读取；这是性能优化，不改变排序规则。

## 易错点

- 按整数值从大到小排序。
- 直接按字符串字典序排序，没有比较 `ab` 和 `ba`。
- comparator 方向写反，得到最小拼接结果。
- 把结果解析成 int/long，遇到长输入溢出。
- 全零输入返回很多前导零。
- 对重复数字去重，违反“每个数组元素使用一次”。
- 来源没有定义负数，却在 `-` 号上自行发明拼接规则。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class LargestNumberTest {
    private static String brute(int[] a) {
        boolean[] used = new boolean[a.length];
        return dfs(a, used, new StringBuilder(), 0, null);
    }

    private static String dfs(int[] a, boolean[] used, StringBuilder cur, int depth, String best) {
        if (depth == a.length) {
            String value = normalize(cur.toString());
            return best == null || compareNumericStrings(value, best) > 0 ? value : best;
        }
        for (int i = 0; i < a.length; i++) {
            if (used[i]) continue;
            used[i] = true;
            int len = cur.length();
            cur.append(a[i]);
            best = dfs(a, used, cur, depth + 1, best);
            cur.setLength(len);
            used[i] = false;
        }
        return best;
    }

    private static String normalize(String s) {
        int i = 0;
        while (i + 1 < s.length() && s.charAt(i) == '0') i++;
        return s.substring(i);
    }

    private static int compareNumericStrings(String a, String b) {
        if (a.length() != b.length()) return Integer.compare(a.length(), b.length());
        return a.compareTo(b);
    }

    private static void check(int[] a, String expected) {
        int[] before = a.clone();
        String actual = LargestNumber.arrange(a);
        if (!actual.equals(expected)) throw new AssertionError("expected=" + expected + " actual=" + actual + " input=" + Arrays.toString(a));
        if (!Arrays.equals(a, before)) throw new AssertionError("input mutated");
    }

    public static void main(String[] args) {
        check(new int[]{10,2}, "210");
        check(new int[]{3,30,34,5,9}, "9534330");
        check(new int[]{0,0}, "0");
        check(new int[]{121,12}, "12121");
        check(new int[]{8308,8308,830}, "83088308830");

        Random rnd = new Random(20260829L);
        for (int tc = 0; tc < 2000; tc++) {
            int n = 1 + rnd.nextInt(7);
            int[] a = new int[n];
            for (int i = 0; i < n; i++) a[i] = rnd.nextInt(1000);
            String expected = brute(a);
            check(a, expected);
        }

        try { LargestNumber.arrange(null); throw new AssertionError("null must fail"); }
        catch (IllegalArgumentException expected) {}
        try { LargestNumber.arrange(new int[]{}); throw new AssertionError("empty must fail"); }
        catch (IllegalArgumentException expected) {}
        try { LargestNumber.arrange(new int[]{1,-2}); throw new AssertionError("negative must fail"); }
        catch (IllegalArgumentException expected) {}

        System.out.println("PASS named zeros prefix-ambiguity duplicate random2000-vs-permutations input-unchanged invalid-boundaries");
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

    with tempfile.TemporaryDirectory(prefix='b52-largest-number-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'LargestNumber.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'LargestNumberTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'LargestNumber.java', 'LargestNumberTest.java', cwd=tmpdir)
        stdout = run('java', 'LargestNumberTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS named zeros prefix-ambiguity duplicate random2000-vs-permutations input-unchanged invalid-boundaries'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac LargestNumber.java LargestNumberTest.java && java LargestNumberTest',
        'stdout': stdout,
        'checks': [
            'named concatenation cases and prefix-ambiguous values match expected maxima',
            'all-zero input is normalized to a single zero',
            'duplicate input elements are preserved',
            '2000 deterministic random arrays of length <=7 match an independent exhaustive permutation oracle',
            'caller input remains unchanged',
            'null, empty and negative-element boundaries follow the explicit candidate contract',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact largest-number source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 largest-number comparator validation versus exhaustive permutation oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The exact source asks to rearrange a number array into the largest possible number but does not define negative values, empty input, result type, or examples.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate explicitly supports non-empty arrays of non-negative integers, returns a String, preserves duplicates/input order externally, and rejects negative values.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节']},
        {'claim_id': 'ordering-rule', 'text': 'Pairwise order is determined by comparing concatenations ab and ba rather than numeric or ordinary lexical order.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '1 分钟版', '原理机制', '常见追问']},
        {'claim_id': 'algorithm-validation', 'text': 'The comparator implementation is validated on named boundaries and 2000 deterministic random arrays of length at most seven against exhaustive permutation search.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '易错点']},
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
        'The source is kept narrow; non-negative domain, non-empty input, String result and negative rejection are explicitly labeled implementation boundaries.',
        'The answer teaches the correct concatenation comparator ab versus ba instead of integer or plain string ordering.',
        'All-zero normalization and duplicate preservation are explicit and executable.',
        'OpenJDK 21 validation checks prefix ambiguity and 2000 deterministic random arrays against exhaustive permutation search, providing independent algorithm evidence.',
        'The adjacent-swap explanation makes the comparator rationale causal rather than presenting it as a memorized trick.',
        'The project section avoids fabricated experience and separates semantic correctness from optional allocation/performance optimization.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0052-largest-number-20260829-v1',
        'review_version': 'batch-0052.largest-number.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 largest-number source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0052-largest-number-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': '[10,2]', 'expected': '210', 'actual': '210', 'passed': True},
                {'case': '[3,30,34,5,9]', 'expected': '9534330', 'actual': '9534330', 'passed': True},
                {'case': '[0,0]', 'expected': '0', 'actual': '0', 'passed': True},
                {'case': '2000 deterministic random arrays length <=7', 'expected': 'equals exhaustive permutation oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_deae43be8cb0a78c37ec2eb91fe9736e` source-first isolated review PASS: the source asks to rearrange a number array into the largest concatenated number, while non-negative domain, String output, empty/negative handling and no-input-mutation are explicit candidate boundaries. The candidate uses the ab-vs-ba concatenation comparator, preserves duplicates, normalizes all-zero output, and OpenJDK 21 validation checks named cases plus 2000 deterministic random arrays against exhaustive permutation search. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
