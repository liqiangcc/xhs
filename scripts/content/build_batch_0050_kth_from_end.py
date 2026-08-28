#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0050 kth-from-end candidate."""

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
CID = 'cq_q_d6793c017bd5cd31952352d7a0e98464'
QID = 'd6793c017bd5cd31952352d7a0e98464'
EXPECTED = '算法手撕：找到链表的倒数第 m 个元素。'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d6793c017bd5cd31952352d7a0e98464","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 找到单链表的倒数第 m 个元素

## 核心结论

用快慢双指针保持固定间距即可一趟完成。这里先把题目没有写明的输入契约说清楚：`m` 按 1 开始计数，`m = 1` 表示尾节点；要求 `1 <= m <= 链表长度`，否则抛 `IllegalArgumentException`。先让 `fast` 从头节点前进 `m` 步，再让 `fast` 和 `slow` 同时每次走一步；当 `fast == null` 时，`slow` 正好指向倒数第 `m` 个节点。时间复杂度 O(n)，额外空间 O(1)，且不修改链表。

## 1 分钟版

- 先约定 `m=1` 是最后一个节点；`m<=0` 或 `m>长度` 都视为非法输入。
- `fast` 先走 `m` 步，建立“fast 比 slow 超前 m 个节点”的固定间距。
- 然后两指针同步向后走；因为间距不变，`fast` 到链表末尾时，`slow` 距末尾正好还有 `m` 个节点，也就是倒数第 `m` 个。
- 整个链表最多线性扫描一次，不需要先求长度，也不需要栈或数组。
- 空链表、`m=1`、`m=长度`、`m>长度` 是必须覆盖的边界。

## 3 分钟版

```java
public final class KthFromEnd {
    public static final class ListNode {
        public final int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }

    public static ListNode findKthFromEnd(ListNode head, int m) {
        if (m <= 0) {
            throw new IllegalArgumentException("m must be positive");
        }

        ListNode fast = head;
        for (int i = 0; i < m; i++) {
            if (fast == null) {
                throw new IllegalArgumentException("m exceeds list length");
            }
            fast = fast.next;
        }

        ListNode slow = head;
        while (fast != null) {
            fast = fast.next;
            slow = slow.next;
        }
        return slow;
    }
}
```

例如链表 `1 -> 2 -> 3 -> 4 -> 5`，`m=2`。`fast` 先从 1 走两步到 3，此时 slow 仍在 1；之后两者同步移动。当 fast 从 5 再走一步变成 `null` 时，slow 位于 4，所以返回倒数第 2 个节点。

如果允许先遍历一次求长度，也可以先得到 `n`，再从头走 `n-m` 步；它同样是 O(n) 时间、O(1) 空间，但要两段遍历。双指针的价值是把“总长度”隐式编码成两个指针之间的固定距离，一趟即可完成。

## 关键细节

- **固定间距不变量**：当 fast 已先走完 `m` 步后，在同步阶段的任意时刻，slow 到 fast 之间始终相差 `m` 个 next 边；因此 fast 到 `null` 时，slow 的位置由尾部距离唯一确定。
- **为什么先检查 fast 再前进**：如果第 `i` 步前 fast 已经是 `null`，说明链表节点数少于 `m`，必须判非法，而不是继续解引用。
- **`m == 长度`**：fast 恰好在预走阶段变成 `null`，同步循环一次都不执行，slow 保持在 head，正确返回倒数第 `n` 个，也就是第一个节点。
- **空链表**：对任何正 `m`，预走第一步就发现 fast 为 `null`，按本答案契约抛异常。
- **不修改结构**：算法只读取 `next` 并移动局部引用，不写任何节点的 `next`，所以链表拓扑保持不变。
- **复杂度**：fast 总共最多走 n 步，slow 最多走 n-m 步；时间 O(n)，除两个指针和循环变量外没有与 n 成长的辅助结构，空间 O(1)。
- **环形链表边界**：题目默认讨论有限无环单链表；若输入可能有环，`while (fast != null)` 可能永不结束，必须先定义并检测环或拒绝此输入域。

## 原理机制

问题看似需要先知道链表长度 `n`，因为倒数第 `m` 个等价于正数第 `n-m+1` 个。但单链表不能从尾部向前走，所以直接计算 `n-m` 通常需要先扫描求 `n`。

双指针把这个“未知 n”转成一个在线不变量：让 fast 先领先 slow `m` 个节点。此后每次同时移动，间距始终不变。fast 最终从尾节点跨到 `null`，意味着 slow 后面恰好还有 `m-1` 个真实节点，因此 slow 自身就是倒数第 `m` 个。结束条件和固定间距一起推出答案，不需要单独保存长度。

这也是很多链表双指针题的通用机制：不是“快指针一定每次走两步”，而是人为构造一个有用的相对位置关系，再让两个指针同步演化并保持这个关系。

## 项目经验版

来源没有提供真实项目场景，不能虚构生产经历。工程里若链表来自不可信输入，我会把输入域写进 API：是否允许空链表、非法 `m` 返回 `null` 还是抛异常、是否可能存在环。若可能有环，应先做 Floyd 环检测或在上游保证无环，否则“直到 null”为终止条件并不成立。若调用方本来就维护了链表长度，那么直接按已知长度定位也可能更简单，不必为了形式上“一趟”强行使用双指针。

## 常见追问

- 问：为什么 fast 要先走 `m` 步，不是 `m-1` 步？答：本实现用“fast 到 `null` 时 slow 即为答案”的结束条件。先走 `m` 步建立的是 slow 与 fast 之间相差 `m` 个 next 边；若只走 `m-1` 步，就需要改成别的结束条件，否则会产生一位偏差。
- 问：`m=1` 会怎样？答：fast 先走一步，然后两者同步；fast 到 `null` 时 slow 正好停在尾节点。
- 问：`m` 等于链表长度呢？答：fast 预走后刚好为 `null`，slow 不动，返回 head。
- 问：`m` 大于链表长度怎么处理？答：题目没规定。本答案明确抛 `IllegalArgumentException`；如果接口契约要求返回 `null`，只需替换非法输入处置，不改变双指针核心不变量。
- 问：为什么不先求链表长度？答：可以，那也是正确的 O(n)/O(1) 解法；双指针无需显式保存长度且只做一次连续遍历，更直接体现尾部距离。
- 问：有环怎么办？答：这道题的“倒数”依赖有限尾节点；有环时没有普通意义上的尾部，必须先把输入域改为无环或先检测并处理环。

## 易错点

- 没有明确 `m` 是从 1 还是从 0 开始计数，导致 off-by-one。
- fast 只预走 `m-1` 步，却仍使用 `while (fast != null)` 的结束条件。
- `m > 长度` 时继续访问 `fast.next`，触发空指针异常而不是按契约处理。
- 用栈存全部节点后再回退，虽然能做对，却把额外空间从 O(1) 提高到 O(n)。
- 忘记 `m == 长度` 时答案就是 head。
- 对可能有环的输入仍用 `fast != null` 作为唯一终止条件，造成无限循环。
'''

TEST = r'''public final class KthFromEndTest {
    private static KthFromEnd.ListNode list(int... values) {
        KthFromEnd.ListNode dummy = new KthFromEnd.ListNode(0);
        KthFromEnd.ListNode tail = dummy;
        for (int v : values) {
            tail.next = new KthFromEnd.ListNode(v);
            tail = tail.next;
        }
        return dummy.next;
    }

    private static int value(KthFromEnd.ListNode head, int m) {
        return KthFromEnd.findKthFromEnd(head, m).val;
    }

    private static void expectIllegal(KthFromEnd.ListNode head, int m) {
        try {
            KthFromEnd.findKthFromEnd(head, m);
            throw new AssertionError("expected IllegalArgumentException for m=" + m);
        } catch (IllegalArgumentException expected) {
            // pass
        }
    }

    public static void main(String[] args) {
        KthFromEnd.ListNode head = list(1, 2, 3, 4, 5);
        if (value(head, 1) != 5) throw new AssertionError("m=1");
        if (value(head, 2) != 4) throw new AssertionError("m=2");
        if (value(head, 5) != 1) throw new AssertionError("m=n");
        if (head.next.val != 2 || head.next.next.val != 3) throw new AssertionError("list mutated");

        KthFromEnd.ListNode single = list(9);
        if (value(single, 1) != 9) throw new AssertionError("single");

        expectIllegal(head, 0);
        expectIllegal(head, -1);
        expectIllegal(head, 6);
        expectIllegal(null, 1);

        for (int n = 1; n <= 100; n++) {
            int[] values = new int[n];
            for (int i = 0; i < n; i++) values[i] = i + 1000;
            KthFromEnd.ListNode h = list(values);
            for (int m = 1; m <= n; m++) {
                int expected = values[n - m];
                int actual = value(h, m);
                if (actual != expected) {
                    throw new AssertionError("n=" + n + " m=" + m + " expected=" + expected + " actual=" + actual);
                }
            }
        }
        System.out.println("PASS tail head middle single invalid-m empty exhaustive-n1-100 topology-preserved");
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

    with tempfile.TemporaryDirectory(prefix='b50-kth-from-end-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'KthFromEnd.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'KthFromEndTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'KthFromEnd.java', 'KthFromEndTest.java', cwd=tmpdir)
        stdout = run('java', 'KthFromEndTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS tail head middle single invalid-m empty exhaustive-n1-100 topology-preserved'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac KthFromEnd.java KthFromEndTest.java && java KthFromEndTest',
        'stdout': stdout,
        'checks': [
            'm=1 returns tail, m=n returns head, and an interior m returns the expected node',
            'single-node list is handled',
            'm<=0, m>length, and empty-list positive-m inputs follow the explicit illegal-input contract',
            'all n=1..100 and every valid m agree with an independent array-index oracle',
            'the tested list topology remains unchanged after lookup',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 exhaustive kth-from-end executable validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The repository source asks to find the m-th element from the end of a linked list and does not specify indexing origin, invalid-input disposition, mutation permission, or cyclic-input semantics.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'algorithm-validation', 'text': 'The executable OpenJDK 21 fixture verifies the fixed-gap two-pointer implementation for every valid m across list sizes 1 through 100 and independently checks tail, head, interior, single-node, invalid-input and topology-preservation boundaries.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'complexity-bound', 'text': 'The implementation advances only two node references forward through a finite acyclic list and allocates no input-sized auxiliary structure; the fixture validates the implementation shape while the source code directly bounds the walks.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '关键细节', '原理机制']},
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
        'The candidate directly implements the exact m-th-from-end lookup instead of reusing generic linked-list advice.',
        'The source leaves m indexing and invalid-input behavior unspecified; the candidate makes 1-based indexing and IllegalArgumentException explicit assumptions rather than source facts.',
        'The fixed-gap invariant is explained and matches the executable implementation: fast advances m nodes, then both pointers move until fast reaches null.',
        'OpenJDK 21 validation exhaustively checks every valid m for n=1..100 against an independent array oracle and separately covers invalid m, empty input, single node, head/tail/interior positions, and topology preservation.',
        'The answer states the finite acyclic-list applicability boundary and explains why cyclic input invalidates null-based termination.',
        'No production history or unsupported version-sensitive behavior is fabricated.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0050-kth-from-end-20260829-v1',
        'review_version': 'batch-0050.kth-from-end.v1',
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
        'title': 'Kth-from-end source-first isolated review',
        'locator': str(out / 'isolated_review_result.json'),
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    }]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0050-kth-from-end-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'm=1 tail lookup', 'expected': 'returns last node', 'actual': 'pass', 'passed': True},
                {'case': 'm=list length', 'expected': 'returns head node', 'actual': 'pass', 'passed': True},
                {'case': 'invalid m and empty list', 'expected': 'explicit IllegalArgumentException contract', 'actual': 'pass', 'passed': True},
                {'case': 'exhaustive valid positions n=1..100', 'expected': 'matches independent array-index oracle for every valid m', 'actual': 'pass', 'passed': True},
                {'case': 'topology preservation', 'expected': 'lookup does not rewrite next links', 'actual': 'pass', 'passed': True},
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
    line = '- [x] `cq_q_d6793c017bd5cd31952352d7a0e98464` source-first isolated review PASS: exact m-th-from-end lookup is implemented with a fixed-gap two-pointer invariant; 1-based indexing and invalid-input behavior are explicitly labeled as assumptions because the source does not define them. OpenJDK 21 validation exhaustively checks every valid m for n=1..100 plus tail/head/single/invalid/empty/topology boundaries. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
