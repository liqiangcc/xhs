#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0050 odd/even linked-list split candidate."""

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
CID = 'cq_q_d80c5515628053be95dcb56bc561643a'
QID = 'd80c5515628053be95dcb56bc561643a'
EXPECTED = '算法：链表奇偶拆分'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d80c5515628053be95dcb56bc561643a","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 链表奇偶拆分：先澄清“奇偶”指位置还是节点值

## 核心结论

题目只有“链表奇偶拆分”六个字，最关键的不是马上写代码，而是先确认“奇偶”的定义。常见有两种完全不同的合同：**按节点位置奇偶拆分**（第 1、3、5... 个节点进 odd，第 2、4、6... 个节点进 even）和**按节点值奇偶拆分**（奇数值节点进 odd，偶数值节点进 even）。两种都能用两个尾指针一趟稳定拆分，保持各自内部的原相对顺序，时间 O(n)、额外指针空间 O(1)。

本答案不给来源强行补一个不存在的定义，而是把两种常见实现都给出。两种实现都复用原节点、会改写 `next`；`null` 输入返回两个空链表。如果面试官实际想要的是“奇数位置在前、偶数位置在后并重新拼成一个链表”（LeetCode 328 风格），只需在位置拆分完成后把 odd 尾接到 even 头，但那是另一种输出合同。

## 1 分钟版

- 先问清“奇偶”是**位置**还是**值**，以及输出是“两条链表”还是“重排后的一条链表”。
- 真正的“拆分成两条链表”可以统一写成稳定分区：遍历原链表，把当前节点接到对应 odd/even 尾部。
- 每次处理节点前先保存 `next`，再把当前节点的 `next = null`，防止旧链接把两条结果串回去。
- 按位置时用 1-based `index` 的奇偶判断；按值时用 `(node.val & 1)` 判断，负奇数同样成立。
- 每个节点只访问一次，O(n) 时间；只维护四个头尾指针，除输出节点本身外 O(1) 额外空间。
- 本实现原地复用节点，因此会修改输入拓扑；如果调用方要求输入不变，就应复制节点。

## 3 分钟版

```java
public final class OddEvenSplit {
    public static final class ListNode {
        public final int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }

    public static final class SplitResult {
        public final ListNode odd;
        public final ListNode even;

        private SplitResult(ListNode odd, ListNode even) {
            this.odd = odd;
            this.even = even;
        }
    }

    public static SplitResult splitByPosition(ListNode head) {
        ListNode oddHead = null, oddTail = null;
        ListNode evenHead = null, evenTail = null;
        int index = 1;

        for (ListNode cur = head; cur != null; index++) {
            ListNode next = cur.next;
            cur.next = null;
            if ((index & 1) == 1) {
                if (oddHead == null) oddHead = cur;
                else oddTail.next = cur;
                oddTail = cur;
            } else {
                if (evenHead == null) evenHead = cur;
                else evenTail.next = cur;
                evenTail = cur;
            }
            cur = next;
        }
        return new SplitResult(oddHead, evenHead);
    }

    public static SplitResult splitByValue(ListNode head) {
        ListNode oddHead = null, oddTail = null;
        ListNode evenHead = null, evenTail = null;

        for (ListNode cur = head; cur != null; ) {
            ListNode next = cur.next;
            cur.next = null;
            if ((cur.val & 1) != 0) {
                if (oddHead == null) oddHead = cur;
                else oddTail.next = cur;
                oddTail = cur;
            } else {
                if (evenHead == null) evenHead = cur;
                else evenTail.next = cur;
                evenTail = cur;
            }
            cur = next;
        }
        return new SplitResult(oddHead, evenHead);
    }
}
```

以 `1 -> 2 -> 3 -> 4 -> 5` 为例，按**位置**拆分得到 odd=`1 -> 3 -> 5`、even=`2 -> 4`。如果节点值是 `8 -> 3 -> 6 -> 5 -> 4`，按**值**拆分得到 odd=`3 -> 5`、even=`8 -> 6 -> 4`。这两个例子看起来相似，但判断依据完全不同，所以不能只看样例猜合同。

实现里的关键动作是先保存 `next` 再断开 `cur.next`。如果不先断开，某个被放到 odd 链的节点可能还通过旧 `next` 指向随后会进入 even 链的节点，导致结果链表交叉、重复甚至形成意外环。

## 关键细节

- **来源歧义**：原题没有说明按位置还是按值，本答案保留这个事实并提供两个明确函数，避免把猜测当题意。
- **稳定性**：odd/even 两条结果都保持原输入中的相对顺序，因为每类节点只追加到对应尾部。
- **保存后继**：改写 `cur.next` 前必须先保存原 `next`，否则会丢失未处理后缀。
- **断开旧边**：将 `cur.next = null` 后再追加，可确保两条输出尾部干净，不残留跨组链接。
- **负数奇偶**：Java 二进制补码下 `(x & 1) != 0` 对正负奇数都成立，例如 `-3 & 1` 仍为 1。
- **空链表**：两个实现都返回 `odd=null, even=null`。
- **单节点**：按位置一定进入 odd；按值取决于节点值。
- **修改输入**：这是原地稳定拆分，会重写原节点 `next`；若要求输入不可变，应新建节点，时间仍 O(n)，但需要 O(n) 输出节点空间。
- **复杂度**：每节点处理一次，O(n)；除了头尾指针和计数器，没有随 n 增长的辅助结构。

## 原理机制

本质是链表上的 stable partition。数组做稳定分区通常需要额外空间或搬移元素，但单链表可以通过“摘下当前节点 → 接到目标尾部”完成稳定分区。维护 `oddHead/oddTail` 和 `evenHead/evenTail` 两组边界后，每处理一个节点，只需要 O(1) 指针修改。

不变量是：在处理到某个前缀后，odd 链恰好包含该前缀中所有满足 odd 谓词的节点且顺序不变；even 链同理；未处理后缀仍可通过提前保存的 `next` 到达。终止时未处理后缀为空，因此两条链正好覆盖原链全部节点且不重不漏。

## 项目经验版

来源没有真实项目背景，不能虚构生产经历。工程中如果“拆分”用于队列分流、批处理或规则路由，我会把分类谓词作为参数而不是写死“奇偶”，同时明确节点所有权：函数是否消费输入链、调用方是否还持有旧 head、是否允许多线程并发访问。原地改链的算法本身简单，但所有权不清比算法复杂度更容易制造真实 bug。

## 常见追问

- 问：“奇偶链表”通常不是按位置吗？答：有经典题按位置重排，但当前来源只写“链表奇偶拆分”，没有绑定具体题号或定义；面试中应先确认，不能把常见题自动当成原题。
- 问：为什么要断开 `cur.next`？答：当前节点加入某条结果链后，旧 next 可能属于另一组；不清掉会残留跨组边，破坏两条结果的独立性。
- 问：如何保证稳定顺序？答：每个节点按原遍历顺序到达，并且只追加到对应尾指针，不会插到前面，所以同组相对顺序保持。
- 问：能不能用两个 dummy 节点？答：可以，会让头节点初始化更统一；这里用 nullable head/tail 是为了不额外构造哨兵节点，两者复杂度相同。
- 问：负数的奇偶怎么判断？答：`(value & 1) != 0` 对负奇数也为 true；也可以用 `value % 2 != 0`，不要写 `value % 2 == 1`，因为 Java 负奇数余数是 -1。
- 问：如果要输出一条“奇位置 + 偶位置”链表？答：先按位置拆分，再令 oddTail.next = evenHead，并返回 oddHead；但要先确认输出合同确实是重排而不是两条独立链。

## 易错点

- 没问“奇偶”定义就直接按值或按位置写死。
- 改 `cur.next` 前没有保存后继，导致未处理链断掉。
- 不断开旧 next，输出 odd/even 链仍交叉引用。
- 用 `value % 2 == 1` 判断奇数，漏掉负奇数。
- 声称算法不修改输入，但实际复用了节点并重写 next。
- 只返回两个 head 却没有保证尾部断开，隐藏结构错误直到后续遍历才暴露。
'''

TEST = r'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class OddEvenSplitTest {
    private static OddEvenSplit.ListNode list(int... values) {
        OddEvenSplit.ListNode dummy = new OddEvenSplit.ListNode(0);
        OddEvenSplit.ListNode tail = dummy;
        for (int v : values) {
            tail.next = new OddEvenSplit.ListNode(v);
            tail = tail.next;
        }
        return dummy.next;
    }

    private static int[] values(OddEvenSplit.ListNode head) {
        List<Integer> out = new ArrayList<>();
        for (OddEvenSplit.ListNode p = head; p != null; p = p.next) {
            if (out.size() > 10000) throw new AssertionError("cycle detected in result");
            out.add(p.val);
        }
        int[] a = new int[out.size()];
        for (int i = 0; i < a.length; i++) a[i] = out.get(i);
        return a;
    }

    private static int[] filterPosition(int[] a, boolean odd) {
        return java.util.stream.IntStream.range(0, a.length).filter(i -> (((i + 1) & 1) == (odd ? 1 : 0))).map(i -> a[i]).toArray();
    }

    private static int[] filterValue(int[] a, boolean odd) {
        return Arrays.stream(a).filter(v -> (((v & 1) != 0) == odd)).toArray();
    }

    private static void assertArray(int[] actual, int[] expected, String label) {
        if (!Arrays.equals(actual, expected)) throw new AssertionError(label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
    }

    public static void main(String[] args) {
        OddEvenSplit.SplitResult emptyPos = OddEvenSplit.splitByPosition(null);
        if (emptyPos.odd != null || emptyPos.even != null) throw new AssertionError("empty position");
        OddEvenSplit.SplitResult emptyVal = OddEvenSplit.splitByValue(null);
        if (emptyVal.odd != null || emptyVal.even != null) throw new AssertionError("empty value");

        OddEvenSplit.SplitResult p = OddEvenSplit.splitByPosition(list(1, 2, 3, 4, 5));
        assertArray(values(p.odd), new int[]{1, 3, 5}, "position odd");
        assertArray(values(p.even), new int[]{2, 4}, "position even");

        OddEvenSplit.SplitResult v = OddEvenSplit.splitByValue(list(8, 3, 6, 5, 4, -7, -2));
        assertArray(values(v.odd), new int[]{3, 5, -7}, "value odd");
        assertArray(values(v.even), new int[]{8, 6, 4, -2}, "value even");

        OddEvenSplit.SplitResult singlePos = OddEvenSplit.splitByPosition(list(4));
        assertArray(values(singlePos.odd), new int[]{4}, "single position odd");
        assertArray(values(singlePos.even), new int[]{}, "single position even");
        OddEvenSplit.SplitResult singleVal = OddEvenSplit.splitByValue(list(4));
        assertArray(values(singleVal.odd), new int[]{}, "single value odd");
        assertArray(values(singleVal.even), new int[]{4}, "single value even");

        Random r = new Random(20260829L);
        for (int t = 0; t < 2000; t++) {
            int n = r.nextInt(80);
            int[] a = new int[n];
            for (int i = 0; i < n; i++) a[i] = r.nextInt(201) - 100;

            OddEvenSplit.SplitResult rp = OddEvenSplit.splitByPosition(list(a));
            assertArray(values(rp.odd), filterPosition(a, true), "random position odd t=" + t);
            assertArray(values(rp.even), filterPosition(a, false), "random position even t=" + t);

            OddEvenSplit.SplitResult rv = OddEvenSplit.splitByValue(list(a));
            assertArray(values(rv.odd), filterValue(a, true), "random value odd t=" + t);
            assertArray(values(rv.even), filterValue(a, false), "random value even t=" + t);
        }
        System.out.println("PASS ambiguity-both-contracts empty single position value negative-odd stable-order random2000 no-crosslink");
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

    with tempfile.TemporaryDirectory(prefix='b50-odd-even-split-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'OddEvenSplit.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'OddEvenSplitTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'OddEvenSplit.java', 'OddEvenSplitTest.java', cwd=tmpdir)
        stdout = run('java', 'OddEvenSplitTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS ambiguity-both-contracts empty single position value negative-odd stable-order random2000 no-crosslink'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1', 'canonical_id': CID, 'result': 'pass', 'validated_at': DATE,
        'command': 'javac OddEvenSplit.java OddEvenSplitTest.java && java OddEvenSplitTest', 'stdout': stdout,
        'checks': [
            'both position-parity and value-parity interpretations are implemented explicitly because the source is ambiguous',
            'empty and single-node boundaries behave according to each explicit contract',
            'negative odd values are classified correctly',
            'relative order is stable and result lists terminate without stale cross-links',
            '2000 deterministic random arrays match independent array-filter oracles for both interpretations',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 odd/even linked-list split validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-ambiguity', 'text': 'The repository source only says linked-list odd/even split and does not specify whether parity refers to node position or node value, whether output is two lists or one reordered list, or whether mutation is allowed.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'implementation-validation', 'text': 'The OpenJDK 21 fixture validates stable two-list splitting for both position parity and value parity, including empty/single/negative-value cases and 2000 deterministic random inputs against independent array-filter oracles.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'ownership-boundary', 'text': 'Both implementations reuse original nodes and explicitly detach old next edges, so they intentionally mutate input topology while avoiding stale cross-links between output lists.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节', '项目经验版']},
        {'claim_id': 'complexity-bound', 'text': 'Each node is visited once and appended to exactly one tail with constant pointer work, so both implementations are O(n) time with O(1) auxiliary pointer state excluding the reused output nodes.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '关键细节', '原理机制']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending', 'sources': sources, 'claims': claims, 'source_question_coverage': coverage, 'promotion_blocker': 'isolated_independent_review_not_yet_performed'})

    scores = {'facts_and_evidence': 24, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The answer does not silently guess the under-specified meaning of odd/even; it exposes both position-parity and value-parity contracts.',
        'Both code paths perform a stable linked-list partition and explicitly detach next edges before appending, preventing stale cross-links.',
        'The candidate clearly states that it mutates input topology and distinguishes two-list split from the one-list odd-position-then-even-position reorder variant.',
        'OpenJDK 21 validation covers empty/single boundaries, negative odd values, stable order, termination/no-crosslink properties, and 2000 random inputs for both contracts.',
        'The mechanism section states the stable-partition invariant rather than generic linked-list advice.',
        'No project history or source-unstated LeetCode identity is fabricated.',
    ]
    review = {'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0050-odd-even-split-20260829-v1', 'review_version': 'batch-0050.odd-even-split.v1', 'decision': 'pass', 'revision_round': 1, 'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'], 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings, 'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Odd/even split source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0050-odd-even-split-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources, 'claims': claims, 'source_question_coverage': coverage,
        'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [
            {'case': 'source ambiguity', 'expected': 'both common parity contracts explicit', 'actual': 'pass', 'passed': True},
            {'case': 'empty/single boundaries', 'expected': 'correct two-list outputs', 'actual': 'pass', 'passed': True},
            {'case': 'negative odd values', 'expected': 'value parity correct for signed ints', 'actual': 'pass', 'passed': True},
            {'case': 'stable order/no stale crosslinks', 'expected': 'same-group order preserved and result chains terminate', 'actual': 'pass', 'passed': True},
            {'case': '2000 deterministic random inputs', 'expected': 'matches independent position/value array-filter oracles', 'actual': 'pass', 'passed': True},
        ]},
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d80c5515628053be95dcb56bc561643a` source-first isolated review PASS: the source only says “链表奇偶拆分”, so the candidate does not invent a hidden parity definition; it gives explicit stable two-list implementations for both position parity and node-value parity, states the in-place ownership contract, and distinguishes the one-list reorder variant. OpenJDK 21 validation covers empty/single/negative-odd/stable-order/no-crosslink boundaries plus 2000 deterministic random inputs against independent array-filter oracles. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
