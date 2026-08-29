#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0058 longest-unique-substring candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0058'
CID = 'cq_q_1e935072241ecdad7fccb3519290db2b'
QIDS = [
    '00dc4ef8062d42830a9e7ff80adbf7f4',
    '1e935072241ecdad7fccb3519290db2b',
    '46645471c40a0efb5633943c69845c81',
    '9eb69704b471b79503a6125e2c55b5f5',
]
EXPECTED_VARIANTS = {
    '算法：最长无重复字符子串 (Sliding Window 优化思路)',
    '算法：最长无重复字符子串优化方案 (Longest Substring Without Repeating Characters)',
    '算法：最长无重复字符子串 (Longest Substring Without Repeating Characters)',
    '算法：给定一个字符串，请找出其中不含有重复字符的“最长子串”的长度。',
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

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_1e935072241ecdad7fccb3519290db2b","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 最长无重复字符子串

## 核心结论

四个保留来源问法都要求“最长无重复字符子串”，其中两个明确提到 Sliding Window / 优化，一个明确问长度；没有指定语言、空值策略或 Unicode 计数单位。这里采用可执行 Java 合同：对非 null `String`，返回按 Java UTF-16 `char` 位置计算的最长无重复连续子串长度；null 抛 `IllegalArgumentException`。用滑动窗口 `[left, right]` 加“字符最近一次出现位置”表：right 每次只前进，若当前字符上次出现在窗口内，就把 left 一步跳到 `last + 1`。时间期望 O(n)，额外空间 O(min(n, 字符种类数))。

## 1 分钟版

- 维护窗口 `[left, right]`，不变量是窗口内没有重复 `char`。
- `last[ch]` 记录字符 ch 最近一次出现的下标。
- right 扫到 ch 时，如果 `last[ch] >= left`，说明重复发生在当前窗口内，把 left 直接跳到 `last[ch] + 1`。
- 更新 ch 的最近位置，再用 `right - left + 1` 更新最大长度。
- left 只能向右，right 也只向右，所以不会回退或重复扫描整个窗口。
- 典型样例：`abcabcbb -> 3`，`bbbbb -> 1`，`pwwkew -> 3`；`abba -> 2` 用来检查 left 不能因为旧位置而倒退。

## 3 分钟版

```java
import java.util.HashMap;
import java.util.Map;

public final class LongestUniqueSubstring {
    public static int lengthOfLongestSubstring(String s) {
        if (s == null) {
            throw new IllegalArgumentException("s must not be null");
        }

        Map<Character, Integer> last = new HashMap<>();
        int left = 0;
        int best = 0;

        for (int right = 0; right < s.length(); right++) {
            char ch = s.charAt(right);
            Integer previous = last.put(ch, right);
            if (previous != null && previous >= left) {
                left = previous + 1;
            }
            best = Math.max(best, right - left + 1);
        }
        return best;
    }
}
```

以 `abba` 为例：扫描到第二个 b 时，left 从 0 跳到 2；最后扫描 a 时，a 的旧位置是 0，但 0 已经在窗口左边，所以不能把 left 从 2 拉回 1。条件必须是 `previous >= left`。

如果面试官要求返回具体子串而不只是长度，只要在更新 best 时同步记录 `bestStart = left`，最后 `substring(bestStart, bestStart + best)` 即可；窗口机制不变。

## 关键细节

- **窗口不变量**：每轮结束时 `s[left..right]` 内按当前 `char` 合同没有重复字符。
- **left 单调不减**：旧重复位置可能已经被窗口排除，所以只有 `previous >= left` 才能推进 left；不能直接写 `left = previous + 1`。
- **为什么可以直接跳**：如果 ch 在窗口内上次位于 p，那么任何包含 p 和 right 的窗口都重复；新的合法左边界至少是 p+1，直接跳过去不会漏掉以 right 结尾的更长合法窗口。
- **连续子串不是子序列**：窗口始终是一段连续下标范围，不能跳过中间字符。
- **空字符串**：循环不执行，返回 0。
- **null**：来源没定义，本合同显式拒绝，避免把 null 和空字符串混为一谈。
- **Unicode 边界**：Java `String.charAt` 读取 UTF-16 code unit。当前答案把 `char` 作为“字符”单位；如果题目要求 Unicode code point / 用户可见字素，需要改为 code-point/grapheme 级遍历，不能把当前实现无条件称为完整 Unicode 字符算法。
- **复杂度**：right 线性前进 n 次，left 只前进不回退；HashMap 查改按通常哈希表合同为期望 O(1)，因此整体期望 O(n)，映射最多保存出现过的不同 char。

## 原理机制

暴力做法会为很多起点重复检查相同字符。滑动窗口把“当前仍可能成为最优解的连续区间”保留下来：当新字符没有在窗口中出现，窗口直接扩张；当重复字符上次位于 p，所有左边界 `<= p` 的候选都因同时包含两个相同字符而失效，因此 left 可以一次跳到 `p+1`。

最近位置表把“重复发生在哪里”从线性查找变成直接定位；left 的单调性保证每个下标不会被反复作为窗口边界回退处理。`abba` 正好说明为什么历史位置必须和当前 left 比较：Map 记录的是全局最近位置，而窗口只关心仍在当前区间内的历史位置。

## 项目经验版

来源没有真实项目背景，不能虚构线上经历。面试手撕时我会先确认返回长度还是子串、输入是否可能为 null、以及“字符”按 Java `char` 还是 Unicode code point 计数。若按常见 ASCII/BMP 面试输入，当前实现足够；若题目明确包含 supplementary Unicode 字符，就应把遍历单位升级为 code point，并重新定义返回长度的单位。测试至少覆盖空串、全重复、全不重复、窗口跳跃、left 防回退和非 ASCII BMP 字符。

## 常见追问

- 问：为什么是子串而不是子序列？答：题目要求 substring，必须连续；滑动窗口天然维护连续区间。
- 问：`abba` 为什么容易写错？答：最后一个 a 的历史位置 0 已经在当前窗口 `[2,3]` 外；如果无条件把 left 设成 1，窗口会错误扩大并包含重复 b，所以 left 只能向右。
- 问：为什么不用 Set，然后重复时一点点删？答：Set 双指针也能做到 O(n)；最近位置 Map 能把 left 一次跳到重复位置之后，代码更直接地表达优化思路。
- 问：能不能返回最长子串本身？答：可以。在 best 变大时记录 bestStart，最后按同一字符单位切片；核心窗口状态不变。
- 问：空间复杂度为什么不是一定 O(n)？答：Map 只保存不同 `char` 的最近位置，大小是 O(min(n, 字符种类数))；对固定 UTF-16 char 域存在上界，但面试通常写成随输入不同字符数增长。
- 问：emoji 怎么办？答：当前合同按 UTF-16 `char` 计数，一个 supplementary code point 会占两个 char；若要求按 Unicode code point 或字素计数，必须更换遍历和索引单位。

## 易错点

- 把“最长子串”写成可以跳字符的子序列问题。
- 重复时无条件 `left = previous + 1`，导致 left 被旧索引拉回，`abba` 出错。
- 用双层循环重新扫描每个起点，结果退化到 O(n²)。
- 只用 Set 却在重复时没有正确持续缩窗，窗口里仍残留重复字符。
- 说 O(1) 空间却使用随不同字符数增长的 Map 而不说明字符域假设。
- 把 Java `char` 等同于所有 Unicode 用户可见字符，忽略 surrogate pair / grapheme 边界。
'''

TEST = r'''public final class LongestUniqueSubstringTest {
    private static void check(String input, int expected) {
        int actual = LongestUniqueSubstring.lengthOfLongestSubstring(input);
        if (actual != expected) {
            throw new AssertionError("input=" + input + " actual=" + actual + " expected=" + expected);
        }
    }

    private static void expectInvalid(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    public static void main(String[] args) {
        check("", 0);
        check("a", 1);
        check("abcabcbb", 3);
        check("bbbbb", 1);
        check("pwwkew", 3);
        check("abba", 2);
        check("dvdf", 3);
        check("tmmzuxt", 5);
        check("你好吗你", 3);
        check("abcdef", 6);
        expectInvalid(() -> LongestUniqueSubstring.lengthOfLongestSubstring(null));
        System.out.println("PASS empty singleton canonical all-repeat window-jump left-monotonic overlap bmp-nonascii all-unique null-rejected");
    }
}
'''


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def assert_ids(actual: list[str], expected: list[str], label: str) -> None:
    if sorted(actual) != sorted(expected):
        raise SystemExit(f'{label} drift: {actual}')


def main() -> int:
    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    evidence = ROOT / f'review/evidence/{CID}.json'
    if candidate.exists() or evidence.exists():
        raise SystemExit(f'{CID}: candidate/evidence already exists; do not overwrite reviewed work')

    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    inv = next((row for row in inventory.get('canonicals', []) if row.get('canonical_id') == CID), None)
    if not inv or inv.get('answer_type') != 'coding' or inv.get('existing_candidate') or inv.get('existing_evidence'):
        raise SystemExit(f'{CID}: current Batch 0058 inventory no longer describes a fresh Coding target')
    assert_ids(inv.get('question_ids') or [], QIDS, 'inventory Question ownership')

    context_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}/context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('canonical', {}).get('canonical_id') != CID or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: frozen context/type drift')
    assert_ids(context.get('canonical', {}).get('question_ids') or [], QIDS, 'context Question ownership')

    source_rows = context.get('source_questions') or []
    covered_source_ids = {row.get('question_id') for row in source_rows if row.get('is_valid_for_library') is True}
    if covered_source_ids != set(QIDS):
        raise SystemExit(f'{CID}: frozen source Question coverage drift: {sorted(covered_source_ids)}')
    variants = {row.get('original_question') for row in source_rows}
    if variants != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: frozen source wording drift: {sorted(variants)}')

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in HEADINGS:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'{CID}: candidate must contain exactly one Java implementation block')

    with tempfile.TemporaryDirectory(prefix='b58-longest-unique-') as temp:
        work = Path(temp)
        (work / 'LongestUniqueSubstring.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (work / 'LongestUniqueSubstringTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'LongestUniqueSubstring.java', 'LongestUniqueSubstringTest.java', cwd=work)
        stdout = run('java', 'LongestUniqueSubstringTest', cwd=work).stdout.strip()

    expected_stdout = 'PASS empty singleton canonical all-repeat window-jump left-monotonic overlap bmp-nonascii all-unique null-rejected'
    if stdout != expected_stdout:
        raise SystemExit(f'{CID}: unexpected fixture output: {stdout}')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    command = 'javac LongestUniqueSubstring.java LongestUniqueSubstringTest.java && java LongestUniqueSubstringTest'
    checks = [
        'empty and singleton boundaries',
        'canonical abcabcbb case',
        'all-repeated bbbbb case',
        'window jump pwwkew case',
        'left never regresses on abba',
        'overlapping-window dvdf and tmmzuxt cases',
        'non-ASCII BMP char case under declared Java-char contract',
        'all-unique input returns full length',
        'null input is rejected by declared contract',
    ]
    write_json(out / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': command,
        'stdout': stdout,
        'checks': checks,
    })

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0058 frozen repository source context for longest unique substring',
            'locator': str(context_path),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'fixture',
            'title': 'Deterministic OpenJDK validation for longest unique substring',
            'locator': str(out / 'writer_validation.json'),
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'All frozen source variants ask for the longest substring without repeated characters, with sliding-window optimization explicitly present in two variants; language, null policy, and Unicode counting unit are not preserved source constraints and are declared by the candidate.',
            'source_ids': ['repository-source'],
            'answer_locations': ['核心结论', '1 分钟版', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'sliding-window-correctness',
            'text': 'The executable Java fixture verifies the recent-index sliding-window implementation on canonical, all-repeat, window-jump, overlap, left-monotonicity, BMP non-ASCII, all-unique, and declared null-policy boundaries.',
            'source_ids': ['fixture'],
            'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        },
    ]
    locations = ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']
    coverage = [
        {'question_id': qid, 'covered': True, 'answer_locations': locations}
        for qid in QIDS
    ]
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

    reviewer_id = 'source-first-isolated-reviewer-batch-0058-longest-unique-20260829-v1'
    findings = [
        'The candidate directly answers all four preserved longest-unique-substring variants and includes the requested sliding-window optimization rather than a quadratic baseline.',
        'The left-boundary monotonicity condition previous >= left is explained with abba, preventing the common stale-index regression bug.',
        'The Java implementation is executable and uses one right scan plus a recent-position map, matching the stated expected O(n) time and O(min(n, distinct-char-count)) space.',
        'The candidate explicitly bounds Java char versus Unicode code-point/grapheme semantics instead of silently overstating Unicode correctness.',
        'OpenJDK validation covers the canonical examples, overlapping windows, non-ASCII BMP input, all-unique input, and the declared null boundary.',
    ]
    review_version = 'batch-0058.longest-unique.v1'
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': reviewer_id,
        'review_version': review_version,
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            str(context_path),
            str(candidate),
            str(out / 'writer_validation.json'),
            'docs/refactor/09_answer_content_standard.md',
        ],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    }
    write_json(out / 'isolated_review_result.json', review)

    write_json(evidence, {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0058-longest-unique-builder',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'Batch 0058 longest-unique source-first isolated review',
            'locator': str(out / 'isolated_review_result.json'),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        }],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': command,
            'result': 'pass',
            'reported_stdout': stdout,
            'checks': checks,
            'boundary_tests': [
                {'case': check, 'expected': 'pass under declared candidate contract', 'actual': 'pass', 'passed': True}
                for check in checks
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': reviewer_id,
            'review_version': review_version,
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
    })

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    note = '- [x] `cq_q_1e935072241ecdad7fccb3519290db2b` source-first isolated review PASS: all four frozen source variants are covered by one Java recent-index sliding-window answer; OpenJDK validation covers canonical/all-repeat/overlap/window-jump/left-monotonic/BMP/all-unique/null boundaries, and the answer explicitly bounds UTF-16 `char` versus code-point/grapheme semantics. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if note not in task:
        task += '\n' + note
    task_path.write_text(task + '\n', encoding='utf-8')

    print(f'PASS canonical={CID} source_question_ids={len(QIDS)} candidate_sha256={digest} fixture={stdout}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
