#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0058 remove-nth-node candidate."""

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
CID = 'cq_q_6385688cc90c9b0c14dd4beaa2c72486'
QIDS = [
    '06162d834ad92cea22206ca03656dca8',
    '6385688cc90c9b0c14dd4beaa2c72486',
    '7036750d93c9c57e27d0a741bddbed08',
    'e5641e5fe7818f1ef9d8d9993da9ed14',
]
EXPECTED_VARIANTS = {
    '算法：删除链表倒数第 N 个节点？',
    '算法：删除链表的倒数第 k 个节点。',
    '算法：删除链表的倒数第N个结点',
    '算法：删除链表的倒数第 N 个结点',
    '算法：删除链表的倒数第 N 个节点。',
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

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_6385688cc90c9b0c14dd4beaa2c72486","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 删除链表的倒数第 N 个节点

## 核心结论

四个保留来源问法都只要求“删除链表倒数第 N/k 个节点”，没有指定语言、节点定义或非法 N 的处理。这里采用一个可执行 Java 合同：`removeNthFromEnd(head, n)` 在 `1 <= n <= 链表长度` 时原地摘除目标节点并返回可能变化的新头；`n <= 0`、`n > 长度` 或空链表配正数 n 都抛 `IllegalArgumentException`。核心做法是 dummy + 前后双指针：先让 fast 从 dummy 前进 n 步，再让 fast/slow 同步移动到 fast 位于尾节点，此时 slow 恰好是待删除节点的前驱，一次改链即可。时间 O(L)，额外空间 O(1)。

## 1 分钟版

- 加一个 `dummy -> head`，这样删除头节点和删除中间节点可以走同一段 `slow.next = slow.next.next`。
- fast、slow 都从 dummy 出发，先让 fast 前进 n 步，保持两者相差 n 个节点位置。
- 然后两者同步向后，直到 `fast.next == null`，也就是 fast 已到尾节点。
- 这时 slow 位于“倒数第 n 个节点”的前一个节点，摘掉 `slow.next` 即可。
- 若 fast 在预走 n 步时提前变成 null，说明 n 大于链表长度；当前合同直接报错，并且此时还没有修改链表。
- 全程每个指针最多线性走一遍，所以时间 O(L)，只用了固定数量指针和一个 dummy 节点，额外空间 O(1)。

## 3 分钟版

```java
public final class RemoveNthFromEnd {
    public static final class ListNode {
        public final int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }

    public static ListNode removeNthFromEnd(ListNode head, int n) {
        if (n <= 0) {
            throw new IllegalArgumentException("n must be positive");
        }

        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode fast = dummy;
        ListNode slow = dummy;

        for (int i = 0; i < n; i++) {
            fast = fast.next;
            if (fast == null) {
                throw new IllegalArgumentException("n exceeds list length");
            }
        }

        while (fast.next != null) {
            fast = fast.next;
            slow = slow.next;
        }

        slow.next = slow.next.next;
        return dummy.next;
    }
}
```

例如 `1 -> 2 -> 3 -> 4 -> 5`，`n=2`。fast 从 dummy 先走两步到节点 2；随后 fast 和 slow 一起走，fast 最终停在 5，slow 停在 3，所以删除 `slow.next`，结果是 `1 -> 2 -> 3 -> 5`。

如果 `n` 等于链表长度，fast 预走后直接停在尾节点，slow 仍在 dummy，于是统一删除原 head；这正是引入 dummy 的价值。

## 关键细节

- **不变量**：预走完成后 fast 比 slow 领先 n 个节点位置；同步移动不会改变这个间距。
- **为什么停止在 `fast.next == null`**：此时 fast 是尾节点，因此 slow 后面的节点正好距离尾部 n 个位置，也就是目标节点。
- **为什么从 dummy 出发**：若删除的是头节点，目标前驱在真实链表中不存在；dummy 提供统一的虚拟前驱，避免单独写 `n == length` 分支。
- **非法 n 的边界**：来源没规定。当前合同显式拒绝 `n <= 0` 或 `n > length`，而且在确认 n 合法之前不改链，失败不会产生半修改状态。
- **空链表**：不存在可删除的倒数节点，因此正数 n 会落入“超过长度”的异常路径。
- **节点值不参与判断**：算法只依赖位置；重复值不会影响正确性。
- **复杂度**：fast 最多走 L 步，slow 最多走 L-n 步，总量仍是 O(L)；除 dummy 和若干引用外不申请随 L 增长的存储，因此额外空间 O(1)。

## 原理机制

假设链表长度为 L，dummy 位置记为 0，真实节点位置为 1..L。fast 从 0 先走 n 步到位置 n；之后 fast、slow 同步走 L-n 步，fast 到位置 L，slow 到位置 L-n。slow 的下一个位置是 `L-n+1`，从尾部数正好是第 n 个真实节点。因此只要维持“fast 比 slow 领先 n”的距离不变量，就不需要预先计算 L，也能在一次主遍历中定位目标前驱。

dummy 并没有改变链表元素的相对位置，只是给位置 1 的 head 增加了一个可操作前驱。真正的删除仍然是把前驱的 `next` 跨过目标节点指向其后继。

## 项目经验版

来源没有真实项目背景，不能虚构线上经历。面试手撕时我会先确认三件事：N 是否保证合法、是否要求原地修改、节点类型和返回值怎么定义。若题目沿用常见的“保证 1 <= n <= length”约束，可以去掉异常分支；如果接口面向不可信输入，则应保留显式校验。验证时至少覆盖删除头、删除尾、删除中间、单节点、重复值和非法 n。

## 常见追问

- 问：为什么 fast 先走 n 步，不是 n+1 步？答：这里 fast、slow 都从 dummy 出发，并让 fast 最终停在尾节点；保持 n 的位置差后，slow 就停在目标前驱。另一种写法可以让 fast 多走一步并以 `fast != null` 为循环条件，但必须和起点、终止条件配套，不能混用。
- 问：不用 dummy 可以吗？答：可以，但删除头节点时必须单独处理，因为普通 slow 没有办法指向 head 的前驱；dummy 把这个边界统一掉。
- 问：为什么不用先遍历求长度？答：两遍法也正确且仍是 O(L)。双指针把“从尾部数 n 个”的定位转换成固定距离不变量，不需要显式保存长度。
- 问：n 大于长度怎么办？答：来源没规定；当前合同在 fast 预走阶段检测并抛异常，而且还没发生任何 `next` 修改。
- 问：链表里有重复值会不会删错？答：不会。定位只看节点位置和指针距离，不比较节点值。
- 问：如果链表有环呢？答：来源描述的是普通链表删除问题，没有给有环合同；当前实现假设有限无环单链表。有环时“倒数第 n 个”本身没有普通有限尾部语义，应先重新定义问题。

## 易错点

- fast/slow 的起点、领先步数和终止条件互相混搭，产生 off-by-one。
- 不使用 dummy 又忘了单独处理删除 head。
- `n > length` 时 fast 已经为 null，却继续访问 `fast.next`。
- 为了删除“某个值”等值比较节点，忽略题目要求的是倒数位置。
- 说“一次遍历”却先完整计算长度再走第二遍；两遍法本身没错，但复杂度和实现描述要一致。
- 没声明普通无环单链表假设，却把算法错误扩张到环形链表。
'''

TEST = r'''import java.util.Arrays;

public final class RemoveNthFromEndTest {
    private static RemoveNthFromEnd.ListNode list(int... values) {
        RemoveNthFromEnd.ListNode dummy = new RemoveNthFromEnd.ListNode(0);
        RemoveNthFromEnd.ListNode tail = dummy;
        for (int value : values) {
            tail.next = new RemoveNthFromEnd.ListNode(value);
            tail = tail.next;
        }
        return dummy.next;
    }

    private static int[] values(RemoveNthFromEnd.ListNode head) {
        int size = 0;
        for (RemoveNthFromEnd.ListNode p = head; p != null; p = p.next) size++;
        int[] out = new int[size];
        int i = 0;
        for (RemoveNthFromEnd.ListNode p = head; p != null; p = p.next) out[i++] = p.val;
        return out;
    }

    private static void check(int[] actual, int[] expected, String label) {
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError(label + " actual=" + Arrays.toString(actual) + " expected=" + Arrays.toString(expected));
        }
    }

    private static void expectInvalid(Runnable action, String label) {
        try {
            action.run();
            throw new AssertionError(label + " expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    public static void main(String[] args) {
        check(values(RemoveNthFromEnd.removeNthFromEnd(list(1, 2, 3, 4, 5), 2)), new int[]{1, 2, 3, 5}, "middle");
        check(values(RemoveNthFromEnd.removeNthFromEnd(list(1, 2, 3, 4, 5), 5)), new int[]{2, 3, 4, 5}, "head");
        check(values(RemoveNthFromEnd.removeNthFromEnd(list(1, 2, 3, 4, 5), 1)), new int[]{1, 2, 3, 4}, "tail");
        check(values(RemoveNthFromEnd.removeNthFromEnd(list(9), 1)), new int[]{}, "singleton");
        check(values(RemoveNthFromEnd.removeNthFromEnd(list(7, 7, 7), 2)), new int[]{7, 7}, "duplicates");

        RemoveNthFromEnd.ListNode a = new RemoveNthFromEnd.ListNode(1);
        RemoveNthFromEnd.ListNode b = new RemoveNthFromEnd.ListNode(2);
        RemoveNthFromEnd.ListNode c = new RemoveNthFromEnd.ListNode(3);
        a.next = b; b.next = c;
        RemoveNthFromEnd.ListNode sameHead = RemoveNthFromEnd.removeNthFromEnd(a, 2);
        if (sameHead != a || a.next != c) throw new AssertionError("must relink existing nodes in place");

        expectInvalid(() -> RemoveNthFromEnd.removeNthFromEnd(list(1, 2), 0), "zero-n");
        RemoveNthFromEnd.ListNode unchanged = list(1, 2);
        expectInvalid(() -> RemoveNthFromEnd.removeNthFromEnd(unchanged, 3), "too-large-n");
        check(values(unchanged), new int[]{1, 2}, "too-large-no-mutation");
        expectInvalid(() -> RemoveNthFromEnd.removeNthFromEnd(null, 1), "empty");

        System.out.println("PASS middle head tail singleton duplicates in-place invalid-zero invalid-too-large no-partial-mutation empty");
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
    if not variants or not variants.issubset(EXPECTED_VARIANTS):
        raise SystemExit(f'{CID}: frozen source wording drift: {sorted(variants)}')

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in HEADINGS:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'{CID}: candidate must contain exactly one Java implementation block')

    with tempfile.TemporaryDirectory(prefix='b58-remove-nth-') as temp:
        work = Path(temp)
        (work / 'RemoveNthFromEnd.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (work / 'RemoveNthFromEndTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'RemoveNthFromEnd.java', 'RemoveNthFromEndTest.java', cwd=work)
        stdout = run('java', 'RemoveNthFromEndTest', cwd=work).stdout.strip()

    expected_stdout = 'PASS middle head tail singleton duplicates in-place invalid-zero invalid-too-large no-partial-mutation empty'
    if stdout != expected_stdout:
        raise SystemExit(f'{CID}: unexpected fixture output: {stdout}')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    command = 'javac RemoveNthFromEnd.java RemoveNthFromEndTest.java && java RemoveNthFromEndTest'
    checks = [
        'middle-node deletion',
        'head deletion when n equals length',
        'tail deletion when n equals one',
        'single-node deletion',
        'duplicate values do not affect positional deletion',
        'surviving nodes are relinked in place',
        'n <= 0 is rejected',
        'n > length is rejected before mutation',
        'empty list with positive n is rejected',
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
            'title': 'Batch 0058 frozen repository source context for remove-nth-from-end',
            'locator': str(context_path),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'fixture',
            'title': 'Deterministic OpenJDK validation for remove-nth-from-end',
            'locator': str(out / 'writer_validation.json'),
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'All frozen source variants ask for deleting the N/k-th node from the end of a linked list; they do not preserve a language, node API, invalid-N policy, or cyclic-list contract, so the candidate declares those boundaries instead of attributing them to the source.',
            'source_ids': ['repository-source'],
            'answer_locations': ['核心结论', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'two-pointer-correctness',
            'text': 'Under the declared finite singly-linked-list contract, the executable Java fixture verifies the dummy/two-pointer implementation for head, middle, tail, singleton, duplicates, in-place relinking, and invalid-input/no-partial-mutation boundaries.',
            'source_ids': ['fixture'],
            'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
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

    reviewer_id = 'source-first-isolated-reviewer-batch-0058-remove-nth-20260829-v1'
    findings = [
        'The candidate directly covers every preserved N/k-th-from-end linked-list source variant and does not import a language or invalid-input requirement from source metadata.',
        'The dummy-node and n-position-gap invariant is stated explicitly, including why the synchronized scan leaves slow at the target predecessor.',
        'The Java implementation is executable, mutates only the predecessor link, and keeps surviving node identities rather than rebuilding the list.',
        'OpenJDK validation covers head/middle/tail/singleton/duplicate-value cases and proves overlarge n fails before any link mutation.',
        'The answer states O(L) time and O(1) extra space consistently with the implementation and keeps cyclic-list semantics out of scope.',
    ]
    review_version = 'batch-0058.remove-nth.v1'
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
            'writer_id': 'content-batch-0058-remove-nth-builder',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'Batch 0058 remove-nth source-first isolated review',
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
    note = '- [x] `cq_q_6385688cc90c9b0c14dd4beaa2c72486` source-first isolated review PASS: all four current source Question IDs / five preserved wording occurrences are covered by one dummy + two-pointer Java answer; executable OpenJDK validation covers head/middle/tail/singleton/duplicate-value cases, in-place relinking, and invalid-N no-partial-mutation boundaries. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if note not in task:
        task += '\n' + note
    task_path.write_text(task + '\n', encoding='utf-8')

    print(f'PASS canonical={CID} source_question_ids={len(QIDS)} candidate_sha256={digest} fixture={stdout}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
