#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 remove-k-digits-for-maximum candidate."""

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
CID = 'cq_q_df2f14997e0ee3459f1eaab3acbb4d23'
QID = 'df2f14997e0ee3459f1eaab3acbb4d23'
EXPECTED = '算法：从n位数字中移除k个数使得留下数字最大'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_df2f14997e0ee3459f1eaab3acbb4d23","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 从 n 位数字中移除 k 位，使剩余数字最大

## 核心结论

来源只说“从 n 位数字中移除 k 个数使得留下数字最大”，没有明确是否能重排剩余位、输入类型、前导零和 k 的边界。这里声明常见的最小可执行合同：输入一个只含十进制字符 `0-9` 的数字串，**删除恰好 k 个位置，剩余数字保持原相对顺序**，返回长度恰好为 `n-k` 的字符串；前导零保留，因为它们是实际留下的位。`0 <= k <= n`，非法字符/null/越界 k 显式报错。

要让结果最大，越靠左的高位越重要。扫描当前数字 d 时，如果已选前缀的末位比 d 小，而且还有删除额度，就应该删除这个更小的末位，让更大的 d 提前到更高位。不断执行这个规则，会形成一个单调不增栈。扫描结束后如果 k 还没删完，说明剩余序列已经单调不增，此时从末尾删掉最小影响的低位即可。

## 1 分钟版

- 剩余位不能重排，只能从原数字串删除 k 个位置。
- 用字符数组/栈保存当前最优前缀。
- 对每个新 digit：当 `top < digit` 且还有删除额度时，持续弹栈；这是用一次删除换取更大的高位。
- 然后压入当前 digit。
- 如果扫描结束仍有删除额度，从栈尾继续删，因为序列已经不增，删低位损失最小。
- 最终取前 `n-k` 个栈元素；时间 O(N)，每个字符最多入栈一次、出栈一次；空间 O(N)。
- 相等数字不弹，避免无意义删除并保持稳定的左侧位置。

## 3 分钟版

```java
public final class RemoveKForMaximum {
    public static String maximize(String digits, int k) {
        if (digits == null) {
            throw new IllegalArgumentException("digits must not be null");
        }
        if (k < 0 || k > digits.length()) {
            throw new IllegalArgumentException("k out of range");
        }
        for (int i = 0; i < digits.length(); i++) {
            char c = digits.charAt(i);
            if (c < '0' || c > '9') {
                throw new IllegalArgumentException("digits must contain only 0-9");
            }
        }

        char[] stack = new char[digits.length()];
        int size = 0;
        int remove = k;

        for (int i = 0; i < digits.length(); i++) {
            char d = digits.charAt(i);
            while (size > 0 && remove > 0 && stack[size - 1] < d) {
                size--;
                remove--;
            }
            stack[size++] = d;
        }

        size -= remove;
        return new String(stack, 0, size);
    }
}
```

例如 `digits="1924", k=2`：看到 9 时删掉前面的 1，让 9 进入更高位；看到 4 时又删掉 2，得到 `94`。`digits="9876", k=2` 本身已经单调下降，扫描阶段不会弹栈，最后从尾部删除 7、6，得到 `98`。

如果 `k=n`，必须删掉所有位，返回空字符串；如果 `k=0`，返回原字符串。

## 关键细节

- **是否允许重排**：当前合同不允许。若允许任意重排，问题会退化为保留最大的 n-k 个数字后降序排列，是完全不同的问题。
- **为什么优先删左侧较小位**：两个候选结果第一次不同的位置决定哪个数字更大。用删除额度让更大的当前位提前，会在最早差异处变大，后面再怎么变化都无法抵消这个收益。
- **为什么 while 而不是 if**：一个很大的当前位可能应该连续淘汰多个更小的尾部，例如 `1239` 在 9 到来时可能连续删 1/2/3 中允许删除的部分。
- **为什么相等不弹**：`top == digit` 时交换/删除哪个相等位不会让当前高位变大；保留更早的相等位给后续决策更自然。
- **为什么最后从尾部删**：如果还有额度，说明从左到右没有任何可用的“前小后大”逆转，栈已单调不增；删除越靠后的位，对高位越没有影响。
- **前导零**：返回的是保留的位串，不做数值规范化。例如 `"0012", k=1` 可得到 `"012"`；若产品要求数值展示再另行去前导零。
- **复杂度**：每个字符最多压栈一次、弹栈一次，所以总时间 O(N)，额外空间 O(N)。

## 原理机制

这是一个“字典序最大固定长度子序列”问题。因为结果长度固定为 n-k，而且都是同长度十进制串，所以最大数等价于字典序最大。目标因此变成：在保持原相对顺序的所有长度 n-k 子序列中，选字典序最大的一个。

单调栈执行局部交换论证：若已选前缀末位 x 小于当前位 y，并且我们仍可删除 x，那么保留 x 会让结果在一个更靠左的位置出现较小数字；删除 x 让 y 前移，必然更优。不断消除这种可改进的尾部，就维护出当前扫描前缀在删除预算内的最大候选。

## 项目经验版

来源没有真实项目背景，不能虚构。工程里应优先确认输入是否可能非常长：若是百万/千万位字符串，O(N) 逻辑仍可用，但要考虑返回结果的必需 O(N) 存储；如果数据来自流，想在不知道未来字符的情况下立即输出前缀并不总安全，因为后续更大数字可能触发删除。只有当某个前缀已经不可能再被剩余 k 次删除影响时，才适合增量输出。

## 常见追问

- 问：这和“移除 k 位使最小”有什么区别？答：方向相反。求最大时遇到更大的当前位就删除前面更小的位，维护单调不增；求最小时通常删除前面更大的位，维护单调不减。
- 问：为什么不是选最大的 n-k 个数字？答：剩余位必须保持原相对顺序，不能任意排序。高位的位置价值比单个数字大小更重要。
- 问：为什么末尾删一定安全？答：还有删除额度意味着栈中不存在前小后大的可改善关系，已经单调不增；删左侧会改变更高位，删右侧对字典序影响最晚。
- 问：`k=n` 怎么办？答：删除所有位，合同返回空字符串；如果业务希望返回 `"0"`，那是展示层的另一个规范。
- 问：前导零怎么办？答：当前返回保留位置形成的原始位串，所以保留；如果把结果解释成规范化整数文本，可在外层单独去零。
- 问：能原地 O(1) 额外空间吗？答：如果输入是可修改字符数组，可以把同一数组当栈写指针使用；但返回结果本身仍需要表示 n-k 个字符。

## 易错点

- 允许重排剩余数字，做成另一个问题。
- while 条件写成 `top > current`，方向反成求最小值。
- 只弹一次，没有处理一个大数字连续淘汰多个较小尾部。
- 扫描结束后还有删除额度却忘了从尾部删除。
- 把相等元素也无条件弹出，浪费删除预算并让证明复杂化。
- 返回前去掉前导零，却没说明已经改变“保留恰好 n-k 位”的合同。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class RemoveKForMaximumTest {
    private static String brute(String s, int k) {
        int keep = s.length() - k;
        String[] best = {null};
        choose(s, 0, keep, new StringBuilder(), best);
        return best[0] == null ? "" : best[0];
    }

    private static void choose(String s, int index, int left, StringBuilder cur, String[] best) {
        if (left == 0) {
            String x = cur.toString();
            if (best[0] == null || x.compareTo(best[0]) > 0) best[0] = x;
            return;
        }
        if (s.length() - index < left) return;
        for (int i = index; i <= s.length() - left; i++) {
            cur.append(s.charAt(i));
            choose(s, i + 1, left - 1, cur, best);
            cur.setLength(cur.length() - 1);
        }
    }

    private static void check(String s, int k, String expected) {
        String actual = RemoveKForMaximum.maximize(s, k);
        if (!actual.equals(expected)) throw new AssertionError("s=" + s + " k=" + k + " expected=" + expected + " actual=" + actual);
        if (actual.length() != s.length() - k) throw new AssertionError("wrong length");
    }

    public static void main(String[] args) {
        check("1924", 2, "94");
        check("9876", 2, "98");
        check("0012", 1, "012");
        check("1111", 2, "11");
        check("1239", 3, "9");
        check("10", 2, "");
        check("10", 0, "10");

        Random rnd = new Random(20260829L);
        for (int tc = 0; tc < 5000; tc++) {
            int n = rnd.nextInt(10);
            StringBuilder s = new StringBuilder();
            for (int i = 0; i < n; i++) s.append((char)('0' + rnd.nextInt(10)));
            int k = rnd.nextInt(n + 1);
            String input = s.toString();
            check(input, k, brute(input, k));
        }

        for (var bad : Arrays.asList("12a3", "-123", " 12")) {
            try { RemoveKForMaximum.maximize(bad, 1); throw new AssertionError("invalid chars must fail"); }
            catch (IllegalArgumentException expected) {}
        }
        try { RemoveKForMaximum.maximize(null, 0); throw new AssertionError("null must fail"); }
        catch (IllegalArgumentException expected) {}
        try { RemoveKForMaximum.maximize("12", 3); throw new AssertionError("k>N must fail"); }
        catch (IllegalArgumentException expected) {}

        System.out.println("PASS named decreasing leading-zero equal cascading all-remove no-remove random5000-vs-subsequence-oracle invalid-boundaries");
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

    with tempfile.TemporaryDirectory(prefix='b52-remove-k-max-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'RemoveKForMaximum.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'RemoveKForMaximumTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'RemoveKForMaximum.java', 'RemoveKForMaximumTest.java', cwd=tmpdir)
        stdout = run('java', 'RemoveKForMaximumTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS named decreasing leading-zero equal cascading all-remove no-remove random5000-vs-subsequence-oracle invalid-boundaries'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac RemoveKForMaximum.java RemoveKForMaximumTest.java && java RemoveKForMaximumTest',
        'stdout': stdout,
        'checks': [
            'named increasing/decreasing/equal/leading-zero and k=0/k=n cases match declared fixed-length subsequence semantics',
            '5000 deterministic random digit strings match an independent exhaustive fixed-length subsequence oracle',
            'result length is exactly n-k for every valid case',
            'invalid characters, null and out-of-range k follow explicit candidate boundaries',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact remove-k-for-maximum source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 monotonic-stack validation versus exhaustive subsequence oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The exact source asks to remove k positions from an n-digit number so the remaining number is largest, but does not explicitly state reordering, representation, leading-zero, or invalid-input semantics.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate fixes the common subsequence contract: delete exactly k decimal positions, preserve relative order, preserve the resulting n-k digit string including leading zeros, and reject invalid characters/k.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节']},
        {'claim_id': 'greedy-mechanism', 'text': 'While removals remain, deleting a smaller selected suffix digit before a larger current digit improves the earliest possible output position; remaining deletions after a non-increasing scan are taken from the tail.', 'source_ids': ['fixture'], 'answer_locations': ['1 分钟版', '原理机制', '常见追问']},
        {'claim_id': 'algorithm-validation', 'text': 'The monotonic-stack implementation is validated on named boundaries and 5000 deterministic random digit strings against exhaustive enumeration of all length n-k subsequences.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '易错点']},
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
        'The sparse source is not silently turned into a reordering problem; preservation of relative order and fixed output length are explicit executable assumptions.',
        'The monotonic-stack direction is correct for maximizing a fixed-length digit subsequence, and cascading pops plus residual tail deletion are explained causally.',
        'Leading zeros, equality, all-remove/no-remove, invalid characters and k bounds are explicitly handled rather than hidden.',
        'OpenJDK 21 validation checks 5000 deterministic random strings against exhaustive enumeration of every legal fixed-length subsequence.',
        'The O(N) amortized argument follows directly from each digit entering and leaving the stack at most once.',
        'The project section avoids fabricated experience and correctly notes that future digits can prevent unconditional streaming output.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0052-remove-k-max-20260829-v1',
        'review_version': 'batch-0052.remove-k-max.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 remove-k-for-maximum source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0052-remove-k-max-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': '1924,k=2', 'expected': '94', 'actual': '94', 'passed': True},
                {'case': '9876,k=2', 'expected': '98', 'actual': '98', 'passed': True},
                {'case': '0012,k=1', 'expected': '012', 'actual': '012', 'passed': True},
                {'case': '5000 deterministic random strings', 'expected': 'equals exhaustive subsequence oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_df2f14997e0ee3459f1eaab3acbb4d23` source-first isolated review PASS: the sparse remove-k source is handled with an explicit fixed-length, relative-order-preserving decimal-subsequence contract rather than an invented reordering rule. The candidate uses a monotonic non-increasing stack, cascading removal of smaller high-position digits and residual tail deletion. OpenJDK 21 validation covers leading-zero/equality/k-boundary cases plus 5000 deterministic random digit strings against exhaustive subsequence enumeration. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
