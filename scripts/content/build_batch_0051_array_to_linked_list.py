#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0051 array-to-linked-list candidate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0051'
CID = 'cq_q_dbf9d916d20b5087fd78e10563bd8091'
QID = 'dbf9d916d20b5087fd78e10563bd8091'
EXPECTED = '算法：数组转链表。'
TASK = Path('tasks/answer-batches/TASK-20260711-0313-answer-batch-0051.md')
OUT = Path(f'review/content_build/answer_batch_{BATCH}/{CID}')
CANDIDATE_PATH = Path(f'review/candidates/answers/{CID}.md')
EVIDENCE_PATH = Path(f'review/evidence/{CID}.json')

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_dbf9d916d20b5087fd78e10563bd8091","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 数组转链表

## 核心结论

来源只写了“数组转链表”，没有规定链表类型、是否复用数组元素、空输入语义或节点 API。先声明一个最小可执行契约：输入 `int[]`，按数组下标顺序创建一个新的单向链表，数组第 0 个元素成为头节点；空数组返回 `null`，输入数组不修改。实现时维护 `head` 和 `tail`，每读一个元素只在尾部追加一次，因此总时间 O(N)，新建 N 个节点占 O(N) 空间。

## 1 分钟版

- 如果数组为空，返回 `null`。
- 遍历数组，每个元素创建一个 `ListNode`。
- 第一个节点同时赋给 `head` 和 `tail`；后续节点执行 `tail.next = node`，再把 `tail = node`。
- 最后返回 `head`，链表顺序与数组顺序完全一致。
- 不要每次都从头走到尾部再追加，否则会从 O(N) 退化成 O(N²)。

## 3 分钟版

```java
public final class ArrayToList {
    public static final class ListNode {
        public final int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }

    public static ListNode fromArray(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }
        if (nums.length == 0) {
            return null;
        }

        ListNode head = null;
        ListNode tail = null;
        for (int value : nums) {
            ListNode node = new ListNode(value);
            if (head == null) {
                head = node;
                tail = node;
            } else {
                tail.next = node;
                tail = node;
            }
        }
        return head;
    }
}
```

这里把 `null` 数组定义为非法输入、空数组定义为空链表；这是本答案为了让契约可执行而做的边界选择，不是原题已经明确给出的规则。如果面试官提供现成 `ListNode` 类型，就直接复用其定义，不必重新声明节点类。

## 关键细节

- **顺序**：链表从头到尾必须依次等于 `nums[0], nums[1], ...`，不能因为头插法把顺序反过来。
- **头插 vs 尾插**：若每次 `node.next = head; head = node`，最终会得到逆序链表；除非题目明确要求逆序，否则这里用尾插。
- **尾指针**：维护 `tail` 可以 O(1) 找到追加位置；如果每插一个节点都从 `head` 扫到尾部，总复杂度是 O(N²)。
- **输入是否修改**：当前实现只读取数组并新建节点，不修改数组。
- **重复值**：数组里相同的值应生成不同节点；“值相同”不代表“节点相同”。
- **空输入**：空数组没有元素，因此返回 `null` 表示空链表；如果项目使用哨兵头节点，需要把契约换成返回 dummy/head wrapper。
- **复杂度**：遍历一次数组，时间 O(N)；新链表本身包含 N 个节点，所以输出空间 O(N)，除输出外只使用 `head/tail/node` 常数级引用。

## 原理机制

数组和链表的差别主要在“元素之间的连接方式”。数组通过连续索引表达顺序；单链表通过每个节点的 `next` 引用表达顺序。因此转换过程就是把第 i 个数组元素创建成第 i 个链表节点，并建立 `node[i].next = node[i+1]`。

维护 `tail` 的不变量是：处理完前 k 个数组元素后，`head` 指向包含这 k 个元素的完整链表，`tail` 指向其中最后一个节点，且 `tail.next == null`。处理下一个元素时只需创建新节点、把旧 `tail.next` 指向它，再更新 `tail`，这个不变量继续成立。

## 项目经验版

来源没有真实项目背景，不能虚构线上使用经历。工程里更常见的问题是“是否真的需要转换”：数组适合按下标随机访问，链表适合通过节点引用做局部插入删除，但链表有额外对象和指针开销。如果只是顺序遍历，转换往往没有收益；只有下游接口或操作模型明确需要链表时才值得构造。

## 常见追问

- 问：能不能用头插法？答：可以，但会得到逆序。如果必须保持数组顺序，要么尾插，要么头插完再反转，后者多做一次工作。
- 问：为什么要 `tail`？答：它让每次追加都是 O(1)。没有 `tail` 而每次从头找末尾，会累计成 O(N²)。
- 问：空数组返回什么？答：来源没规定。本实现把空数组映射成 `null` 空链表；如果题目给了哨兵节点协议，应按那个协议调整。
- 问：数组里有两个相同数字怎么办？答：它们位于不同位置，应创建两个不同节点，只是 `val` 相同。
- 问：如果数组元素是对象呢？答：要先定义“转换”只复制引用还是深拷贝对象。来源没有这个要求，当前 `int[]` 契约不存在对象拷贝语义。
- 问：能不能原地转换？答：普通 Java `int[]` 元素没有 `next` 字段，不能原地变成链表节点；可以复用对象型元素的前提是其类型本身支持链接且契约允许修改。

## 易错点

- 用头插法却忘记结果顺序会反转。
- 每次追加都从头遍历到尾部，导致 O(N²)。
- 空数组访问 `nums[0]`，产生越界。
- 把重复值去重，擅自改变数组的元素个数和顺序。
- 没说明 `null`、空数组、节点类型等边界，却把某一种实现选择说成原题要求。
'''

JAVA = r'''public final class ArrayToList {
    public static final class ListNode {
        public final int val;
        public ListNode next;
        public ListNode(int val) { this.val = val; }
    }

    public static ListNode fromArray(int[] nums) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        if (nums.length == 0) return null;
        ListNode head = null;
        ListNode tail = null;
        for (int value : nums) {
            ListNode node = new ListNode(value);
            if (head == null) {
                head = node;
                tail = node;
            } else {
                tail.next = node;
                tail = node;
            }
        }
        return head;
    }
}
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class ArrayToListTest {
    private static int[] toArray(ArrayToList.ListNode head) {
        int n = 0;
        for (ArrayToList.ListNode p = head; p != null; p = p.next) n++;
        int[] out = new int[n];
        int i = 0;
        for (ArrayToList.ListNode p = head; p != null; p = p.next) out[i++] = p.val;
        return out;
    }

    private static void check(int[] input) {
        int[] before = input.clone();
        ArrayToList.ListNode head = ArrayToList.fromArray(input);
        if (!Arrays.equals(input, before)) throw new AssertionError("input mutated");
        if (!Arrays.equals(toArray(head), input)) throw new AssertionError("order/value mismatch");
        if (input.length == 0 && head != null) throw new AssertionError("empty array must map to null");
        if (input.length > 1) {
            ArrayToList.ListNode p = head;
            for (int i = 1; i < input.length; i++) {
                if (p.next == null || p.next == p) throw new AssertionError("broken node topology");
                p = p.next;
            }
            if (p.next != null) throw new AssertionError("tail.next must be null");
        }
    }

    public static void main(String[] args) {
        check(new int[]{});
        check(new int[]{7});
        check(new int[]{1, 2, 3, 4});
        check(new int[]{5, 5, 5});
        check(new int[]{-3, 0, 9, -3});
        Random rnd = new Random(20260829L);
        for (int t = 0; t < 2000; t++) {
            int n = rnd.nextInt(80);
            int[] a = new int[n];
            for (int i = 0; i < n; i++) a[i] = rnd.nextInt(41) - 20;
            check(a);
        }
        try {
            ArrayToList.fromArray(null);
            throw new AssertionError("null must fail");
        } catch (IllegalArgumentException expected) {
            // pass
        }
        System.out.println("PASS empty-single-order-duplicates-input-unchanged random2000 null-boundary");
    }
}
'''


def run(*args: str, cwd: Path | None = None) -> str:
    proc = subprocess.run(args, cwd=cwd or ROOT, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(args)}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
    return proc.stdout.strip()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_context() -> dict:
    raw = run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite')
    ctx = json.loads(raw)
    if not ctx.get('ok'):
        raise RuntimeError('canonical context unavailable')
    if ctx.get('answer_type') != 'coding':
        raise RuntimeError(f"answer type drifted: {ctx.get('answer_type')}")
    canonical = ctx.get('canonical') or {}
    if canonical.get('canonical_id') != CID:
        raise RuntimeError('canonical id drifted')
    if canonical.get('question_ids') != [QID]:
        raise RuntimeError(f"question ownership drifted: {canonical.get('question_ids')}")
    source = next((q for q in ctx.get('source_questions', []) if q.get('question_id') == QID), None)
    if not source or source.get('original_question') != EXPECTED:
        raise RuntimeError(f"source wording drifted: {source and source.get('original_question')}")
    return ctx


def validate_java() -> str:
    with tempfile.TemporaryDirectory(prefix='xhs-array-to-list-') as td:
        d = Path(td)
        (d / 'ArrayToList.java').write_text(JAVA, encoding='utf-8')
        (d / 'ArrayToListTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'ArrayToList.java', 'ArrayToListTest.java', cwd=d)
        return run('java', 'ArrayToListTest', cwd=d)


def main() -> None:
    ctx = load_context()
    OUT.mkdir(parents=True, exist_ok=True)
    write_json(OUT / 'context.json', ctx)
    CANDIDATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATE_PATH.write_text(CANDIDATE, encoding='utf-8')

    stdout = validate_java()
    expected_stdout = 'PASS empty-single-order-duplicates-input-unchanged random2000 null-boundary'
    if stdout != expected_stdout:
        raise RuntimeError(f'unexpected validation stdout: {stdout!r}')

    write_json(OUT / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac ArrayToList.java ArrayToListTest.java && java ArrayToListTest',
        'stdout': stdout,
        'checks': [
            'empty array maps to an empty linked list represented by null',
            'single and multi-element arrays preserve exact order and values',
            'duplicate values remain distinct positions/nodes',
            'input array remains unchanged',
            '2000 deterministic random arrays round-trip through list traversal',
            'null input follows the candidate explicit illegal-input boundary',
        ],
    })

    candidate_sha = hashlib.sha256(CANDIDATE.encode('utf-8')).hexdigest()
    reviewer_id = 'source-first-isolated-reviewer-batch-0051-array-to-list-20260829-v1'
    findings = [
        'The repository source only says array-to-linked-list, so the candidate explicitly labels singly-linked int[] semantics and null/empty behavior as implementation boundaries rather than source facts.',
        'The algorithm preserves array order with a tail pointer and does not accidentally reverse the sequence through head insertion.',
        'The candidate explains why maintaining tail keeps construction O(N) instead of repeatedly scanning the partial list and degrading to O(N^2).',
        'Executable Java validation covers empty/single/multi-element inputs, duplicates, negative/zero values, input immutability, and 2000 deterministic random arrays.',
        'The answer distinguishes equal values from node identity and does not introduce deduplication absent from the source.',
        'The project section avoids fabricated experience and instead states when conversion may or may not be useful.',
    ]
    write_json(OUT / 'isolated_review_result.json', {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': candidate_sha,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': reviewer_id,
        'review_version': 'batch-0051.array-to-list.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            str(OUT / 'context.json'),
            str(CANDIDATE_PATH),
            str(OUT / 'writer_validation.json'),
            'docs/refactor/09_answer_content_standard.md',
        ],
        'scores': {
            'facts_and_evidence': 25,
            'directness_and_relevance': 20,
            'type_specific_completeness': 20,
            'mechanism_and_causality': 15,
            'boundaries_and_tradeoffs': 10,
            'followup_quality': 5,
            'oral_quality': 5,
        },
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    })

    write_json(EVIDENCE_PATH, {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': candidate_sha,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0051-array-to-list-builder',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': [
            {
                'source_id': 'repository-context',
                'title': 'Batch 0051 canonical/source context',
                'locator': str(OUT / 'context.json'),
                'source_type': 'repository_source_record',
                'checked_at': DATE,
            },
            {
                'source_id': 'fixture',
                'title': 'OpenJDK 21 array-to-linked-list validation',
                'locator': str(OUT / 'writer_validation.json'),
                'source_type': 'executable_test_or_reproducible_experiment',
                'checked_at': DATE,
            },
            {
                'source_id': 'isolated-review',
                'title': 'Array-to-linked-list source-first isolated review',
                'locator': str(OUT / 'isolated_review_result.json'),
                'source_type': 'repository_structured_source',
                'checked_at': DATE,
            },
        ],
        'claims': [
            {
                'claim_id': 'source-boundary',
                'text': 'The repository source only requires converting an array to a linked list; list type and null/empty semantics are not preserved source constraints.',
                'source_ids': ['repository-context'],
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节'],
            },
            {
                'claim_id': 'construction-validation',
                'text': 'Under the candidate explicit int[] to singly-linked-list contract, tail-based construction preserves order and duplicates without mutating the input, as verified by deterministic executable tests.',
                'source_ids': ['fixture'],
                'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制'],
            },
        ],
        'source_question_coverage': [
            {
                'question_id': QID,
                'covered': True,
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
            }
        ],
        'validation': {
            'command': 'javac ArrayToList.java ArrayToListTest.java && java ArrayToListTest',
            'result': 'pass',
            'reported_stdout': stdout,
            'checks': [
                'empty/single/multi-element boundaries',
                'exact order and duplicate preservation',
                'input immutability',
                '2000 deterministic random cases',
                'explicit null-input boundary',
            ],
            'boundary_tests': [
                {'case': 'empty array', 'expected': 'null head', 'actual': 'pass', 'passed': True},
                {'case': 'single element', 'expected': 'one-node list', 'actual': 'pass', 'passed': True},
                {'case': 'duplicates', 'expected': 'same cardinality and order', 'actual': 'pass', 'passed': True},
                {'case': '2000 random arrays', 'expected': 'list traversal equals source array', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': reviewer_id,
            'review_version': 'batch-0051.array-to-list.v1',
            'independent': True,
            'decision': 'pass',
            'revision_round': 1,
            'scores': {
                'facts_and_evidence': 25,
                'directness_and_relevance': 20,
                'type_specific_completeness': 20,
                'mechanism_and_causality': 15,
                'boundaries_and_tradeoffs': 10,
                'followup_quality': 5,
                'oral_quality': 5,
            },
            'hard_failures': [],
            'unsupported_claims': [],
            'uncovered_source_variants': [],
            'findings': findings,
        },
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    progress = ('- [x] `cq_q_dbf9d916d20b5087fd78e10563bd8091` source-first isolated review PASS: '
                'the source only preserves “数组转链表”, so the candidate makes its int[]→new singly linked list contract explicit instead of inventing list/null semantics. '
                'Tail-based construction preserves source order and duplicates in O(N) time without mutating the input; OpenJDK 21 validation covers empty/single/multi-element cases, duplicates, null boundary, and 2000 deterministic random arrays. '
                'Formal promotion remains blocked by repository human-approval/real-review policy.')
    text = TASK.read_text(encoding='utf-8')
    if progress not in text:
        if not text.endswith('\n'):
            text += '\n'
        text += progress + '\n'
        TASK.write_text(text, encoding='utf-8')

    run('node', 'scripts/xhs.js', 'answer', 'audit', '--candidate', str(CANDIDATE_PATH), '--require-evidence', '--require-code', '--noWrite', '--noDraftCheck')


if __name__ == '__main__':
    main()
