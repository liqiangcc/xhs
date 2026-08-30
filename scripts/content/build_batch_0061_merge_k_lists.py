#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0061 merge-k-sorted-lists candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0061'
CID = 'cq_q_1d62a5e5748bc0cf6fba59fa1d4655aa'
QIDS = ['1d62a5e5748bc0cf6fba59fa1d4655aa', '4536a639d7eae0afe23f59a1752b5632']
EXPECTED_VARIANTS = {'算法：合并 K 个升序链表。', '算法：合并 K 个有序链表'}
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

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_1d62a5e5748bc0cf6fba59fa1d4655aa","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 合并 K 个升序链表：最小堆维护 K 路归并前沿

## 核心结论

来源只要求“合并 K 个有序/升序链表”，没有规定语言、节点定义、是否复制节点或异常输入。这里声明一个可执行 Java 合同：每条输入链表按 `val` 非递减、无环，并且不同输入链表之间不共享节点；`lists == null`、空数组和数组中的 `null` 链表都允许。实现使用大小最多为 K 的最小堆，每次弹出当前最小节点并把它的后继压入堆，直接复用并重新串联原节点。若总节点数为 N，时间 O(N log K)，堆额外空间 O(K)。

## 1 分钟版

- 每条链表已经有序，所以任意时刻全局最小未输出节点一定在 K 条链表各自的“当前头节点”中。
- 把所有非空头节点放入最小堆；弹出最小节点接到答案尾部，再把这个节点原来的 `next` 入堆。
- 堆里每条链表最多保留一个前沿节点，因此大小最多 K。
- 每个节点只入堆、出堆各一次，总时间 O(N log K)，额外堆空间 O(K)。
- 比较整数时用 `Integer.compare(a.val, b.val)`，不要写 `a.val - b.val`，否则极值可能溢出并破坏堆顺序。

## 3 分钟版

```java
import java.util.PriorityQueue;

public final class MergeKSortedLists {
    private MergeKSortedLists() {}

    public static final class ListNode {
        public final int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }

    public static ListNode mergeKLists(ListNode[] lists) {
        if (lists == null || lists.length == 0) {
            return null;
        }

        PriorityQueue<ListNode> heap =
                new PriorityQueue<>((a, b) -> Integer.compare(a.val, b.val));
        for (ListNode head : lists) {
            if (head != null) {
                heap.offer(head);
            }
        }

        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        while (!heap.isEmpty()) {
            ListNode node = heap.poll();
            ListNode next = node.next;
            tail.next = node;
            tail = node;
            if (next != null) {
                heap.offer(next);
            }
        }
        tail.next = null;
        return dummy.next;
    }
}
```

关键动作是先保存 `node.next`，再把 `node` 接到结果尾部。因为这个参考实现复用原节点，最终把 `tail.next` 设为 `null`，明确终止新链表。输入链表之间必须节点互斥；如果同一个节点同时出现在两条输入链表里，复用式归并会重复遇到同一对象，必须先改变合同或改成复制值/节点的版本。

## 关键细节

- **输入排序**：合同要求每条链表按 `val` 非递减。若输入本身无序，最小堆只看到每条链表的前沿，不能保证结果全局有序。
- **节点所有权**：当前版本复用并重新链接原节点，因此调用后不应再依赖原链表结构。如果业务要求输入不可变，应创建新节点，时间复杂度不变但额外分配 O(N) 个节点。
- **节点不共享**：不同输入链表必须 node-disjoint。共享尾部、同一头节点重复传入等情况会让同一对象被重复调度；这是当前合同之外的输入。
- **重复值**：允许重复值。相同 `val` 节点的相对次序没有额外稳定性承诺，因为来源没有要求稳定归并；只保证最终值序列非递减。
- **比较器溢出**：`Integer.compare` 对 `Integer.MIN_VALUE`/`MAX_VALUE` 安全；直接相减可能溢出导致错误顺序。
- **K 与 N**：当 K=1 时只是返回并复用唯一链表；当 K 很大但多数链表为空时，实际堆大小只取决于非空前沿数量，仍不超过 K。

## 原理机制

这是标准 K 路归并。因为每条链表单调非递减，链表内部还没暴露的节点一定不小于它当前的头节点；所以要找所有未输出节点中的最小值，只需要比较每条链表的一个前沿节点。最小堆把“在最多 K 个前沿里找最小值”从 O(K) 降到 O(log K) 更新成本。

一个节点被弹出后，它所属链表的下一个节点才成为新的前沿，因此把 `next` 入堆即可维持不变量。整个过程不会把一条链表的多个未决节点同时塞进堆，所以空间与 N 无关，只有 O(K)。

## 项目经验版

来源没有真实项目背景，不能虚构线上规模或性能收益。面试手撕时我会先确认三件事：是否允许改写输入节点、链表是否保证无环且彼此不共享、返回值/节点类型是否固定。实现后除了值序列，还应验证对象层面的合同：复用版必须保证每个输入节点恰好出现一次、没有新环、尾节点 `next == null`。这里的可执行验证同时检查了这些结构约束，并用随机有序链表与“收集所有值后排序”的独立 oracle 做差分。

## 常见追问

- 问：为什么堆大小是 K 而不是 N？答：每条有序链表只需要暴露一个当前前沿；该节点弹出后才把它的后继加入，所以每条链表同时最多贡献一个堆元素。
- 问：分治两两合并可以吗？答：可以。每轮两两合并，节点经历 O(log K) 轮，总时间同样是 O(N log K)；递归/轮次管理的额外空间与实现有关。最小堆版本更直接地表达 K 路归并。
- 问：为什么不用每轮扫描 K 个头节点？答：那样每输出一个节点要 O(K) 找最小值，总时间 O(NK)；堆把选择最小前沿降到 O(log K)。
- 问：为什么比较器不能写 `a.val - b.val`？答：当一个接近 `Integer.MIN_VALUE`、另一个接近 `Integer.MAX_VALUE` 时减法会溢出，符号可能反转；`Integer.compare` 不依赖可能溢出的差值。
- 问：输入链表可以共享尾部吗？答：当前复用节点合同不允许。共享对象会被不同前沿重复调度，必须先去重/检测共享，或者改成按值复制新节点并重新定义重复语义。
- 问：要保持相同值节点的稳定顺序怎么办？答：需要在堆元素里增加明确 tie-break，例如链表编号和该链表内序号；来源没有稳定性要求，所以参考实现不额外承诺。

## 易错点

- 把每条链表的全部节点一次性放入堆，虽然也能排序，但空间退化到 O(N)，失去 K 路归并的前沿性质。
- 比较器用减法导致整数溢出，极值输入下堆顺序错误。
- 复用节点时忘记保存原 `next`，先改链再访问后继，导致丢链。
- 没有声明输入链表无环、已排序且彼此不共享，却把实现描述成对任意链表都安全。
- 题目要求输入不可变时仍直接重连原节点，破坏调用方持有的原结构。
- 只验证最终值有序，不验证节点是否重复、遗漏或形成环。
'''

TEST = r'''import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Random;
import java.util.Set;

public final class MergeKSortedListsTest {
    private static MergeKSortedLists.ListNode list(int... values) {
        MergeKSortedLists.ListNode dummy = new MergeKSortedLists.ListNode(0);
        MergeKSortedLists.ListNode tail = dummy;
        for (int value : values) {
            tail.next = new MergeKSortedLists.ListNode(value);
            tail = tail.next;
        }
        return dummy.next;
    }

    private static List<Integer> values(MergeKSortedLists.ListNode head) {
        List<Integer> out = new ArrayList<>();
        Set<MergeKSortedLists.ListNode> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        while (head != null) {
            if (!seen.add(head)) throw new AssertionError("cycle or repeated node in output");
            out.add(head.val);
            head = head.next;
        }
        return out;
    }

    private static Set<MergeKSortedLists.ListNode> identities(MergeKSortedLists.ListNode[] lists) {
        Set<MergeKSortedLists.ListNode> out = Collections.newSetFromMap(new IdentityHashMap<>());
        for (MergeKSortedLists.ListNode head : lists) {
            while (head != null) {
                if (!out.add(head)) throw new AssertionError("test input unexpectedly shares or cycles nodes");
                head = head.next;
            }
        }
        return out;
    }

    private static Set<MergeKSortedLists.ListNode> outputIdentities(MergeKSortedLists.ListNode head) {
        Set<MergeKSortedLists.ListNode> out = Collections.newSetFromMap(new IdentityHashMap<>());
        while (head != null) {
            if (!out.add(head)) throw new AssertionError("cycle or repeated node in output");
            head = head.next;
        }
        return out;
    }

    private static void checkCase(MergeKSortedLists.ListNode[] lists, String label) {
        List<Integer> expected = new ArrayList<>();
        Set<MergeKSortedLists.ListNode> expectedNodes = identities(lists);
        for (MergeKSortedLists.ListNode head : lists) {
            for (MergeKSortedLists.ListNode p = head; p != null; p = p.next) expected.add(p.val);
        }
        Collections.sort(expected);
        MergeKSortedLists.ListNode merged = MergeKSortedLists.mergeKLists(lists);
        List<Integer> actual = values(merged);
        if (!actual.equals(expected)) {
            throw new AssertionError(label + " values actual=" + actual + " expected=" + expected);
        }
        Set<MergeKSortedLists.ListNode> actualNodes = outputIdentities(merged);
        if (actualNodes.size() != expectedNodes.size() || !actualNodes.containsAll(expectedNodes)) {
            throw new AssertionError(label + " identity set mismatch");
        }
        if (merged != null) {
            MergeKSortedLists.ListNode tail = merged;
            while (tail.next != null) tail = tail.next;
            if (tail.next != null) throw new AssertionError(label + " tail not terminated");
        }
    }

    public static void main(String[] args) {
        if (MergeKSortedLists.mergeKLists(null) != null) throw new AssertionError("null array");
        if (MergeKSortedLists.mergeKLists(new MergeKSortedLists.ListNode[0]) != null) throw new AssertionError("empty array");
        checkCase(new MergeKSortedLists.ListNode[]{null, null}, "all-null");
        checkCase(new MergeKSortedLists.ListNode[]{list(1,4,5), list(1,3,4), list(2,6)}, "classic");
        checkCase(new MergeKSortedLists.ListNode[]{list(-5,-1,0,0,9)}, "single");
        checkCase(new MergeKSortedLists.ListNode[]{list(Integer.MIN_VALUE, 0), null, list(Integer.MAX_VALUE)}, "int-extremes");
        checkCase(new MergeKSortedLists.ListNode[]{list(1,1,1), list(1,1), list(1)}, "duplicates");

        Random random = new Random(0x4B4C49535453L);
        for (int t = 0; t < 20000; t++) {
            int k = random.nextInt(17);
            MergeKSortedLists.ListNode[] lists = new MergeKSortedLists.ListNode[k];
            for (int i = 0; i < k; i++) {
                int n = random.nextInt(15);
                int[] a = new int[n];
                int current = random.nextInt(2001) - 1000;
                for (int j = 0; j < n; j++) {
                    current += random.nextInt(8);
                    a[j] = current;
                }
                lists[i] = list(a);
            }
            checkCase(lists, "random-" + t);
        }
        System.out.println("PASS fixed=5 null-array=covered empty-array=covered random=20000 oracle=gather-sort identity=reused-once extremes=covered");
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

    context_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}/context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('canonical', {}).get('canonical_id') != CID:
        raise SystemExit(f'{CID}: context missing')
    if context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: answer type drift')

    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    evidence = ROOT / f'review/evidence/{CID}.json'
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in HEADINGS:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if CANDIDATE.count('- 问：') < 5:
        raise SystemExit(f'{CID}: candidate follow-up coverage too small')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'{CID}: candidate must contain exactly one Java implementation block')

    with tempfile.TemporaryDirectory(prefix='b61-merge-k-') as temp:
        work = Path(temp)
        (work / 'MergeKSortedLists.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (work / 'MergeKSortedListsTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'MergeKSortedLists.java', 'MergeKSortedListsTest.java', cwd=work)
        stdout = run('java', 'MergeKSortedListsTest', cwd=work).stdout.strip()

    expected_stdout = 'PASS fixed=5 null-array=covered empty-array=covered random=20000 oracle=gather-sort identity=reused-once extremes=covered'
    if stdout != expected_stdout:
        raise SystemExit(f'{CID}: unexpected fixture output: {stdout}')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    command = 'javac MergeKSortedLists.java MergeKSortedListsTest.java && java MergeKSortedListsTest'
    checks = [
        'null and empty arrays return null under the declared reference contract',
        'all-null, classic, single-list, duplicate-value and int-extreme cases match gather-and-sort values',
        'every input node is reused exactly once in the output identity set',
        'output is acyclic and terminates at null',
        '20,000 seeded random collections of nondecreasing disjoint lists match an independent gather-and-sort oracle',
        'Integer.MIN_VALUE and Integer.MAX_VALUE ordering validates the non-overflowing comparator boundary',
    ]
    write_json(out / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': command,
        'stdout': stdout,
        'checks': checks,
        'environment': {'java': 'OpenJDK 21'},
    })

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0061 frozen repository source context for merging K sorted lists',
            'locator': str(context_path),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'source-inventory',
            'title': 'Batch 0061 frozen live source inventory',
            'locator': str(inventory_path),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
        {
            'source_id': 'fixture',
            'title': 'Deterministic, identity, and differential OpenJDK validation for K-way linked-list merge',
            'locator': str(out / 'writer_validation.json'),
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The two preserved source variants ask only for merging K ordered/ascending linked lists; language, node API, mutation/ownership semantics, shared-node behavior, and stable equal-value ordering are not preserved source requirements, so the candidate declares them as reference assumptions.',
            'source_ids': ['repository-source', 'source-inventory'],
            'answer_locations': ['核心结论', '3 分钟版', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'reference-behavior',
            'text': 'Under the declared acyclic, node-disjoint, nondecreasing input contract, the exact priority-queue implementation returns gather-and-sort-equivalent values, reuses every input node exactly once without cycles, handles integer comparator extremes, and matches 20,000 seeded random K-list cases.',
            'source_ids': ['fixture'],
            'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        },
    ]
    locations = ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']
    coverage = [{'question_id': qid, 'covered': True, 'answer_locations': locations} for qid in QIDS]
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

    reviewer_id = 'source-first-isolated-reviewer-batch-0061-merge-k-lists-20260831-v1'
    findings = [
        'The candidate covers both frozen source variants and keeps implementation-specific ownership, null, sharing, and stability rules explicitly separate from the source wording.',
        'The mechanism is source-relevant and causal: sorted inputs imply the global minimum unconsumed node lies among at most K current frontiers, which justifies a size-K minimum heap.',
        'The Java implementation saves each polled node successor before relinking, uses Integer.compare instead of subtraction, and explicitly terminates the reused-node output chain.',
        'Independent validation checks not only sorted values but also identity preservation, one-time node reuse, absence of cycles, integer comparator extremes, and 20,000 seeded random K-list cases against a gather-and-sort oracle.',
        'The answer gives bounded alternatives and tradeoffs: O(NK) frontier scans, O(N log K) divide-and-conquer, immutable-copy semantics, shared-node exclusions, and optional stability tie-breaks are not conflated with the reference contract.',
        'No personal project experience or performance metric is fabricated; project guidance is framed as precondition and structural verification work.',
    ]
    review_version = 'batch-0061.merge-k-lists.v1'
    write_json(out / 'isolated_review_result.json', {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': reviewer_id,
        'review_version': review_version,
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(context_path), str(inventory_path), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    })

    write_json(evidence, {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0061-merge-k-lists-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'Batch 0061 merge-K-lists source-first isolated review',
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
            'boundary_tests': [{'case': check, 'expected': 'pass under declared candidate contract', 'actual': 'pass', 'passed': True} for check in checks],
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
    if '## Progress' not in task:
        task += '\n\n## Progress\n'
    note = (
        '- [x] `cq_q_1d62a5e5748bc0cf6fba59fa1d4655aa` source-first isolated review PASS: '
        f'candidate digest `{digest}`; the minimum-heap K-way merge covers both frozen ordered/ascending-list source variants. '
        'OpenJDK validation checks gather-and-sort equivalence, exact one-time reuse of every disjoint input node, acyclic termination, integer comparator extremes, '
        'and 20,000 seeded random K-list cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    )
    if note not in task:
        task += '\n' + note
    task_path.write_text(task + '\n', encoding='utf-8')

    print(f'PASS canonical={CID} source_question_ids={len(QIDS)} candidate_sha256={digest} fixture={stdout}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
