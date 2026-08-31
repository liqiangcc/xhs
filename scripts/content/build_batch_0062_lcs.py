#!/usr/bin/env python3
"""Build the source-bounded Batch 0062 longest-common-subsequence candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_6a7c7f58ad4a4828e2c984b668d7ba32'
QIDS = ['6a7c7f58ad4a4828e2c984b668d7ba32', 'b49c67887ac2b8fed060d5c61351f0c5']
EXPECTED_VARIANTS = {
    '算法：最长公共子序列（Dynamic Programming）？',
    '算法：最长公共子序列',
}
EXPECTED_STDOUT = 'PASS fixed=8 random=30000 oracle=2d-dp symmetry=preserved empty=0 repeated=preserved'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_6a7c7f58ad4a4828e2c984b668d7ba32","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 最长公共子序列（LCS）：动态规划实现

## 核心结论

来源只要求“最长公共子序列 / Dynamic Programming”，没有给语言、输入 API、是否要求恢复具体序列，也没有定义 `null`。这里采用一个明确且可执行的最小契约：输入两个非 `null` Java `String`，返回它们最长公共子序列的**长度**；空字符串合法并返回 `0`，`null` 视为调用错误并抛 `IllegalArgumentException`。实现使用动态规划，并把二维 DP 压缩成一维数组：时间复杂度 `O(m * n)`，额外 DP 空间 `O(min(m, n))`。

## 1 分钟版

- 先区分“子序列”和“子串”：LCS 允许跳过字符，但必须保持相对顺序，不要求连续。
- 状态可以理解为 `dp[i][j]`：两个前缀 `a[0..i)`、`b[0..j)` 的 LCS 长度。
- 若末尾字符相等，`dp[i][j] = dp[i-1][j-1] + 1`；否则只能舍弃一边的末尾字符，取 `max(dp[i-1][j], dp[i][j-1])`。
- 只求长度时可以把二维表压成一行；更新时必须保存“左上角旧值” `prevDiag`，否则会把本轮新值错误当成上一轮状态。
- 为了降低空间，把较短字符串放到 DP 数组这一维，额外空间就是 `O(min(m, n))`。

## 3 分钟版

先写二维递推更容易说明正确性：

```text
如果 a[i - 1] == b[j - 1]:
    dp[i][j] = dp[i - 1][j - 1] + 1
否则:
    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
```

只返回长度时，可以把它压成一维：

```java
public final class LongestCommonSubsequence {
    private LongestCommonSubsequence() {}

    public static int lcsLength(String first, String second) {
        if (first == null || second == null) {
            throw new IllegalArgumentException("inputs must be non-null");
        }

        String rows = first;
        String cols = second;
        if (rows.length() < cols.length()) {
            String tmp = rows;
            rows = cols;
            cols = tmp;
        }

        int[] dp = new int[cols.length() + 1];
        for (int i = 1; i <= rows.length(); i++) {
            int prevDiag = 0;
            for (int j = 1; j <= cols.length(); j++) {
                int oldUp = dp[j];
                if (rows.charAt(i - 1) == cols.charAt(j - 1)) {
                    dp[j] = prevDiag + 1;
                } else {
                    dp[j] = Math.max(dp[j], dp[j - 1]);
                }
                prevDiag = oldUp;
            }
        }
        return dp[cols.length()];
    }
}
```

这里 `dp[j]` 在覆盖前表示二维表里的“上方”，`dp[j - 1]` 已经是当前行的“左侧”，`prevDiag` 保存覆盖前的“左上角”。因此一维压缩没有改变原递推依赖，只是复用了存储。

## 关键细节

- **状态语义要先固定**：`dp[i][j]` 表示两个前缀的 LCS 长度，而不是“必须以当前字符结尾”的长度。
- **相等时为什么走左上角 + 1**：当前两个末尾字符相等，可以把这个字符接到更短前缀的公共子序列后面。
- **不等时为什么取上/左最大值**：一个最优公共子序列不可能同时依赖两个不同的末尾字符，至少要舍弃其中一边的当前末尾，所以比较两种前缀选择。
- **一维更新方向**：这里 `j` 从小到大，因为 `dp[j - 1]` 要代表当前行左侧；同时必须单独保存覆盖前的 `dp[j - 1]`，也就是 `prevDiag`。
- **重复字符不能去重**：LCS 比较的是位置和顺序，不是字符集合；例如 `"aaaa"` 与 `"aa"` 的答案是 `2`。
- **只求长度，不恢复序列**：如果题目要求输出一个实际 LCS，需要额外保存路径信息、保留二维表回溯，或使用更复杂的低空间恢复算法；不能从这一个最终整数直接恢复路径。
- **Java `char` 边界**：该实现按 UTF-16 code unit 比较 `String.charAt`。如果业务契约要求按 Unicode code point 处理，需要先把字符串转换到 code point 序列后再做同样的 DP。

## 原理机制

LCS 的核心是“最优解由更短前缀的最优解组成”。设两个前缀的最后字符分别为 `x` 和 `y`：当 `x == y` 时，可以把这个共同字符加入 `dp[i-1][j-1]` 的解；当 `x != y` 时，任何公共子序列都不能同时把两个不同的末尾字符作为同一个末尾匹配，因此最优解一定包含在“去掉 `x`”或“去掉 `y`”这两个子问题之一，取两者最大值即可。

二维表里每个状态只依赖“上、左、左上”三个位置，所以只求长度时可以滚动压缩。一维版本真正需要维护的不变量是：进入第 `j` 列更新前，`dp[j]` 仍是上一行的上方值，`dp[j - 1]` 已是当前行左侧值，`prevDiag` 是上一行左上角值。只要这个不变量不被破坏，压缩后的结果和二维 DP 一致。

## 项目经验版

来源没有真实业务项目、字符串规模、字符集或内存约束，不能虚构“线上就是这样做”。真实落地时我会先确认：只需要长度还是要恢复序列、字符串最大长度、是否允许 `null`、字符语义是 UTF-16 code unit 还是 Unicode code point。如果输入可能很长，`O(m*n)` 时间本身可能先成为瓶颈；空间压缩只能解决 DP 表内存，不能把二次时间复杂度变成线性。

## 常见追问

- 问：LCS 和最长公共子串有什么区别？答：LCS 只要求顺序一致，可以不连续；最长公共子串要求连续，因此状态转移不同。
- 问：为什么字符不相等时不是 `dp[i-1][j-1]`？答：不相等时仍可能通过只舍弃一边末尾保留更长的公共子序列，所以要比较“上”和“左”。
- 问：为什么一维数组从左往右更新还能正确？答：因为当前状态需要当前行左侧 `dp[j-1]`，而上一行左上角另存到 `prevDiag`；若不保存旧值就会破坏依赖。
- 问：能不能把空间做到 `O(1)`？答：一般的 LCS 长度递推需要保留一整行前缀状态，普通 DP 的低空间边界是 `O(min(m,n))`，不是常数空间。
- 问：如果要输出具体 LCS 怎么办？答：最直接是保留二维 DP 后从右下角回溯；若内存受限，可以再讨论分治式恢复方案，但那是额外契约。
- 问：为什么重复字符不能 `distinct`？答：两个相同字符出现在不同位置时可以分别参与匹配，LCS 是序列位置问题，不是集合交集。

## 易错点

- 把“子序列”误写成必须连续的“子串”。
- 二维压一维后忘记保存左上角旧值，导致相等分支读取到本轮已更新状态。
- 不相等时只从某一个方向转移，漏掉另一侧前缀可能更优的情况。
- 对重复字符先去重，破坏序列位置语义。
- 题目只问长度，却擅自承诺能从一维最终状态直接恢复具体序列。
- 没声明 `null`、Unicode 字符单位和规模边界，却把某一种实现选择说成原题既定条件。
'''

JAVA_IMPL = r'''import java.util.Objects;

public final class LongestCommonSubsequence {
    private LongestCommonSubsequence() {}

    public static int lcsLength(String first, String second) {
        if (first == null || second == null) {
            throw new IllegalArgumentException("inputs must be non-null");
        }
        String rows = first;
        String cols = second;
        if (rows.length() < cols.length()) {
            String tmp = rows;
            rows = cols;
            cols = tmp;
        }
        int[] dp = new int[cols.length() + 1];
        for (int i = 1; i <= rows.length(); i++) {
            int prevDiag = 0;
            for (int j = 1; j <= cols.length(); j++) {
                int oldUp = dp[j];
                if (rows.charAt(i - 1) == cols.charAt(j - 1)) {
                    dp[j] = prevDiag + 1;
                } else {
                    dp[j] = Math.max(dp[j], dp[j - 1]);
                }
                prevDiag = oldUp;
            }
        }
        return dp[cols.length()];
    }
}
'''

JAVA_TEST = r'''import java.util.Random;

public final class LongestCommonSubsequenceWriterTest {
    private static final Random RNG = new Random(0x62006A7CL);
    private static final char[] ALPHABET = {'a','b','c','d'};

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

    private static void check(String a, String b, int expected, String label) {
        int actual = LongestCommonSubsequence.lcsLength(a, b);
        if (actual != expected) throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        int reversed = LongestCommonSubsequence.lcsLength(b, a);
        if (reversed != expected) throw new AssertionError(label + " symmetry expected=" + expected + " actual=" + reversed);
    }

    private static String randomString(int maxLen) {
        int len = RNG.nextInt(maxLen + 1);
        StringBuilder sb = new StringBuilder(len);
        for (int i = 0; i < len; i++) sb.append(ALPHABET[RNG.nextInt(ALPHABET.length)]);
        return sb.toString();
    }

    public static void main(String[] args) {
        check("", "", 0, "both-empty");
        check("abc", "", 0, "one-empty");
        check("abcde", "ace", 3, "classic");
        check("abc", "abc", 3, "identical");
        check("abc", "def", 0, "disjoint");
        check("abc", "bac", 2, "cross-order");
        check("aaaa", "aa", 2, "repeated");
        check("XMJYAUZ", "MZJAWXU", 4, "nontrivial");
        boolean threw = false;
        try { LongestCommonSubsequence.lcsLength(null, "x"); } catch (IllegalArgumentException expected) { threw = true; }
        if (!threw) throw new AssertionError("null contract must throw IllegalArgumentException");

        for (int i = 0; i < 30000; i++) {
            String a = randomString(12);
            String b = randomString(12);
            int expected = oracle(a, b);
            check(a, b, expected, "random-" + i);
        }
        System.out.println("PASS fixed=8 random=30000 oracle=2d-dp symmetry=preserved empty=0 repeated=preserved");
    }
}
'''


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass':
        raise SystemExit('batch 0062 source inventory is not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item:
        raise SystemExit(f'{CID}: missing from source inventory')
    if item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: answer type drifted: {item.get("answer_type")}')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: frozen ownership drift: {item.get("question_ids")}')
    if {x.get('original_question') for x in item.get('source_questions', [])} != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: source wording drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context_path = out / 'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: context/type drift')
    canonical = context.get('canonical') or {}
    if sorted(canonical.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: context ownership drift')
    source_rows = context.get('source_questions') or []
    if len(source_rows) != 2 or {x.get('original_question') for x in source_rows} != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: source variants drift')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE, encoding='utf-8')
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()

    impl_path = out / 'LongestCommonSubsequence.java'
    test_path = out / 'LongestCommonSubsequenceWriterTest.java'
    impl_path.write_text(JAVA_IMPL, encoding='utf-8')
    test_path.write_text(JAVA_TEST, encoding='utf-8')
    proc = subprocess.run(
        ['bash', '-lc', 'javac LongestCommonSubsequence.java LongestCommonSubsequenceWriterTest.java && java LongestCommonSubsequenceWriterTest'],
        cwd=out,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f'{CID}: writer validation failed: {proc.stderr or proc.stdout}')
    stdout = proc.stdout.strip()
    if stdout != EXPECTED_STDOUT:
        raise SystemExit(f'{CID}: writer stdout drift: {stdout!r}')
    for class_file in out.glob('*.class'):
        class_file.unlink()

    validation_path = out / 'writer_validation.json'
    write_json(validation_path, {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'validator': 'batch_0062_lcs_writer_fixture',
        'command': 'javac LongestCommonSubsequence.java LongestCommonSubsequenceWriterTest.java && java LongestCommonSubsequenceWriterTest',
        'stdout': stdout,
        'checks': [
            'empty, identical, disjoint, crossing-order, repeated-character and nontrivial fixed cases',
            'explicit null-input contract throws IllegalArgumentException',
            '30,000 seeded random string pairs match an independent two-dimensional DP oracle',
            'symmetry lcs(a,b) == lcs(b,a) checked for every fixed and random case',
        ],
    })

    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'candidate_sha256': digest,
        'sources': [
            {
                'source_id': 'repository-source',
                'title': 'Batch 0062 frozen repository context for LCS',
                'locator': str(context_path),
                'source_type': 'repository_source_record',
                'checked_at': DATE,
            },
            {
                'source_id': 'writer-fixture',
                'title': 'LCS one-dimensional DP differential validation',
                'locator': str(validation_path),
                'source_type': 'executable_test_or_reproducible_experiment',
                'checked_at': DATE,
            },
        ],
        'claims': [
            {
                'claim_id': 'source-boundary',
                'text': 'Both frozen source variants ask for longest common subsequence / dynamic programming without prescribing language, concrete API, null handling or sequence reconstruction.',
                'source_ids': ['repository-source'],
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版'],
            },
            {
                'claim_id': 'implementation-behavior',
                'text': 'Under the declared Java length-only contract, the one-dimensional DP matches an independent two-dimensional DP oracle across fixed edge cases and 30,000 seeded random pairs and preserves symmetry.',
                'source_ids': ['writer-fixture'],
                'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问'],
            },
        ],
        'source_question_coverage': [
            {'question_id': qid, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问']}
            for qid in QIDS
        ],
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    line = (
        f'- [x] `{CID}` writer stage complete: both frozen LCS source Questions are covered by an explicit Java length-only DP contract; '
        'the executable fixture validates empty/identical/disjoint/repeated/cross-order boundaries plus 30,000 seeded random pairs against an independent two-dimensional DP oracle and symmetry checks. '
        'Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    )
    if line not in task:
        task_path.write_text(task + '\n' + line + '\n', encoding='utf-8')

    print(EXPECTED_STDOUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
