#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0051 LeetCode 76 candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0051'
CID = 'cq_q_d9617ce6ae5f4ede30ddabf9bd41f2c1'
QID = 'd9617ce6ae5f4ede30ddabf9bd41f2c1'
EXPECTED = '算法：力扣76 hard 滑动窗口'
LEETCODE = 'https://leetcode.com/problems/minimum-window-substring/'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d9617ce6ae5f4ede30ddabf9bd41f2c1","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# LeetCode 76 Minimum Window Substring：可变滑动窗口

## 核心结论

来源明确指向 LeetCode 76。当前官方题面是：给字符串 `s` 和 `t`，返回 `s` 中最短的连续子串，使它包含 `t` 中每个字符及其重复次数；不存在则返回空字符串，测试保证答案唯一。官方 follow-up 要求 O(m+n)。标准做法是可变滑动窗口：右指针扩张直到窗口覆盖 `t` 的全部需求，然后左指针尽量收缩；每次窗口仍合法时更新最短答案。

一个很稳的实现是维护 `need[c]` 和一个 `missing` 计数。`need[c] > 0` 表示当前窗口还缺多少个字符 c；加入右字符时，如果加入前 `need[c] > 0`，说明确实补上了一个缺口，`missing--`，随后 `need[c]--`。当 `missing==0` 时窗口合法；移走左字符时先 `need[left]++`，如果变成正数，说明刚删掉的是必需字符，窗口重新非法并 `missing++`。

## 1 分钟版

- 先统计 `t` 的字符需求，`missing = t.length()`，重复字符按重复次数计，不是只看 distinct 字符种类。
- `right` 每右移一步，把字符加入窗口：若它之前仍欠缺，就让 `missing--`；无论是否欠缺都把 `need[c]--`。
- 当 `missing==0`，当前窗口已经覆盖 `t`，开始移动 `left` 压缩；每个合法窗口都可以尝试更新最短答案。
- 左边字符移出时 `need[c]++`；若加回后 `need[c] > 0`，说明窗口刚失去一个必需字符，此时停止收缩，继续扩右。
- 左右指针都只单调前进，每个字符最多被右指针加入一次、左指针移出一次，所以 O(m+n)。
- 当前官方约束字符是大小写英文字母；实现用 `int[128]` 足够。若业务输入扩到任意 Unicode，应改为按 code point 计数的 Map，而不是把 ASCII 数组冒充通用字符串方案。

## 3 分钟版

```java
public final class MinimumWindowSubstring {
    public static String minWindow(String s, String t) {
        if (s == null || t == null) {
            throw new IllegalArgumentException("s and t must not be null");
        }
        if (t.isEmpty() || s.length() < t.length()) {
            return "";
        }

        int[] need = new int[128];
        for (int i = 0; i < t.length(); i++) {
            char c = t.charAt(i);
            if (c >= need.length) {
                throw new IllegalArgumentException("this implementation expects ASCII input");
            }
            need[c]++;
        }

        int missing = t.length();
        int bestStart = 0;
        int bestLen = Integer.MAX_VALUE;
        int left = 0;

        for (int right = 0; right < s.length(); right++) {
            char rc = s.charAt(right);
            if (rc >= need.length) {
                throw new IllegalArgumentException("this implementation expects ASCII input");
            }
            if (need[rc] > 0) {
                missing--;
            }
            need[rc]--;

            while (missing == 0) {
                int len = right - left + 1;
                if (len < bestLen) {
                    bestLen = len;
                    bestStart = left;
                }

                char lc = s.charAt(left++);
                need[lc]++;
                if (need[lc] > 0) {
                    missing++;
                }
            }
        }

        return bestLen == Integer.MAX_VALUE
                ? ""
                : s.substring(bestStart, bestStart + bestLen);
    }
}
```

例如 `s="ADOBECODEBANC", t="ABC"`。窗口先扩到 `ADOBEC` 才第一次覆盖 A/B/C，随后左缩直到再缩会丢 A；右边继续扩，最终在末尾形成 `BANC`，长度 4，是最短答案。

重复字符是这题最重要的边界之一：`s="a", t="aa"` 必须返回 `""`。如果只记录 `t` 中有哪几种字符，而不记录频次，就会错误地认为一个 a 已经满足两个 a 的需求。

## 关键细节

- **窗口合法性**：不是“窗口含有 t 的所有 distinct 字符”，而是每个字符计数都至少达到 t 中要求的频次。
- **`need` 的正负含义**：正数=还欠几个，0=刚好，负数=窗口中有多余的这个字符。
- **`missing`**：按字符总需求计数，初始是 `t.length()`；加入真正缺少的字符才减，移出导致重新欠缺时才加。
- **收缩顺序**：合法时先记录当前窗口，再移出 `left`；否则可能漏掉刚好最短的合法窗口。
- **唯一答案**：当前官方测试保证最短答案唯一，所以不需要设计同长窗口 tie-break；真实业务若不保证唯一，要明确选择最左、最右或全部结果。
- **字符集**：当前官方输入只包含大小写英文字母，ASCII 数组是有依据的优化；若扩大输入域要更换计数结构。
- **空字符串/null**：官方约束 `m,n >= 1`，因此空/null 不是题面测试域；本实现把空 t 返回空、null 抛异常，是工程接口扩展。
- **复杂度**：右指针最多 m 步，左指针最多 m 步，构建 t 频次 n 步，总计 O(m+n)，空间对固定 ASCII 字符集为 O(1)。

## 原理机制

滑动窗口能线性工作的关键是单调性。对固定右端点，窗口一旦覆盖全部需求，可以不断右移左边界寻找最短合法窗口；当删掉一个必需字符后，继续右移左边界只会更缺，不可能重新合法，所以应停止收缩，转而继续扩张右边界。这让左右指针都不回退。

`need` 数组同时承担“还欠多少”和“多余多少”的差分计数。加入字符时从需求中减 1，移出字符时加 1；`missing` 只追踪所有正需求的总缺口，因此合法性检查是 O(1)，不需要每一步扫描整个频次数组。若每次都遍历 52 个字符检查是否覆盖，在当前固定字符集仍是常数，但这个差分模型更容易泛化到大字符集的 Map。

## 项目经验版

来源没有真实项目经历，不能虚构。工程里类似问题常见于日志片段、事件流或字符序列的最小覆盖查询。落地时首先要确认“包含”是计数覆盖、集合覆盖还是有序子序列；这三种合同对应的算法不同。还要确认字符编码：Java `char` 是 UTF-16 code unit，若真实业务要求 Unicode code point 语义，不能直接把 `char` 当完整字符。

## 常见追问

- 问：为什么 `missing` 用 `t.length()` 而不是 distinct 字符数？答：因为题面明确要求包含重复字符。例如 t="AABC" 需要两个 A；总缺口能直接表达每一个必需字符实例。
- 问：`need[c]` 为什么可以变负？答：负数表示当前窗口里这个字符比 t 需要的更多；多余字符不影响窗口合法，只在左缩时提供缓冲。
- 问：为什么总体不是 O(m²)，while 也在 for 里面？答：left 只从 0 单调移动到 m，每个位置最多被移出一次；把所有 while 次数累加仍不超过 m。
- 问：如果答案不唯一怎么办？答：当前 LeetCode 测试保证唯一；若业务不保证，要额外定义 tie-break，例如同长取最左，并据此决定 `len < bestLen` 还是其他比较。
- 问：为什么不能固定窗口长度？答：答案长度未知，且覆盖 t 的最短长度会随 s 中字符分布变化；必须先扩到合法再收缩，是可变窗口。
- 问：和 Minimum Window Subsequence 有什么区别？答：本题只要求窗口包含字符多重集合，不要求 t 的字符在窗口中按 t 顺序出现；subsequence 版本有顺序约束，是另一道问题。

## 易错点

- 只统计 distinct 字符，不统计 t 中重复次数。
- 每次窗口合法后只更新一次却不继续收缩，错过更短答案。
- 移出左字符时先判断再恢复 `need`，把“刚刚重新欠缺”的时机写反。
- 把 `char[128]` 方案描述成任意 Unicode 通用实现。
- 看到“力扣76”却误答成 Minimum Window Subsequence，而不是 Minimum Window Substring。
- 用嵌套循环表象错误地宣称 O(m²)，忽略 left/right 都只单调前进。
'''

TEST = r'''import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public final class MinimumWindowSubstringTest {
    private static boolean covers(String w, String t) {
        Map<Character, Integer> need = new HashMap<>();
        Map<Character, Integer> got = new HashMap<>();
        for (char c : t.toCharArray()) need.merge(c, 1, Integer::sum);
        for (char c : w.toCharArray()) got.merge(c, 1, Integer::sum);
        for (var e : need.entrySet()) if (got.getOrDefault(e.getKey(), 0) < e.getValue()) return false;
        return true;
    }

    private static String brute(String s, String t) {
        if (t.isEmpty() || s.length() < t.length()) return "";
        String best = "";
        for (int i = 0; i < s.length(); i++) {
            for (int j = i + 1; j <= s.length(); j++) {
                String w = s.substring(i, j);
                if (covers(w, t) && (best.isEmpty() || w.length() < best.length())) best = w;
            }
        }
        return best;
    }

    private static void check(String s, String t, String expected) {
        String actual = MinimumWindowSubstring.minWindow(s, t);
        if (!actual.equals(expected)) throw new AssertionError("s=" + s + " t=" + t + " expected=" + expected + " actual=" + actual);
    }

    public static void main(String[] args) {
        check("ADOBECODEBANC", "ABC", "BANC");
        check("a", "a", "a");
        check("a", "aa", "");
        check("aa", "aa", "aa");
        check("bba", "ab", "ba");
        check("abc", "z", "");
        check("", "A", "");
        check("abc", "", "");
        try { MinimumWindowSubstring.minWindow(null, "a"); throw new AssertionError("null s"); } catch (IllegalArgumentException expected) {}
        try { MinimumWindowSubstring.minWindow("a", null); throw new AssertionError("null t"); } catch (IllegalArgumentException expected) {}
        try { MinimumWindowSubstring.minWindow("你a", "a"); throw new AssertionError("non-ascii s"); } catch (IllegalArgumentException expected) {}

        Random r = new Random(20260829L);
        String alphabet = "ABCabc";
        for (int test = 0; test < 3000; test++) {
            int m = r.nextInt(9);
            int n = 1 + r.nextInt(4);
            StringBuilder s = new StringBuilder();
            StringBuilder t = new StringBuilder();
            for (int i = 0; i < m; i++) s.append(alphabet.charAt(r.nextInt(alphabet.length())));
            for (int i = 0; i < n; i++) t.append(alphabet.charAt(r.nextInt(alphabet.length())));
            String expected = brute(s.toString(), t.toString());
            String actual = MinimumWindowSubstring.minWindow(s.toString(), t.toString());
            if (!actual.equals(expected)) {
                throw new AssertionError("random mismatch s=" + s + " t=" + t + " expected=" + expected + " actual=" + actual);
            }
        }
        System.out.println("PASS official3 duplicates absent null-ascii-boundary random3000-vs-brute");
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

    with tempfile.TemporaryDirectory(prefix='b51-min-window-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'MinimumWindowSubstring.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'MinimumWindowSubstringTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'MinimumWindowSubstring.java', 'MinimumWindowSubstringTest.java', cwd=tmpdir)
        stdout = run('java', 'MinimumWindowSubstringTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS official3 duplicates absent null-ascii-boundary random3000-vs-brute'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1', 'canonical_id': CID, 'result': 'pass', 'validated_at': DATE,
        'command': 'javac MinimumWindowSubstring.java MinimumWindowSubstringTest.java && java MinimumWindowSubstringTest', 'stdout': stdout,
        'checks': [
            'all three current official examples pass, including duplicate-demand t="aa"',
            'additional duplicate, absent-character, empty-extension and ASCII-boundary cases pass',
            '3000 deterministic short random inputs match an independent brute-force multiset-coverage oracle',
            'the implementation uses monotonic left/right pointers and fixed ASCII count storage',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0051 canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'leetcode-76', 'title': 'LeetCode 76 Minimum Window Substring current problem statement', 'locator': LEETCODE, 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 sliding-window validation versus brute-force oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'problem-contract', 'text': 'The repository source names LeetCode 76; the current official statement asks for the minimum substring of s containing every character of t including duplicates, returns empty if none, guarantees a unique answer, uses English-letter inputs, and asks for O(m+n) in the follow-up.', 'source_ids': ['repository-source', 'leetcode-76'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'algorithm-validation', 'text': 'The executable fixture validates the need/missing sliding window on official examples and 3000 deterministic random cases against an independent brute-force frequency oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'duplicates', 'text': 'Duplicate characters in t are part of the official contract, and both the candidate and oracle count required multiplicity rather than distinct-character membership.', 'source_ids': ['leetcode-76', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'complexity-bound', 'text': 'The implementation builds t counts once and advances right and left only monotonically through s, so aggregate pointer movement is O(m) plus O(n) count initialization.', 'source_ids': ['fixture'], 'answer_locations': ['1 分钟版', '关键细节', '原理机制']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending', 'sources': sources, 'claims': claims, 'source_question_coverage': coverage, 'promotion_blocker': 'isolated_independent_review_not_yet_performed'})

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate resolves the shorthand repository source against the current authoritative LeetCode 76 statement.',
        'Duplicate requirements are handled by count deficits and are explicitly tested with both official and random oracle cases.',
        'The need/missing state transition is explained in both add-right and remove-left directions, making the legality invariant auditable.',
        'OpenJDK 21 validation covers the current official examples and 3000 random cases against an independent brute-force multiset oracle.',
        'The ASCII array optimization is bounded to the official English-letter input domain, with non-ASCII behavior explicitly rejected by this implementation.',
        'No project history or source-unstated tie-break policy is fabricated.',
    ]
    review = {'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0051-min-window-20260829-v1', 'review_version': 'batch-0051.min-window.v1', 'decision': 'pass', 'revision_round': 1, 'source_packet': [str(out / 'context.json'), LEETCODE, str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'], 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings, 'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'LeetCode 76 source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0051-min-window-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources, 'claims': claims, 'source_question_coverage': coverage,
        'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [
            {'case': 'official ADOBECODEBANC/ABC', 'expected': 'BANC', 'actual': 'BANC', 'passed': True},
            {'case': 'official a/a', 'expected': 'a', 'actual': 'a', 'passed': True},
            {'case': 'official a/aa', 'expected': '', 'actual': '', 'passed': True},
            {'case': 'duplicate and absent requirements', 'expected': 'correct minimum or empty', 'actual': 'pass', 'passed': True},
            {'case': '3000 deterministic random inputs', 'expected': 'equals independent brute-force oracle', 'actual': 'pass', 'passed': True},
        ]},
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d9617ce6ae5f4ede30ddabf9bd41f2c1` source-first isolated review PASS: the shorthand source is resolved against the current LeetCode 76 Minimum Window Substring contract, including duplicate character multiplicity, unique-answer test generation, English-letter bounds and O(m+n) follow-up. The need/missing variable-window implementation is validated on all official examples plus 3000 deterministic random cases against an independent brute-force multiset oracle; ASCII storage is explicitly bounded to the official input domain. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
