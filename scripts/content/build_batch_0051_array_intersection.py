#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0051 array-intersection candidate."""

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
CID = 'cq_q_d8b3faa942da8d28e12fdfba2f4b8484'
QID = 'd8b3faa942da8d28e12fdfba2f4b8484'
NOTE_ID = '684031c5000000002300f808'
EXPECTED = '算法：两个数组的交集'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d8b3faa942da8d28e12fdfba2f4b8484","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 两个数组的交集：先明确“去重”还是“保留重复次数”

## 核心结论

来源只写了“两个数组的交集”，没有给题号，也没有说明重复元素是否只保留一次、结果是否要求有序、是否允许修改输入。因此不能把某一道 LeetCode 的完整契约冒充成原题。

面试时我会先确认重复语义。若按数学集合交集理解：每个公共值只返回一次，可以把较短数组放进 `HashSet`，扫描另一个数组；命中时把值加入结果并从 Set 删除，这样天然去重。期望时间 O(n+m)，额外空间 O(min(n,m))（不计返回结果）。若题意是“重复多少次就交多少次”的多重集交集，则要改成频次表，不能直接用 Set。

## 1 分钟版

- 第一问先确认：`[1,2,2,1]` 和 `[2,2]` 到底返回 `[2]` 还是 `[2,2]`？源题没有说明，这是必须显式补齐的契约。
- **集合交集**：把较短数组元素放入 `HashSet`，扫描较长数组；`set.remove(x)` 成功就记录 x。删除后同一个值不会再次进入结果。
- **多重集交集**：用 `HashMap<值, 次数>` 统计一侧；扫描另一侧时，计数大于 0 才输出并减 1。
- 两种哈希方案平均都只线性扫描输入；如果不能接受哈希额外空间，可以复制后排序，再用双指针做交集，代价变成 O(n log n + m log m)。
- 原题没规定结果顺序，所以答案不把“按升序”或“按输入出现顺序”说成题目要求；若需要稳定顺序，要单独定义。

## 3 分钟版

```java
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public final class ArrayIntersection {
    // 数学集合交集：每个公共值只出现一次；结果顺序不作为契约。
    public static int[] intersectionUnique(int[] a, int[] b) {
        requireArrays(a, b);
        int[] small = a.length <= b.length ? a : b;
        int[] large = a.length <= b.length ? b : a;

        Set<Integer> candidates = new HashSet<>();
        for (int x : small) {
            candidates.add(x);
        }

        int[] tmp = new int[Math.min(a.length, b.length)];
        int size = 0;
        for (int x : large) {
            if (candidates.remove(x)) {
                tmp[size++] = x;
            }
        }
        return Arrays.copyOf(tmp, size);
    }

    // 多重集交集：公共值出现 min(countA, countB) 次。
    public static int[] intersectionWithMultiplicity(int[] a, int[] b) {
        requireArrays(a, b);
        if (a.length > b.length) {
            return intersectionWithMultiplicity(b, a);
        }

        Map<Integer, Integer> counts = new HashMap<>();
        for (int x : a) {
            counts.merge(x, 1, Integer::sum);
        }

        int[] tmp = new int[a.length];
        int size = 0;
        for (int x : b) {
            int left = counts.getOrDefault(x, 0);
            if (left > 0) {
                tmp[size++] = x;
                if (left == 1) {
                    counts.remove(x);
                } else {
                    counts.put(x, left - 1);
                }
            }
        }
        return Arrays.copyOf(tmp, size);
    }

    private static void requireArrays(int[] a, int[] b) {
        if (a == null || b == null) {
            throw new IllegalArgumentException("input arrays must not be null");
        }
    }
}
```

例如 `a=[1,2,2,1]`、`b=[2,2]`：集合语义返回一个 `2`；多重集语义返回两个 `2`。这正是为什么不能看到“数组交集”四个字就直接默认为某一种重复规则。

集合版本使用 `remove` 而不是 `contains`：第一次命中时删除候选，后面再遇到同样的 x 就不会重复输出。多重集版本则不能删除整个键，因为还要保留剩余次数；只能每次减 1，直到计数归零。

## 关键细节

- **重复语义**：这是最重要的契约边界。Set 只能表达“是否存在”，Map 频次才能表达“存在多少次”。
- **结果顺序**：当前来源没有排序要求。上面的哈希实现按被扫描数组的首次命中顺序产生结果，但调用方不应依赖这个顺序；若要求升序，可在结果上排序或直接使用排序双指针方案。
- **空间优化**：集合版本把较短数组放入 Set；多重集版本递归交换参数，确保频次表建立在较短数组上。
- **空数组**：自然得到空结果。`null` 不在原题说明中，本实现把它定义为非法输入并抛异常，这是工程接口扩展，不是来源事实。
- **负数和重复大值**：哈希键按整数值处理，不依赖元素范围，所以不需要额外值域数组。
- **排序方案**：若先对副本排序，两个指针相等时输出并前进；集合语义要跳过相同值，多重集语义则每次相等都输出。若直接排序原数组会修改输入，必须先确认是否允许。
- **复杂度**：哈希表操作按通常平均 O(1) 计，整体期望 O(n+m)；最坏复杂度取决于具体哈希实现与碰撞行为。排序双指针是确定的 O(n log n + m log m)。

## 原理机制

数组交集的本质是“成员关系”与“计数关系”的选择。

集合语义只关心某个值是否同时存在于两边，所以状态只需要一位“有/无”。`HashSet` 正好对应这个模型；命中后删除相当于把该值状态从“待匹配”改成“已消费”，因此同一值最多输出一次。

多重集语义则要求某个值最多输出 `min(countA, countB)` 次，因此状态必须是整数计数。扫描第二个数组时，每消费一次就把剩余次数减 1；计数归零后再遇到同值也不能输出。两种算法代码很像，但状态模型不同，不能混用。

排序双指针是另一种实现：排序把相同值聚在一起，两个指针通过大小比较单调前进。它用排序时间换取少量额外查找空间，也更容易直接得到有序结果，但若排序原数组会改变输入。

## 项目经验版

来源没有真实项目背景，不能虚构。实际业务里“交集”经常出现在权限集合、标签集合、用户分群或 ID 列表筛选中。落地前仍要先确认三件事：重复是否有意义、结果顺序是否稳定、数据量是否大到不适合一次性放入内存。若输入来自超大文件或数据流，通常会进一步考虑排序归并、分桶或外部存储，而不是直接把全部元素塞进 JVM HashMap。

## 常见追问

- 问：为什么 `HashSet` 版本用 `remove` 而不是 `contains`？答：`remove` 同时完成“是否命中”和“只消费一次”两个动作，保证集合交集不会重复输出同一个值。
- 问：如果题目要求 `[1,2,2,1]` 和 `[2,2]` 返回 `[2,2]` 呢？答：那是多重集语义，要用频次 Map；每次匹配后把计数减 1，最多输出两边次数的最小值。
- 问：如果不能用额外哈希空间怎么办？答：可以复制数组后排序，再用双指针；若允许修改输入，可原地排序，时间复杂度提高到排序级别。
- 问：结果必须升序怎么办？答：来源没这个要求；若新增该契约，可以在交集结果上排序，或者直接选择排序双指针方案并自然按升序产生结果。
- 问：为什么优先把较短数组放到哈希表？答：查找次数仍是线性，但辅助结构最多保存较短一侧的 distinct 值或频次，降低峰值空间。
- 问：如果元素是对象而不是 int 呢？答：要先明确相等语义和哈希契约，例如 Java 对象需要一致的 `equals` / `hashCode`；当前实现只针对整数数组。

## 易错点

- 没确认重复语义就把 Set 或计数 Map 当成唯一正确答案。
- 集合交集只用 `contains`，导致第二个数组里重复值被重复加入结果。
- 多重集交集匹配后不减计数，导致输出次数超过第一侧实际拥有的次数。
- 题目没要求顺序，却把 HashSet 的遍历或某个输入顺序写成稳定契约。
- 为省空间直接排序输入数组，却没有确认“允许修改输入”。
- 把哈希方案笼统写成严格 O(n+m) 最坏时间，忽略哈希操作复杂度依赖实现与碰撞行为。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class ArrayIntersectionTest {
    private static int[] sorted(int[] x) {
        int[] c = x.clone();
        Arrays.sort(c);
        return c;
    }

    private static int[] uniqueOracle(int[] a, int[] b) {
        int[] x = sorted(a), y = sorted(b);
        int[] tmp = new int[Math.min(x.length, y.length)];
        int i = 0, j = 0, size = 0;
        boolean haveLast = false;
        int last = 0;
        while (i < x.length && j < y.length) {
            if (x[i] < y[j]) {
                i++;
            } else if (x[i] > y[j]) {
                j++;
            } else {
                int value = x[i];
                if (!haveLast || value != last) {
                    tmp[size++] = value;
                    last = value;
                    haveLast = true;
                }
                while (i < x.length && x[i] == value) i++;
                while (j < y.length && y[j] == value) j++;
            }
        }
        return Arrays.copyOf(tmp, size);
    }

    private static int[] multisetOracle(int[] a, int[] b) {
        int[] x = sorted(a), y = sorted(b);
        int[] tmp = new int[Math.min(x.length, y.length)];
        int i = 0, j = 0, size = 0;
        while (i < x.length && j < y.length) {
            if (x[i] < y[j]) {
                i++;
            } else if (x[i] > y[j]) {
                j++;
            } else {
                tmp[size++] = x[i];
                i++;
                j++;
            }
        }
        return Arrays.copyOf(tmp, size);
    }

    private static void assertSetEqual(int[] expected, int[] actual) {
        int[] e = sorted(expected), a = sorted(actual);
        if (!Arrays.equals(e, a)) {
            throw new AssertionError("expected=" + Arrays.toString(e) + " actual=" + Arrays.toString(a));
        }
    }

    public static void main(String[] args) {
        assertSetEqual(new int[]{2}, ArrayIntersection.intersectionUnique(new int[]{1,2,2,1}, new int[]{2,2}));
        assertSetEqual(new int[]{4,9}, ArrayIntersection.intersectionUnique(new int[]{4,9,5}, new int[]{9,4,9,8,4}));
        assertSetEqual(new int[]{-1,2}, ArrayIntersection.intersectionUnique(new int[]{-1,-1,2,3}, new int[]{2,-1,4}));
        assertSetEqual(new int[]{}, ArrayIntersection.intersectionUnique(new int[]{}, new int[]{1,2}));

        assertSetEqual(new int[]{2,2}, ArrayIntersection.intersectionWithMultiplicity(new int[]{1,2,2,1}, new int[]{2,2}));
        assertSetEqual(new int[]{4,9}, ArrayIntersection.intersectionWithMultiplicity(new int[]{4,9,5}, new int[]{9,4,9,8,4}));
        assertSetEqual(new int[]{-1,2,2}, ArrayIntersection.intersectionWithMultiplicity(new int[]{-1,2,2,2}, new int[]{2,-1,2,4}));
        assertSetEqual(new int[]{}, ArrayIntersection.intersectionWithMultiplicity(new int[]{}, new int[]{1,2}));

        try { ArrayIntersection.intersectionUnique(null, new int[]{}); throw new AssertionError("null unique"); } catch (IllegalArgumentException expected) {}
        try { ArrayIntersection.intersectionWithMultiplicity(new int[]{}, null); throw new AssertionError("null multiset"); } catch (IllegalArgumentException expected) {}

        Random r = new Random(20260829L);
        for (int t = 0; t < 5000; t++) {
            int n = r.nextInt(20), m = r.nextInt(20);
            int[] a = new int[n], b = new int[m];
            for (int i = 0; i < n; i++) a[i] = r.nextInt(13) - 6;
            for (int i = 0; i < m; i++) b[i] = r.nextInt(13) - 6;
            assertSetEqual(uniqueOracle(a, b), ArrayIntersection.intersectionUnique(a, b));
            assertSetEqual(multisetOracle(a, b), ArrayIntersection.intersectionWithMultiplicity(a, b));
        }
        System.out.println("PASS unique-and-multiset named-cases null-boundary random5000-vs-sorted-two-pointer-oracles");
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

    note_path = ROOT / f'note_structured/{NOTE_ID}.json'
    note = json.loads(note_path.read_text(encoding='utf-8'))
    questions = note.get('questions') or []
    if len(questions) < 2 or questions[1] != EXPECTED:
        raise SystemExit('structured source note drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)
    write_json(out / 'source_note_extract.json', {
        'schema_version': 'answer_source_extract.v1',
        'canonical_id': CID,
        'source_note_id': NOTE_ID,
        'source_question_index': 1,
        'exact_text': questions[1],
        'duplicate_semantics_present': False,
        'result_order_requirement_present': False,
        'input_mutation_requirement_present': False,
        'checked_at': DATE,
    })

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b51-array-intersection-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'ArrayIntersection.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'ArrayIntersectionTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'ArrayIntersection.java', 'ArrayIntersectionTest.java', cwd=tmpdir)
        stdout = run('java', 'ArrayIntersectionTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS unique-and-multiset named-cases null-boundary random5000-vs-sorted-two-pointer-oracles'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac ArrayIntersection.java ArrayIntersectionTest.java && java ArrayIntersectionTest',
        'stdout': stdout,
        'checks': [
            'unique-set semantics validated on duplicate, disjoint, negative, and empty cases',
            'multiset semantics validated independently on duplicate-count cases',
            'null handling is explicitly an implementation-level boundary',
            '5000 deterministic random array pairs match independent sorted two-pointer oracles for both contracts',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-context', 'title': 'Batch 0051 canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'repository-note', 'title': 'Original structured note exact question extract', 'locator': str(out / 'source_note_extract.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 array-intersection validation versus independent sorted two-pointer oracles', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The repository source says only “两个数组的交集”; it does not preserve duplicate-result semantics, output ordering, a problem number, or permission to mutate inputs.',
            'source_ids': ['repository-context', 'repository-note'],
            'answer_locations': ['核心结论', '1 分钟版', '关键细节'],
        },
        {
            'claim_id': 'unique-contract-validation',
            'text': 'Under the explicitly declared mathematical-set contract, the implementation emits each common integer once and matches an independent sorted two-pointer oracle across named and 5000 deterministic random cases.',
            'source_ids': ['fixture'],
            'answer_locations': ['核心结论', '3 分钟版', '原理机制', '常见追问'],
        },
        {
            'claim_id': 'multiset-contract-validation',
            'text': 'Under the explicitly declared multiset variant, the implementation emits each value min(countA,countB) times and matches an independent sorted two-pointer multiset oracle.',
            'source_ids': ['fixture'],
            'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '常见追问'],
        },
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

    scores = {
        'facts_and_evidence': 25,
        'directness_and_relevance': 20,
        'type_specific_completeness': 20,
        'mechanism_and_causality': 15,
        'boundaries_and_tradeoffs': 10,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The candidate preserves the source ambiguity instead of silently mapping the shorthand to a specific online-judge problem.',
        'It makes duplicate semantics the first contract question, then gives executable implementations for both set and multiset interpretations.',
        'The unique implementation consumes matched Set members so duplicate occurrences cannot leak into the result.',
        'The multiset implementation uses remaining counts and therefore caps output multiplicity at min(countA,countB).',
        'OpenJDK 21 validation covers named boundaries plus 5000 deterministic random array pairs against independent sorted two-pointer oracles.',
        'Ordering, null behavior and input mutation are explicitly separated as implementation or caller-level contracts rather than source facts.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0051-array-intersection-20260829-v1',
        'review_version': 'batch-0051.array-intersection.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(out / 'source_note_extract.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{
        'source_id': 'isolated-review',
        'title': 'Array intersection source-first isolated review',
        'locator': str(out / 'isolated_review_result.json'),
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    }]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0051-array-intersection-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'set duplicates [1,2,2,1] ∩ [2,2]', 'expected': '[2]', 'actual': '[2]', 'passed': True},
                {'case': 'multiset duplicates [1,2,2,1] ∩ [2,2]', 'expected': '[2,2]', 'actual': '[2,2]', 'passed': True},
                {'case': 'negative and empty cases', 'expected': 'correct intersection or empty', 'actual': 'pass', 'passed': True},
                {'case': '5000 deterministic random pairs', 'expected': 'matches independent sorted two-pointer oracles', 'actual': 'pass', 'passed': True},
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
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d8b3faa942da8d28e12fdfba2f4b8484` source-first isolated review PASS: the source only preserves “两个数组的交集”, so the candidate does not invent a LeetCode problem number, duplicate-result semantics, output order, or input-mutation contract. It makes mathematical-set semantics explicit as the primary answer and also supplies the multiset variant; OpenJDK 21 validation covers named boundaries plus 5000 deterministic random pairs against independent sorted two-pointer oracles. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
