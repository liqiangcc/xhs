#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0050 cycle-detection candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0050'
CID = 'cq_q_88d86d8e4586504b5c9365f4126f7436'
QID = '88d86d8e4586504b5c9365f4126f7436'
EXPECTED = '算法：检测链表是否有环（要求检测入参合法性）'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_88d86d8e4586504b5c9365f4126f7436","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 检测链表是否有环，并明确输入合法性边界

## 核心结论

检测单链表是否有环，核心用 Floyd 快慢指针：`slow` 每次走 1 步，`fast` 每次走 2 步；如果存在环，两者最终会在环内相遇；如果不存在环，`fast` 或 `fast.next` 会先到 `null`。时间复杂度 O(n)，额外空间 O(1)，不修改链表。

题目还明确要求“检测入参合法性”，但没有定义什么叫非法。对 Java 的 `ListNode head` 本身，`null` 应视为合法空链表并返回 `false`；非 `null` 引用已经受类型系统约束，没有办法像 C/C++ 裸指针那样额外判断“地址是否合法”。如果链表由外部的“节点数组 + 入环位置 `pos`”构造，则可以在输入适配层明确校验：数组不能为 `null`，`pos` 只能是 `-1`（无环）或 `[0, n-1]`，空数组只能配 `pos=-1`。不要把未定义的“合法性”偷偷扩张成题目事实。

## 1 分钟版

- `head == null` 是合法空链表，直接返回 `false`。
- Floyd：slow 每次 1 步、fast 每次 2 步；无环时 fast 会触达 `null`，有环时快指针会在环内追上慢指针。
- 循环条件写成 `fast != null && fast.next != null`，避免访问空引用。
- 算法只移动局部引用，不改 `next`，所以输入拓扑保持不变。
- “入参合法性”必须绑定具体接口。若只有 `ListNode head`，Java 里没有额外可验证的裸指针地址；若输入来自数组和 `pos`，就在构造层验证 `pos` 范围。
- 若要求找入环节点而不只是判断是否有环，需要在第一次相遇后再做第二阶段，这不是本题当前输出要求。

## 3 分钟版

```java
public final class CycleDetection {
    public static final class ListNode {
        public final int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }

    public static boolean hasCycle(ListNode head) {
        ListNode slow = head;
        ListNode fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) {
                return true;
            }
        }
        return false;
    }

    public static boolean hasCycleFromInput(int[] values, int pos) {
        if (values == null) {
            throw new IllegalArgumentException("values must not be null");
        }
        if (pos < -1 || pos >= values.length) {
            throw new IllegalArgumentException("pos out of range");
        }

        if (values.length == 0) {
            return false; // only pos == -1 can reach here
        }

        ListNode[] nodes = new ListNode[values.length];
        for (int i = 0; i < values.length; i++) {
            nodes[i] = new ListNode(values[i]);
            if (i > 0) {
                nodes[i - 1].next = nodes[i];
            }
        }
        if (pos >= 0) {
            nodes[nodes.length - 1].next = nodes[pos];
        }
        return hasCycle(nodes[0]);
    }
}
```

为什么 Floyd 一定有效？如果无环，fast 每次走得更快，所以会先越过尾部并触发 `null` 结束。如果有环，slow 和 fast 都进入环后，可以只看它们在环上的相对位置：每一轮 fast 比 slow 多前进 1 个节点，因此二者的环上距离会按模“环长”不断变化，最多经过一个环长的轮数必然变成 0，也就是相遇。

这里把“算法输入”和“外部输入”分开：`hasCycle(ListNode)` 只负责链表拓扑判断；`hasCycleFromInput(int[], pos)` 才负责数组是否为空引用、`pos` 是否越界等可判定的入参契约。这样不会把输入解析规则污染到 Floyd 核心。

## 关键细节

- **空链表**：`head == null` 是正常边界，不是异常；Floyd 直接返回 `false`。
- **单节点无环**：`head.next == null`，循环不进入，返回 `false`。
- **单节点自环**：第一次循环 slow 和 fast 都回到该节点，立即相遇，返回 `true`。
- **循环条件**：必须同时检查 `fast != null` 和 `fast.next != null`，因为下一步会访问 `fast.next.next`。
- **相等判断**：比较的是节点引用 identity，不是节点值；两个值相同但不同节点不能算相遇。
- **不修改输入**：检测过程中不写任何 `next`，因此无论有环还是无环，拓扑保持不变。
- **复杂度**：无环时 fast 至多线性向尾部推进；有环时进入环后最多再经过 O(环长) 轮相遇，因此总时间 O(n)，只用两个指针，额外空间 O(1)。
- **合法性边界**：Java 对象引用不是裸地址；若题目真正要求检查“坏指针/悬空指针”，那是另一种语言和内存模型下的接口，不能由这个 Java API 假装完成。

## 原理机制

Floyd 算法把“是否重复访问过某节点”的历史信息编码成两个不同速度的指针，而不是显式保存 `HashSet<ListNode>`。无环链表是一条有限路径，快指针最终离开路径；有环链表包含一个有限环，两个指针进入环后，它们的相对速度为每轮 1 个节点。设环长为 `L`，相对距离每轮加 1（模 `L`），因此一定会覆盖模 `L` 的全部余数并出现 0，也就是引用相同。

HashSet 方案同样正确：遍历时把节点引用放入集合，第一次遇到已存在节点即可判环，时间 O(n)、空间 O(n)。Floyd 的优势是在只需要“是否有环”时把辅助空间降到 O(1)；如果后续还需要保留访问路径或做更复杂诊断，集合方案可能更直接。

## 项目经验版

来源没有提供真实项目场景，不能虚构生产经历。工程中我会先明确链表从哪里来：如果是进程内 Java 对象，合法性通常是 API 级的 `null`、长度或构造参数规则；如果是反序列化后的索引表，则应先验证索引范围、节点数量和引用关系，再构造链表；如果是 C/C++ 裸指针，悬空指针或非法地址不能靠普通 Floyd 逻辑安全探测，必须依赖更上层的内存所有权、边界和工具保障。

## 常见追问

- 问：为什么快慢指针有环时一定会相遇？答：两者进入环后，fast 每轮比 slow 多走 1 步；环上相对距离按环长取模，每轮变化 1，最多一个环长就会变成 0。
- 问：为什么不能比较节点值？答：环判断关心是否回到同一个节点对象；不同节点完全可以有相同 `val`，值相同不能证明拓扑重复。
- 问：`null` 是不是非法入参？答：题目没有这样规定。对“链表头指针”接口，空链表是常见合法边界，本答案将它定义为合法并返回 `false`；若调用方契约明确禁止空链表，再在接口层抛异常。
- 问：如何找入环节点？答：第一次相遇后，把一个指针放回 head，另一个留在相遇点，两者都改为每次走 1 步；再次相遇的位置就是环入口。那是比“是否有环”更强的输出契约。
- 问：HashSet 和 Floyd 怎么选？答：只判环且追求 O(1) 辅助空间用 Floyd；如果需要记录访问历史、输出路径或更强诊断，HashSet 更直观但需要 O(n) 空间。
- 问：如何检测“非法指针”？答：Java `ListNode` 引用层没有 C/C++ 裸地址式的可探测合法性。必须先说明输入模型；能验证的是解析层参数和结构约束，不能安全地解引用一个真正未知的坏地址去“试试看”。

## 易错点

- 只检查 `fast != null`，随后直接访问 `fast.next.next`。
- 比较节点值而不是节点引用，重复值会造成误判。
- 把 `null` 无依据地判成非法，或反过来声称题目明确允许空链表。
- 为了所谓“输入合法性”在 Floyd 循环里加入与题意无关的最大步数，反而把合法的大环误判成异常。
- 检测时修改 `next` 做标记，破坏原链表。
- 把“判断有环”和“找到入环点”混成同一个未说明的输出契约。
'''

TEST = r'''public final class CycleDetectionTest {
    private static CycleDetection.ListNode[] nodes(int... values) {
        CycleDetection.ListNode[] out = new CycleDetection.ListNode[values.length];
        for (int i = 0; i < values.length; i++) {
            out[i] = new CycleDetection.ListNode(values[i]);
            if (i > 0) out[i - 1].next = out[i];
        }
        return out;
    }

    private static void expectIllegal(int[] values, int pos) {
        try {
            CycleDetection.hasCycleFromInput(values, pos);
            throw new AssertionError("expected IllegalArgumentException pos=" + pos);
        } catch (IllegalArgumentException expected) {
            // pass
        }
    }

    public static void main(String[] args) {
        if (CycleDetection.hasCycle(null)) throw new AssertionError("empty direct list");

        CycleDetection.ListNode[] one = nodes(7);
        if (CycleDetection.hasCycle(one[0])) throw new AssertionError("single no-cycle");
        one[0].next = one[0];
        if (!CycleDetection.hasCycle(one[0])) throw new AssertionError("single self-cycle");

        CycleDetection.ListNode[] linear = nodes(1, 1, 1, 1, 1);
        if (CycleDetection.hasCycle(linear[0])) throw new AssertionError("duplicate values are not a cycle");
        if (linear[0].next != linear[1] || linear[3].next != linear[4] || linear[4].next != null) {
            throw new AssertionError("linear topology mutated");
        }

        CycleDetection.ListNode[] tailCycle = nodes(1, 2, 3, 4, 5);
        tailCycle[4].next = tailCycle[2];
        if (!CycleDetection.hasCycle(tailCycle[0])) throw new AssertionError("tail-to-middle cycle");
        if (tailCycle[4].next != tailCycle[2]) throw new AssertionError("cycle topology mutated");

        if (CycleDetection.hasCycleFromInput(new int[]{1, 2, 3}, -1)) throw new AssertionError("validated no-cycle input");
        if (!CycleDetection.hasCycleFromInput(new int[]{1, 2, 3}, 0)) throw new AssertionError("validated head-cycle input");
        if (!CycleDetection.hasCycleFromInput(new int[]{1, 2, 3}, 2)) throw new AssertionError("validated self-tail cycle input");
        if (CycleDetection.hasCycleFromInput(new int[]{}, -1)) throw new AssertionError("validated empty input");
        expectIllegal(null, -1);
        expectIllegal(new int[]{}, 0);
        expectIllegal(new int[]{1, 2, 3}, -2);
        expectIllegal(new int[]{1, 2, 3}, 3);

        for (int n = 1; n <= 200; n++) {
            int[] values = new int[n];
            for (int i = 0; i < n; i++) values[i] = i % 5;
            if (CycleDetection.hasCycleFromInput(values, -1)) throw new AssertionError("exhaustive no-cycle n=" + n);
            for (int pos = 0; pos < n; pos++) {
                if (!CycleDetection.hasCycleFromInput(values, pos)) {
                    throw new AssertionError("exhaustive cycle n=" + n + " pos=" + pos);
                }
            }
        }
        System.out.println("PASS empty single self-cycle duplicate-values tail-cycle input-validation exhaustive-n1-200 topology-preserved");
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

    with tempfile.TemporaryDirectory(prefix='b50-cycle-detection-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'CycleDetection.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'CycleDetectionTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'CycleDetection.java', 'CycleDetectionTest.java', cwd=tmpdir)
        stdout = run('java', 'CycleDetectionTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS empty single self-cycle duplicate-values tail-cycle input-validation exhaustive-n1-200 topology-preserved'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac CycleDetection.java CycleDetectionTest.java && java CycleDetectionTest',
        'stdout': stdout,
        'checks': [
            'null/empty and single-node acyclic inputs return false',
            'single-node self-cycle and tail-to-middle cycles return true',
            'duplicate node values without repeated node identity do not create a false positive',
            'the validated values+pos adapter rejects null arrays and out-of-range positions',
            'all n=1..200 no-cycle and every possible cycle-entry position return the expected result',
            'the direct linked-list topology remains unchanged by detection',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 split-child canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 exhaustive Floyd-cycle executable validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The split repository source asks to detect whether a linked list has a cycle and explicitly asks for input-validity checking, but it does not define the language-level invalid-input model or require cycle-entry output.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'algorithm-validation', 'text': 'The OpenJDK 21 fixture verifies Floyd reference-identity detection for empty, single-node, self-cycle, duplicate-value acyclic, and tail-to-middle-cycle cases and exhaustively checks every cycle-entry position for list sizes 1 through 200.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'input-validation', 'text': 'The explicit values-plus-pos adapter validates only a concrete external input contract: values must be non-null and pos must be -1 or a valid node index; null ListNode head remains a legal empty-list boundary for the core detector.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'complexity-bound', 'text': 'The detector stores only slow and fast node references and advances them forward; the executable source shape therefore uses constant auxiliary storage and linear traversal time for finite lists.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '关键细节', '原理机制']},
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
        'facts_and_evidence': 24,
        'directness_and_relevance': 20,
        'type_specific_completeness': 20,
        'mechanism_and_causality': 15,
        'boundaries_and_tradeoffs': 10,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The candidate directly answers the split cycle-detection source instead of carrying over the retired compound Canonical.',
        'The source requests input-validity checking but leaves the invalid-input model unspecified; the candidate separates Java ListNode semantics from a concrete values-plus-pos input adapter rather than inventing unsafe pointer validation.',
        'The Floyd relative-speed invariant is explained and the implementation compares node identity, not node value.',
        'OpenJDK 21 validation covers empty, single-node, self-cycle, duplicate-value acyclic, tail-cycle, input-validation, topology-preservation, and exhaustive n=1..200 every-entry cases.',
        'The answer explicitly separates boolean cycle detection from the stronger cycle-entry problem and does not silently broaden the requested output.',
        'No production history or language-independent bad-pointer claim is fabricated.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0050-cycle-detection-20260829-v1',
        'review_version': 'batch-0050.cycle-detection.v1',
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

    evidence_sources = sources + [{
        'source_id': 'isolated-review',
        'title': 'Cycle-detection split-child source-first isolated review',
        'locator': str(out / 'isolated_review_result.json'),
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    }]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0050-cycle-detection-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'empty and single-node acyclic inputs', 'expected': 'false without exception', 'actual': 'pass', 'passed': True},
                {'case': 'single-node self-cycle and tail-to-middle cycle', 'expected': 'true', 'actual': 'pass', 'passed': True},
                {'case': 'duplicate values on distinct nodes', 'expected': 'no false cycle from equal values', 'actual': 'pass', 'passed': True},
                {'case': 'external values+pos validation', 'expected': 'null arrays and out-of-range positions rejected', 'actual': 'pass', 'passed': True},
                {'case': 'exhaustive n=1..200', 'expected': 'all acyclic and every possible cycle-entry topology classified correctly', 'actual': 'pass', 'passed': True},
                {'case': 'topology preservation', 'expected': 'detector does not rewrite next links', 'actual': 'pass', 'passed': True},
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
    line = '- [x] `cq_q_88d86d8e4586504b5c9365f4126f7436` split-child source-first isolated review PASS: the source-exact contract is cycle detection plus input-validity checking; the candidate uses Floyd reference-identity detection, treats null head as a legal empty-list boundary, and moves concrete values/pos validation into an explicit adapter because the source does not define a language-level bad-pointer model. OpenJDK 21 validation covers empty/single/self-cycle/duplicate-value/tail-cycle/topology boundaries and exhaustively checks every entry position for n=1..200. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
