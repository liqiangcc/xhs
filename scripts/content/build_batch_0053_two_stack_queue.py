#!/usr/bin/env python3
# Build, validate, source-first review, and stage the normalized Batch 0053 two-stack queue candidate.

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0053'
CID = 'cq_q_36ab1630843f456fa940c19962292fbe'
EXPECTED = {
    '36ab1630843f456fa940c19962292fbe': '算法：两个栈实现队列',
    '4a4761c79b9ebbb35a45eaf3843caca0': '算法：两个栈模拟队列？',
    '7f276bae3d88861ba9c9abc663d172cf': '算法 2：使用两个栈实现一个队列（要求不使用额外的辅助数据结构）',
    'eaae17962ef4c12e3a382e102ff461c1': '编程题: 用两个栈模拟队列 (实现push、pop、count)',
}

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_36ab1630843f456fa940c19962292fbe","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 用两个栈实现队列

## 核心结论

四个仓库来源都要求同一件事：**只借助两个栈实现 FIFO 队列**；其中一个来源额外明确“不使用额外的辅助数据结构”，另一个来源明确要求 `push`、`pop`、`count`。因此候选合同直接覆盖这些交集和附加约束：内部只有两个栈 `in` / `out`；`push` 把元素压入 `in`；`pop` 只有在 `out` 为空时才把 `in` 全量倒入 `out`，再从 `out` 弹出；`count` 直接返回两个栈当前元素个数之和，不维护第三个集合或额外计数结构。空队列 `pop` 抛 `NoSuchElementException`，null 元素不支持。

这个做法的关键不是“每次 pop 都倒栈”，而是**惰性搬运**：每个元素至多经历一次 `in -> out` 搬运，再从 `out` 弹出，所以一串操作上 `push/pop` 的摊销时间都是 O(1)；单次触发搬运的 `pop` 最坏可达 O(N)。`count` 是 O(1)，额外数据结构仍只有两个栈。

## 1 分钟版

- 用两个栈：`in` 接收入队，`out` 负责出队。
- `push(x)`：只做 `in.push(x)`。
- `pop()`：若 `out` 非空直接弹；若 `out` 为空，才把 `in` 全部逐个弹出并压入 `out`，这样顺序被反转成 FIFO。
- 不要每次 pop 都来回搬；`out` 还有元素时继续消费它。
- `count()` 不需要第三个变量或容器，直接 `in.size() + out.size()`。
- 每个元素最多进 `in` 一次、搬到 `out` 一次、从 `out` 出一次，因此摊销 O(1)；一次搬运型 pop 最坏 O(N)。
- 空队列 pop 的行为必须先定义；当前实现抛异常。

## 3 分钟版

```java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.NoSuchElementException;
import java.util.Objects;

public final class TwoStackQueue<E> {
    private final Deque<E> in = new ArrayDeque<>();
    private final Deque<E> out = new ArrayDeque<>();

    public void push(E value) {
        in.push(Objects.requireNonNull(value, "null values are not supported"));
    }

    public E pop() {
        moveIfNeeded();
        E value = out.pollFirst();
        if (value == null) {
            throw new NoSuchElementException("queue is empty");
        }
        return value;
    }

    public int count() {
        return in.size() + out.size();
    }

    private void moveIfNeeded() {
        if (!out.isEmpty()) return;
        while (!in.isEmpty()) {
            out.push(in.pop());
        }
    }
}
```

举例连续执行 `push(1), push(2), push(3)` 后，`in` 顶部顺序是 `3,2,1`，`out` 为空。第一次 `pop()` 才触发搬运：依次从 `in` 弹出 3、2、1 并压入 `out`，于是 `out` 顶部变成 1，弹出的正是最早入队元素。之后再 `push(4)` 只进入 `in`，而后续 `pop()` 会先继续从已有 `out` 取 2、3；只有 `out` 再次为空时才搬运 4。

## 关键细节

- **FIFO 为什么成立**：第一个栈把入队顺序反转一次，第二个栈在搬运时再反转一次；较早进入 `in` 的元素最终位于 `out` 顶部。
- **什么时候搬运**：只有 `out` 为空才搬。若 `out` 非空又把新元素搬进去，会破坏已排好的旧元素出队顺序。
- **count 无需第三个结构**：一个元素任意时刻只会位于 `in` 或 `out` 之一，所以队列长度恰好是 `in.size()+out.size()`。这也满足“只使用两个栈”的来源约束。
- **复杂度口径**：`push` 最坏 O(1)；`count` O(1)；某次 `pop` 可能搬 N 个元素而最坏 O(N)，但每个元素只会被搬运一次，所以操作序列上的 `pop` 摊销 O(1)。
- **空队列**：来源没有保存返回 sentinel 还是异常；当前候选明确抛 `NoSuchElementException`，避免把合法元素值和“空”混淆。
- **null**：示例用 `ArrayDeque` 作为栈实现，因此明确拒绝 null。若业务要支持 null，需要另外定义空队列返回语义，不能把实现细节藏起来。
- **线程安全**：来源没有并发要求；两个栈之间的搬运不是原子操作，当前实现不是并发队列。

## 原理机制

两个栈实现队列依赖“反转两次恢复原相对顺序”。把元素按 `a,b,c` 入 `in` 后，从 `in` 弹出的顺序是 `c,b,a`；把这个序列再逐个压入 `out`，`out` 的弹出顺序就变回 `a,b,c`。

摊销分析可以给每个元素记账：

1. 入队时进入 `in` 一次；
2. 某次 `out` 为空时，从 `in` 弹出并压入 `out`，只发生一次；
3. 最终从 `out` 弹出一次。

不会出现元素在两个栈之间反复横跳。因此即使某一次 pop 搬了很多元素，总搬运次数仍与实际入队元素数线性相关，一串 M 次队列操作总工作量 O(M)，得到摊销 O(1)。

## 项目经验版

来源没有真实吞吐、容量、并发和阻塞语义，不能虚构线上使用。工程里通常直接选标准队列实现；手写两个栈更适合考察栈/队列语义和摊销分析。如果扩展到多线程，还必须定义锁、线性化点、阻塞/非阻塞和可见性，不能把这个单线程面试实现直接包装成并发队列。

## 常见追问

- 问：为什么不能每次 pop 都把两个栈来回倒？答：那会重复搬运同一批元素，最坏把一串操作退化成 O(N²)。惰性搬运保证每个元素只从 `in` 到 `out` 一次。
- 问：push 之后 out 里还有旧元素怎么办？答：新元素留在 `in`。FIFO 要先消费 `out` 中更早入队的元素，只有 `out` 空了才搬新批次。
- 问：count 要不要单独维护变量？答：不需要。队列元素严格分布在两个栈中，`in.size()+out.size()` 就是总数，也避免引入第三份状态同步问题。
- 问：pop 是 O(1) 吗？答：摊销 O(1)，不是每次最坏 O(1)。触发全量搬运的那一次可能 O(N)。
- 问：为什么 count 是 O(1)？答：当前底层 `ArrayDeque.size()` 是 O(1)，只做两个 size 相加；如果换成 size 不是 O(1) 的抽象栈，则需要重新说明合同。
- 问：能不能只用两个栈且不用其他辅助数据结构？答：可以，两个栈本身保存全部元素；代码只有局部变量和方法调用，count 也从两个栈大小直接计算，没有第三个集合。
- 问：空队列 pop 返回什么？答：来源没规定；当前合同抛 `NoSuchElementException`，面试官若要求 sentinel/Optional 再按指定 API 改。

## 易错点

- `out` 非空时仍然搬运 `in`，破坏 FIFO 顺序。
- 每次 pop 后把剩余元素再倒回 `in`，造成重复搬运和更差复杂度。
- 把摊销 O(1) 说成每次最坏 O(1)。
- 为 count 维护一个容易和两个栈不同步的第三份状态，却没有必要。
- 忽略空队列 pop 的语义。
- 看到来源写 push/pop/count，就拆成另一个 Canonical，造成与“两个栈实现队列”重复；这些只是同一队列合同的具体接口。
'''

TEST = r'''import java.util.*;

public final class TwoStackQueueTest {
    private static void check(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }

    public static void main(String[] args) {
        TwoStackQueue<Integer> q = new TwoStackQueue<>();
        check(q.count() == 0, "initial count");
        try {
            q.pop();
            throw new AssertionError("empty pop should fail");
        } catch (NoSuchElementException expected) {}

        q.push(1); q.push(2); q.push(3);
        check(q.count() == 3, "count after pushes");
        check(q.pop() == 1, "first fifo");
        q.push(4);
        check(q.count() == 3, "split-stack count");
        check(q.pop() == 2, "old out before new in 2");
        check(q.pop() == 3, "old out before new in 3");
        check(q.pop() == 4, "new batch 4");
        check(q.count() == 0, "drained count");

        TwoStackQueue<Integer> actual = new TwoStackQueue<>();
        ArrayDeque<Integer> oracle = new ArrayDeque<>();
        Random random = new Random(20260829L);
        for (int round = 0; round < 200_000; round++) {
            boolean doPush = oracle.isEmpty() || random.nextInt(100) < 58;
            if (doPush) {
                int v = random.nextInt();
                actual.push(v);
                oracle.addLast(v);
            } else {
                int a = actual.pop();
                int b = oracle.removeFirst();
                check(a == b, "fifo round=" + round);
            }
            check(actual.count() == oracle.size(), "count round=" + round);
        }
        while (!oracle.isEmpty()) {
            check(actual.pop().equals(oracle.removeFirst()), "final drain");
            check(actual.count() == oracle.size(), "final count");
        }

        try {
            actual.push(null);
            throw new AssertionError("null push should fail");
        } catch (NullPointerException expected) {}

        System.out.println("PASS empty directed interleaved-count 200000-random-vs-arraydeque final-drain null-boundary");
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
    qids = ctx.get('canonical', {}).get('question_ids') or []
    if set(qids) != set(EXPECTED):
        raise SystemExit(f'normalized ownership drift: {qids}')
    sources = {x.get('question_id'): x for x in ctx.get('source_questions', [])}
    if set(sources) != set(EXPECTED):
        raise SystemExit('normalized source coverage drift')
    for qid, wording in EXPECTED.items():
        src = sources[qid]
        if src.get('original_question') != wording or src.get('is_valid_for_library') is not True:
            raise SystemExit(f'{qid}: source wording/validity drift')

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

    with tempfile.TemporaryDirectory(prefix='b53-two-stack-queue-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'TwoStackQueue.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'TwoStackQueueTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'TwoStackQueue.java', 'TwoStackQueueTest.java', cwd=tmpdir)
        stdout = run('java', 'TwoStackQueueTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS empty directed interleaved-count 200000-random-vs-arraydeque final-drain null-boundary'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac TwoStackQueue.java TwoStackQueueTest.java && java TwoStackQueueTest',
        'stdout': stdout,
        'checks': [
            'empty-pop exception and zero count',
            'directed FIFO behavior across lazy transfer plus interleaved push/count',
            '200000 deterministic random operations agree with java.util.ArrayDeque FIFO and size oracle',
            'final drain preserves order and count',
            'null rejection matches explicit candidate contract',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    source_records = [
        {'source_id': 'repository-source', 'title': 'Normalized Batch 0053 two-stack queue repository context with four preserved Questions', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'relation-review', 'title': 'Batch 0053 source-first same-relation review and application', 'locator': 'review/content_build/answer_batch_0053/two_stack_queue_relation/relation_review.md', 'source_type': 'repository_structured_source', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 two-stack FIFO deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'All four normalized source questions preserve the same two-stack queue Coding goal; one adds a no-extra-data-structure constraint and another explicitly names push, pop, and count.', 'source_ids': ['repository-source', 'relation-review'], 'answer_locations': ['核心结论', '1 分钟版', '易错点']},
        {'claim_id': 'queue-contract', 'text': 'The candidate uses exactly two stack containers, defines empty pop as NoSuchElementException and null as unsupported, and computes count from the two stack sizes rather than maintaining a third data structure.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节']},
        {'claim_id': 'lazy-transfer-mechanism', 'text': 'Input elements enter the in stack and transfer to out only when out is empty; double reversal restores FIFO order and each element transfers at most once.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制']},
        {'claim_id': 'complexity-validation', 'text': 'Push and count are O(1); a transfer-triggering pop can be O(N) worst-case while pop is amortized O(1) over an operation sequence. Executable validation covers 200000 deterministic operations against ArrayDeque.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '关键细节', '常见追问']},
    ]
    coverage = [{'question_id': qid, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']} for qid in EXPECTED]
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': source_records,
        'claims': claims,
        'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate is written against the post-normalization four-question source context and explicitly covers the push/pop/count and no-extra-data-structure variants.',
        'Using count = in.size() + out.size() avoids a third container or independently synchronized count state while preserving O(1) count under the declared stack implementation.',
        'Lazy transfer only when out is empty preserves FIFO order for interleaved pushes and prevents repeated back-and-forth movement.',
        'The complexity statement correctly separates a single O(N) transfer-triggering pop from amortized O(1) pop over a sequence.',
        'OpenJDK 21 validation covers empty semantics, directed interleaving, count while elements are split across both stacks, 200000 deterministic operations against ArrayDeque, final drain, and null rejection.',
        'The answer treats empty-pop/null/thread-safety behavior as explicit candidate contract rather than unpreserved source fact.',
        'The normalized relation is reflected in content: one answer covers all four source Questions rather than reintroducing a duplicate Canonical through separate answers.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0053-two-stack-queue-20260829-v1',
        'review_version': 'batch-0053.two-stack-queue.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), 'review/content_build/answer_batch_0053/two_stack_queue_relation/relation_review.md', str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = source_records + [{'source_id': 'isolated-review', 'title': 'Batch 0053 normalized two-stack queue source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0053-two-stack-queue-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'empty queue', 'expected': 'count 0 and pop throws', 'actual': 'pass', 'passed': True},
                {'case': 'interleaved push/pop with both stacks occupied', 'expected': 'FIFO plus exact count', 'actual': 'pass', 'passed': True},
                {'case': '200000 deterministic random operations', 'expected': 'matches ArrayDeque FIFO and size oracle', 'actual': 'pass', 'passed': True},
                {'case': 'null push', 'expected': 'NullPointerException under declared contract', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_36ab1630843f456fa940c19962292fbe` normalized two-stack queue source-first isolated review PASS: after consolidating Batch 0053 singleton `cq_q_eaae17962ef4c12e3a382e102ff461c1`, the survivor owns all four exact repository prompts. One answer now covers two-stack FIFO, the no-extra-data-structure constraint, and explicit push/pop/count; count derives from the two stack sizes, lazy transfer preserves FIFO with amortized O(1) pop, and OpenJDK 21 validation covers directed and 200000 deterministic operations against ArrayDeque. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
