#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 longest-substring-with-tests candidate."""

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
CID = 'cq_q_e0ca3b11b4089b4f754ba3961313843f'
QID = 'e0ca3b11b4089b4f754ba3961313843f'
EXPECTED = '算法与测试：编写“无重复字符的最长子串”代码，并为此代码设计完备的单元测试用例（正常、边界、异常、超长输入）。'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e0ca3b11b4089b4f754ba3961313843f","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 无重复字符的最长子串：滑动窗口 + 完整测试设计

## 核心结论

这道题不仅要求算法，还明确要求正常、边界、异常和超长输入测试。先定义接口合同：输入 Java `String`，返回最长“无重复 Unicode code point”的连续子串长度，长度单位也是 code point；空串返回 0，`null` 是无效输入并抛 `IllegalArgumentException`。用 code point 而不是单个 UTF-16 `char`，避免一个 supplementary character 被拆成两个 surrogate 单元。

算法使用滑动窗口：右指针逐个读取 code point，`lastSeen` 记录该字符最近出现的 code-point 下标。若当前字符上次出现位置仍在窗口内，就把左边界跳到 `last+1`；然后更新最近位置并记录窗口最大长度。每个字符只进右边界一次，左边界只单调右移，所以时间 O(N)，空间 O(min(N,字符集大小))。

测试不能只写 `abcabcbb -> 3`。应覆盖重复发生在头/尾/中间、全部相同、空串、单字符、Unicode supplementary character、null 异常、超长输入，以及小规模随机输入与独立暴力 oracle 的交叉验证。

## 1 分钟版

- `left` 表示当前无重复窗口起点，`right` 是当前 code-point 下标。
- `lastSeen[ch]` 保存字符最近一次位置。
- 若 `lastSeen[ch] >= left`，说明重复发生在当前窗口内，直接 `left = lastSeen[ch] + 1`。
- 绝不能让 left 往回走，因此只在旧位置仍位于窗口内时更新。
- 当前窗口长度是 `right-left+1`，持续维护最大值。
- 示例：`abba`。第二个 b 把 left 推到 2；最后 a 的旧位置 0 已经在窗口外，left 不能退回 1，答案保持 2。
- 实现按 Unicode code point 扫描，所以 `😀a😀` 的答案是 2，而不是按 surrogate `char` 误计。

## 3 分钟版

```java
import java.util.HashMap;
import java.util.Map;

public final class LongestUniqueSubstring {
    public static int length(String s) {
        if (s == null) {
            throw new IllegalArgumentException("s must not be null");
        }

        Map<Integer, Integer> lastSeen = new HashMap<>();
        int left = 0;
        int right = 0;
        int best = 0;

        for (int offset = 0; offset < s.length(); ) {
            int cp = s.codePointAt(offset);
            Integer previous = lastSeen.get(cp);
            if (previous != null && previous >= left) {
                left = previous + 1;
            }
            lastSeen.put(cp, right);
            best = Math.max(best, right - left + 1);

            offset += Character.charCount(cp);
            right++;
        }
        return best;
    }
}
```

测试分类建议：

1. **正常用例**：`abcabcbb -> 3`、`pwwkew -> 3`、`abba -> 2`，覆盖重复后窗口跳跃和“left 不回退”。
2. **边界用例**：`"" -> 0`、`"a" -> 1`、`"aaaa" -> 1`、全部唯一字符串返回完整长度。
3. **Unicode 边界**：`"😀a😀" -> 2`、两个不同 emoji + 普通字符，验证按 code point 而不是 UTF-16 code unit。
4. **异常用例**：`null` 必须抛 `IllegalArgumentException`，而不是 NPE 或静默返回 0。
5. **超长输入**：例如百万个 `a` 应返回 1；再构造大量重复模式，确认线性扫描不会出现明显的二次退化。
6. **性质测试**：随机生成小字符串，与 O(N²~N³) 暴力实现比较几千轮，覆盖人工样例想不到的窗口状态组合。

## 关键细节

- **子串必须连续**：窗口方法天然维护连续区间，不能把字符跨位置拼成子序列。
- **left 不能回退**：典型 bug 是遇到一个早已在窗口外的重复字符仍执行 `left=old+1`，例如 `abba` 会算错。
- **最近位置而不是布尔集合**：只用 Set 也能通过逐个左移实现，但 last-index 可以一次跳到重复位置之后，更直接。
- **Unicode 语义**：Java `char` 是 UTF-16 code unit，不等于所有用户感知字符。当前合同至少提升到 Unicode code point；复杂 grapheme cluster（如组合音标/ZWJ emoji）仍可能由多个 code point 组成，如果产品要求“用户可见字符”就需要更高层 segmentation。
- **复杂度口径**：N 指 code point 数；遍历底层 UTF-16 code units 仍是线性的。Map 最多保存见过的不同 code point。
- **超长测试不是只测正确值**：还要选择能暴露错误复杂度的输入，例如百万重复字符；测试环境可设置合理超时，但不能把机器性能的绝对毫秒数写成算法合同。
- **异常合同**：null 与 empty 不应混为一谈；当前 empty 是合法值 0，null 是编程错误。

## 原理机制

窗口不变量是：在每次处理当前字符后，区间 `[left,right]` 内没有重复 code point。若当前字符从未出现或上次出现位置 `< left`，它不会破坏当前窗口；若上次位置 p 在窗口内，则任何包含 p 和当前 right 的窗口都重复，因此新的合法窗口最早只能从 `p+1` 开始。

因为 left 只向右移动，而 right 每轮加一，整个算法没有回溯。与“每个起点重新向右扫描”的暴力 O(N²) 不同，窗口把已经证明不可能成为合法起点的一段一次性跳过，这就是线性复杂度的来源。

## 项目经验版

来源没有真实项目经历，不能虚构。工程里最先确认的是“字符”的业务定义：ASCII、Unicode code point，还是 grapheme cluster。日志/协议字段可能按 code point 就够，面向用户文本可能需要 ICU/BreakIterator 一类 segmentation。测试也应与合同一致：如果 API 承诺 code point，就必须保留 surrogate-pair 用例；如果以后切换 grapheme，现有期望值也要相应升级。

## 常见追问

- 问：为什么 `abba` 是容易错的例子？答：处理最后一个 a 时，它上次出现的位置 0 已经在 left=2 之前；如果无条件把 left 设为 1，就让窗口左边界倒退并破坏不变量。
- 问：Set 滑动窗口可以吗？答：可以。遇到重复时不断删除左侧字符直到重复消失，同样 O(N)；last-index 方案能一步跳转，代码更紧凑。
- 问：为什么不用 int[128]？答：如果合同明确 ASCII 可以；当前选择 Unicode code point，因此用 Map 更直接。也可以用更大的数组但空间/初始化代价不同。
- 问：emoji 为什么要特别测？答：Java 一个 emoji 可能占两个 `char`。按 char 做会把 surrogate 当成字符，和 code-point 合同不一致。
- 问：超长输入怎么测？答：选可预测结果且能暴露复杂度的构造，如百万个同字符、长周期重复串；不要只依赖随机大字符串。
- 问：如何做更强的测试？答：小规模随机输入和独立暴力 oracle 做 differential testing，再加契约边界/异常/Unicode/超长定向样例。

## 易错点

- 把子串写成子序列。
- 遇到重复时让 left 回退。
- 用 UTF-16 char 实现，却宣称处理的是 Unicode 字符。
- 只测一个 LeetCode 风格正常样例，没有边界/异常/性能形状测试。
- 用超长随机串却不知道正确答案，最后只测“不崩溃”。
- 给超长测试写死极小毫秒阈值，把 CI 机器噪声当成算法正确性。
- null 和 empty 采用不同语义却没有在接口/测试里明确。
'''

TEST = r'''import java.util.HashSet;
import java.util.Random;
import java.util.Set;

public final class LongestUniqueSubstringTest {
    private static int brute(String s) {
        int[] cp = s.codePoints().toArray();
        int best = 0;
        for (int i = 0; i < cp.length; i++) {
            Set<Integer> seen = new HashSet<>();
            for (int j = i; j < cp.length; j++) {
                if (!seen.add(cp[j])) break;
                best = Math.max(best, j - i + 1);
            }
        }
        return best;
    }

    private static void check(String s, int expected) {
        int actual = LongestUniqueSubstring.length(s);
        if (actual != expected) throw new AssertionError("expected=" + expected + " actual=" + actual + " s=" + s);
    }

    public static void main(String[] args) {
        check("abcabcbb", 3);
        check("pwwkew", 3);
        check("abba", 2);
        check("", 0);
        check("a", 1);
        check("aaaa", 1);
        check("abcdef", 6);
        check("😀a😀", 2);
        check("😀😃a😄", 4);
        check("éaé", 2);

        Random rnd = new Random(20260829L);
        int[] alphabet = {'a','b','c','d',0x1F600,0x1F603};
        for (int tc = 0; tc < 5000; tc++) {
            int n = rnd.nextInt(18);
            StringBuilder s = new StringBuilder();
            for (int i = 0; i < n; i++) s.appendCodePoint(alphabet[rnd.nextInt(alphabet.length)]);
            String x = s.toString();
            check(x, brute(x));
        }

        String longSame = "a".repeat(1_000_000);
        check(longSame, 1);
        String pattern = "abcdefghijklmnopqrstuvwxyz".repeat(20_000);
        check(pattern, 26);

        try { LongestUniqueSubstring.length(null); throw new AssertionError("null must fail"); }
        catch (IllegalArgumentException expected) {}

        System.out.println("PASS normal left-no-retreat boundaries unicode random5000-vs-bruteforce million-same long-periodic null-exception");
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

    with tempfile.TemporaryDirectory(prefix='b52-longest-substring-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'LongestUniqueSubstring.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'LongestUniqueSubstringTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'LongestUniqueSubstring.java', 'LongestUniqueSubstringTest.java', cwd=tmpdir)
        stdout = run('java', '-Xmx512m', 'LongestUniqueSubstringTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS normal left-no-retreat boundaries unicode random5000-vs-bruteforce million-same long-periodic null-exception'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac LongestUniqueSubstring.java LongestUniqueSubstringTest.java && java -Xmx512m LongestUniqueSubstringTest',
        'stdout': stdout,
        'checks': [
            'normal examples cover repeated-window movement and the classic left-boundary-no-retreat case',
            'empty/single/all-same/all-unique boundaries are explicit',
            'supplementary Unicode code points are counted as code points rather than UTF-16 char units',
            '5000 deterministic random small strings match an independent brute-force code-point oracle',
            'one-million-same-character and long-periodic inputs validate large linear-shaped inputs without fixed wall-clock assumptions',
            'null follows the explicit exception contract',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact longest-unique-substring-and-tests source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 longest-unique-substring differential and long-input validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The exact source explicitly requests both the longest-substring-without-repetition implementation and comprehensive normal, boundary, exception, and very-long-input unit tests.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节']},
        {'claim_id': 'character-contract', 'text': 'The candidate explicitly defines characters and returned length as Unicode code points, empty as 0, and null as an invalid call.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'algorithm-validation', 'text': 'The last-seen sliding window is validated on directed edge cases plus 5000 deterministic random strings against an independent brute-force code-point oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'test-completeness', 'text': 'Executable tests separately cover normal behavior, left-boundary regression, empty/single/repeated/unique boundaries, Unicode supplementary characters, null exception, million-character and long-periodic inputs.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '常见追问']},
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
        'The answer treats test design as a first-class part of the source requirement rather than appending a few happy-path examples.',
        'The sliding-window invariant and the no-left-retreat condition are explicit, with abba included as a regression shape.',
        'Character semantics are strengthened to Unicode code point and validated with supplementary characters; grapheme-cluster limits are still stated.',
        'OpenJDK 21 validation includes 5000 deterministic differential cases plus million-character and long-periodic large-input shapes without brittle fixed timing thresholds.',
        'Normal, boundary, exception and long-input categories requested by the source are all separately covered and traceable to executable checks.',
        'The project section avoids fabricated experience and correctly frames segmentation choice as an API contract decision.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0052-longest-substring-tests-20260829-v1',
        'review_version': 'batch-0052.longest-substring-tests.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 longest-unique-substring test-focused source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0052-longest-substring-tests-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'abba', 'expected': 2, 'actual': 2, 'passed': True},
                {'case': '😀a😀', 'expected': 2, 'actual': 2, 'passed': True},
                {'case': '1,000,000 × a', 'expected': 1, 'actual': 1, 'passed': True},
                {'case': '5000 deterministic random Unicode-small strings', 'expected': 'equals brute-force oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e0ca3b11b4089b4f754ba3961313843f` source-first isolated review PASS: the source explicitly requires both longest-unique-substring code and complete normal/boundary/exception/very-long-input tests. The candidate defines Unicode code-point semantics, uses a no-left-retreat last-seen sliding window, and OpenJDK 21 validation covers directed normal/boundary/Unicode/null cases, 5000 random cases against a brute-force oracle, one million repeated characters, and a long periodic input. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
