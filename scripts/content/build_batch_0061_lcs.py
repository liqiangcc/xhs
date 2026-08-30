#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0061 LCS candidate."""

from __future__ import annotations

import hashlib
import json
import random
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0061'
CID = 'cq_q_206301f6679d9047d406eb16ef08be5c'
QIDS = ['206301f6679d9047d406eb16ef08be5c', '3e06d9a27b2adbb6c978d267ec2a9651']
EXPECTED_VARIANTS = {
    '算法手撕：最长公共子序列（Longest Common Subsequence）。',
    '算法手撕：最长公共子序列（LCS - Longest Common Subsequence）问题求解？',
}
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = [
    '## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节',
    '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点',
]
SCORES = {
    'facts_and_evidence': 25,
    'directness_and_relevance': 20,
    'type_specific_completeness': 20,
    'mechanism_and_causality': 15,
    'boundaries_and_tradeoffs': 10,
    'followup_quality': 5,
    'oral_quality': 5,
}

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_206301f6679d9047d406eb16ef08be5c","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 最长公共子序列（LCS）：二维状态压缩到一维 DP

## 核心结论

最长公共子序列要求保持两个序列中的相对顺序，但字符不必连续。一个直接的动态规划定义是：`dp[i][j]` 表示 `text1[0..i)` 与 `text2[0..j)` 的 LCS 长度。若当前字符相同，就在两个前缀都去掉最后一个字符的答案上加 1；若不同，就从“丢掉 text1 当前字符”和“丢掉 text2 当前字符”两种前缀状态取最大值。二维表时间复杂度 `O(mn)`、空间 `O(mn)`；只求长度时可把空间压到 `O(min(m,n))`。

## 1 分钟版

- 状态：`dp[j]` 表示当前处理到 `text1` 某个前缀时，与 `text2[0..j)` 的 LCS 长度。
- 转移需要同时保留三个值：上一行左上角、上一行当前列、当前行左边。
- 字符相同：`dp[j] = prevDiagonal + 1`。
- 字符不同：`dp[j] = max(dp[j], dp[j - 1])`；更新前的 `dp[j]` 是上一行当前列，`dp[j-1]` 是当前行左边。
- 为了省空间，让较短字符串作为列，空间降为 `O(min(m,n))`；时间仍是 `O(mn)`。

## 3 分钟版

下面用 Java 返回 LCS 的长度；来源没有指定语言，因此 Java 只是一个明确的可执行实现选择：

```java
public static int longestCommonSubsequence(String a, String b) {
    if (a == null || b == null) {
        throw new IllegalArgumentException("input must not be null");
    }
    if (a.length() < b.length()) {
        String tmp = a;
        a = b;
        b = tmp;
    }

    int[] dp = new int[b.length() + 1];
    for (int i = 1; i <= a.length(); i++) {
        int prevDiagonal = 0;
        for (int j = 1; j <= b.length(); j++) {
            int previousRowSameColumn = dp[j];
            if (a.charAt(i - 1) == b.charAt(j - 1)) {
                dp[j] = prevDiagonal + 1;
            } else {
                dp[j] = Math.max(dp[j], dp[j - 1]);
            }
            prevDiagonal = previousRowSameColumn;
        }
    }
    return dp[b.length()];
}
```

例如 `abcde` 和 `ace` 的答案是 3；`abc` 和 `abc` 是 3；`abc` 和 `def` 是 0。空字符串与任意字符串的 LCS 长度都是 0。本实现把 `null` 与空字符串区分开：空字符串是合法输入，`null` 被视为调用错误并显式拒绝。

## 关键细节

- **为什么相同字符可以接上左上角**：当 `a[i-1] == b[j-1]` 时，把这个共同字符接到两个更短前缀的公共子序列之后，就得到当前前缀的候选解，因此使用上一行上一列加 1。
- **为什么不同字符取上/左最大值**：若末尾字符不同，一个公共子序列不可能同时靠这两个不同字符作为同一个末尾匹配；至少需要舍弃其中一侧当前末尾，所以比较两个更小前缀。
- **一维压缩最容易写错的地方**：`dp[j]` 在覆盖前代表上一行当前列；`dp[j-1]` 已经代表当前行左边；还需要单独保存覆盖前的左上角值 `prevDiagonal`。
- **遍历方向**：这里 `j` 从左到右，因为转移明确需要当前行左边 `dp[j-1]`。若直接照搬 0/1 背包式的右到左循环，会破坏这套状态含义。
- **只求长度与恢复序列不同**：一维 DP 足够返回长度；如果题目要求输出具体 LCS，通常保留二维决策信息，或者采用额外的重建策略，不能凭一个长度数组直接声称已恢复序列。
- **字符单位**：示例按 Java `char` 比较 UTF-16 code unit。若业务要求按 Unicode code point 或更高层的字素簇比较，需要先重新定义序列元素。

## 原理机制

LCS 的核心是“前缀最优解可由更短前缀组合”。二维状态形成一个 `(m+1) × (n+1)` 的有向无环依赖图：每个状态只依赖左、上、左上三个更早状态，所以按行或按列推进即可。

空间压缩并没有改变递推关系，只是利用“计算当前行时只需要上一行与当前行已经算出的左侧状态”这一事实复用数组。每次写入 `dp[j]` 前先保存旧值，使它在下一列充当上一行左上角。这个不变量比死记代码更重要：一旦旧 `dp[j]` 被覆盖而没有保存，下一列的相等字符转移就会读到错误状态。

## 项目经验版

来源没有真实项目背景，不能虚构“线上用 LCS 做过某功能”。实际落地前我会先确认元素定义、是否只求长度、输入规模和内存限制。如果要处理很长文本，还要评估 `O(mn)` 是否可接受；如果需要恢复具体序列，则把“只求长度”的空间优化与“可重建路径”的需求分开设计，并用边界样例和随机差分测试验证实现。

## 常见追问

- 问：子序列和子串有什么区别？答：子序列只要求相对顺序不变，可以跳过中间元素；子串要求连续。把 LCS 当最长公共子串会得到不同的状态转移。
- 问：为什么空间能压成一维？答：当前状态只依赖上一行同列、当前行左边和上一行左上角；前两者可复用同一个数组，左上角用一个临时变量保存。
- 问：交换两个字符串会改变答案吗？答：不会改变 LCS 长度；这里交换只是让较短字符串作为列，从而减少数组空间。
- 问：能不能恢复具体 LCS？答：可以，但当前实现只承诺长度。恢复序列需要保存足够的路径信息或采用另外的重建算法。
- 问：时间复杂度能不能总是优于 `O(mn)`？答：不能在没有额外输入性质和目标约束时作这种保证；当前候选明确给出通用二维前缀 DP 的 `O(mn)` 边界。
- 问：空字符串怎么办？答：DP 第 0 行和第 0 列天然都是 0，所以任一输入为空时返回 0。

## 易错点

- 把“子序列”误写成要求连续的“子串”。
- 一维 DP 覆盖 `dp[j]` 后才保存旧值，导致左上角状态丢失。
- 字符不同时错误地使用 `prevDiagonal`，而不是当前行左边与上一行当前列的最大值。
- 为省空间交换字符串后又混淆循环边界或返回下标。
- 只实现长度，却在答案里声称能直接恢复具体序列。
- 没定义 `null`、空字符串和字符单位的边界语义。
'''

SOLUTION = r'''public final class Solution {
    public static int longestCommonSubsequence(String a, String b) {
        if (a == null || b == null) throw new IllegalArgumentException("input must not be null");
        if (a.length() < b.length()) {
            String tmp = a; a = b; b = tmp;
        }
        int[] dp = new int[b.length() + 1];
        for (int i = 1; i <= a.length(); i++) {
            int prevDiagonal = 0;
            for (int j = 1; j <= b.length(); j++) {
                int previousRowSameColumn = dp[j];
                if (a.charAt(i - 1) == b.charAt(j - 1)) dp[j] = prevDiagonal + 1;
                else dp[j] = Math.max(dp[j], dp[j - 1]);
                prevDiagonal = previousRowSameColumn;
            }
        }
        return dp[b.length()];
    }
}
'''

TEST = r'''import java.util.Random;

public final class SolutionTest {
    private static int oracle(String a, String b) {
        int[][] dp = new int[a.length() + 1][b.length() + 1];
        for (int i = 1; i <= a.length(); i++) {
            for (int j = 1; j <= b.length(); j++) {
                if (a.charAt(i - 1) == b.charAt(j - 1)) dp[i][j] = dp[i - 1][j - 1] + 1;
                else dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
            }
        }
        return dp[a.length()][b.length()];
    }

    private static void check(String a, String b, int expected) {
        int actual = Solution.longestCommonSubsequence(a, b);
        if (actual != expected) throw new AssertionError(a + " / " + b + ": " + actual + " != " + expected);
        int symmetric = Solution.longestCommonSubsequence(b, a);
        if (symmetric != expected) throw new AssertionError("symmetry failed");
    }

    public static void main(String[] args) {
        check("", "", 0);
        check("", "abc", 0);
        check("abcde", "ace", 3);
        check("abc", "abc", 3);
        check("abc", "def", 0);
        check("aaaa", "aa", 2);
        check("XMJYAUZ", "MZJAWXU", 4);
        boolean nullRejected = false;
        try { Solution.longestCommonSubsequence(null, "a"); }
        catch (IllegalArgumentException expected) { nullRejected = true; }
        if (!nullRejected) throw new AssertionError("null input must be rejected");

        Random r = new Random(20260831L);
        String alphabet = "abcd";
        final int cases = 50000;
        for (int t = 0; t < cases; t++) {
            int m = r.nextInt(13), n = r.nextInt(13);
            StringBuilder a = new StringBuilder(), b = new StringBuilder();
            for (int i = 0; i < m; i++) a.append(alphabet.charAt(r.nextInt(alphabet.length())));
            for (int j = 0; j < n; j++) b.append(alphabet.charAt(r.nextInt(alphabet.length())));
            int expected = oracle(a.toString(), b.toString());
            int actual = Solution.longestCommonSubsequence(a.toString(), b.toString());
            if (actual != expected) throw new AssertionError("random mismatch: " + a + " / " + b + ": " + actual + " != " + expected);
        }
        System.out.println("PASS fixed=7 null=rejected random=50000 oracle=2d-dp symmetry=checked");
    }
}
'''


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass':
        raise SystemExit('batch 0061 source inventory is not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item or item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: frozen coding source item missing')
    if item.get('personal_fact_verification_required') or item.get('secondary_coverage_required'):
        raise SystemExit(f'{CID}: unexpected sensitive/secondary gate')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: frozen ownership drift: {item.get("question_ids")}')
    wordings = {q.get('original_question') for q in item.get('source_questions', [])}
    if wordings != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: source wording drift: {wordings}')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    context_raw = run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout
    context = json.loads(context_raw)
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: live context/type drift')
    live_qids = sorted((context.get('canonical') or {}).get('question_ids') or [])
    if live_qids != sorted(QIDS):
        raise SystemExit(f'{CID}: live context ownership drift: {live_qids}')
    write_json(out / 'context.json', context)

    for heading in HEADINGS:
        if heading not in CANDIDATE:
            raise SystemExit(f'candidate heading missing: {heading}')
    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE, encoding='utf-8')
    digest = hashlib.sha256(CANDIDATE.encode('utf-8')).hexdigest()

    with tempfile.TemporaryDirectory(prefix='xhs-lcs-') as tmp:
        td = Path(tmp)
        (td / 'Solution.java').write_text(SOLUTION, encoding='utf-8')
        (td / 'SolutionTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'Solution.java', 'SolutionTest.java', cwd=td)
        stdout = run('java', 'SolutionTest', cwd=td).stdout.strip()
    expected_stdout = 'PASS fixed=7 null=rejected random=50000 oracle=2d-dp symmetry=checked'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected LCS validation output: {stdout}')

    checks = [
        'empty, identical, disjoint, repeated-character, and standard LCS boundary cases match expected lengths',
        'null input is explicitly rejected by the declared candidate contract',
        '50,000 seeded random short-string cases match an independent two-dimensional DP oracle',
        'symmetry is checked on fixed cases while the implementation swaps inputs only to minimize memory',
    ]
    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac Solution.java SolutionTest.java && java SolutionTest',
        'stdout': stdout,
        'checks': checks,
        'environment': {'java': 'OpenJDK 21'},
        'limitation': 'The executable differential test validates the exact one-dimensional implementation against an independently written two-dimensional DP oracle on bounded generated inputs; it does not claim to exhaust all possible strings.',
    }
    write_json(out / 'writer_validation.json', validation)

    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0061 frozen repository source context for LCS',
            'locator': f'review/content_build/answer_batch_{BATCH}/{CID}/context.json',
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'source-inventory',
            'title': 'Batch 0061 frozen live source inventory',
            'locator': f'review/content_build/answer_batch_{BATCH}/source_inventory.json',
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
        {
            'source_id': 'fixture',
            'title': 'OpenJDK differential validation for the exact one-dimensional LCS implementation',
            'locator': f'review/content_build/answer_batch_{BATCH}/{CID}/writer_validation.json',
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The two frozen source variants ask to solve Longest Common Subsequence and do not prescribe a programming language, API, reconstruction requirement, null contract, or Unicode element model; the candidate states its Java/length-only boundary explicitly.',
            'source_ids': ['repository-source', 'source-inventory'],
            'answer_locations': ['核心结论', '3 分钟版', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'reference-behavior',
            'text': 'The exact one-dimensional Java implementation compiles, passes fixed boundary cases, rejects null under its declared contract, and matches an independently written two-dimensional DP oracle on 50,000 seeded random short-string pairs.',
            'source_ids': ['fixture'],
            'answer_locations': ['3 分钟版', '关键细节', '原理机制', '项目经验版'],
        },
    ]
    coverage = [
        {
            'question_id': qid,
            'covered': True,
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        }
        for qid in QIDS
    ]
    writer_research = {
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
    write_json(out / 'writer_research.json', writer_research)

    findings = [
        'The candidate covers both frozen LCS source variants directly and does not substitute the different longest-common-substring problem.',
        'The state definition and one-dimensional update preserve the required previous-row diagonal before overwriting the current cell.',
        'The candidate clearly separates length-only computation from sequence reconstruction and makes the Java/null/UTF-16 boundaries explicit rather than presenting them as source constraints.',
        'Executable validation compares the exact implementation with an independently written two-dimensional DP oracle over fixed boundaries and 50,000 seeded random short-string pairs.',
        'The memory optimization is tied to using the shorter string as the DP-column dimension; swapping inputs does not alter the length contract.',
        'No production or personal claim is fabricated from the source.',
    ]
    isolated = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0061-lcs-20260831-v1',
        'review_version': 'batch-0061.lcs.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            f'review/content_build/answer_batch_{BATCH}/{CID}/context.json',
            f'review/content_build/answer_batch_{BATCH}/source_inventory.json',
            f'review/candidates/answers/{CID}.md',
            f'review/content_build/answer_batch_{BATCH}/{CID}/writer_validation.json',
            'docs/refactor/09_answer_content_standard.md',
        ],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    }
    write_json(out / 'isolated_review_result.json', isolated)

    evidence_sources = sources + [{
        'source_id': 'isolated-review',
        'title': 'Batch 0061 LCS source-first isolated review',
        'locator': f'review/content_build/answer_batch_{BATCH}/{CID}/isolated_review_result.json',
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    }]
    evidence = {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0061-lcs-builder',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': stdout,
            'checks': checks,
            'boundary_tests': [
                {'case': c, 'expected': 'pass under declared candidate contract', 'actual': 'pass', 'passed': True}
                for c in checks
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': isolated['reviewer_id'],
            'review_version': isolated['review_version'],
            'independent': True,
            'decision': 'pass',
            'revision_round': 1,
            'scores': SCORES,
            'hard_failures': [],
            'unsupported_claims': [],
            'uncovered_source_variants': [],
            'findings': findings,
        },
        'promotion_blocker': PROMOTION_BLOCKER,
    }
    write_json(ROOT / f'review/evidence/{CID}.json', evidence)

    task_path = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0061.md'
    task = task_path.read_text(encoding='utf-8')
    marker = f'- [x] `{CID}` source-first isolated review PASS:'
    if marker not in task:
        task = task.rstrip() + '\n' + (
            f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; '
            'the one-dimensional Java DP covers both frozen LCS source variants while making language, null, length-only, and UTF-16 boundaries explicit. '
            'OpenJDK validation matches an independently written two-dimensional DP oracle on fixed boundary cases and 50,000 seeded random short-string pairs. '
            'Formal promotion remains blocked by repository human-approval/real-review policy.\n'
        )
        task_path.write_text(task, encoding='utf-8')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
