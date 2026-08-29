#!/usr/bin/env python3
"""Stage and deterministically validate Batch 0059 merge-two-sorted-lists candidate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
BATCH = '0059'
DATE = '2026-08-30'
CID = 'cq_q_4046b5252e29fc4fdc52fb2fdd54e544'
EXPECTED_QIDS = ['4046b5252e29fc4fdc52fb2fdd54e544', '6d0ce7413637171a69c6ef564b3b20b7']
EXPECTED_VARIANTS = {
    '代码手撕：合并两个有序链表（Merge Two Sorted Lists）。',
    '算法手撕：合并两个有序链表（Merge Two Sorted Lists）。',
}

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_4046b5252e29fc4fdc52fb2fdd54e544","version":1,"status":"draft","updated_at":"2026-08-30","answer_type":"coding","quality_tier":"candidate"} -->
# 合并两个有序链表

## 核心结论

来源只要求“合并两个有序链表”，没有指定语言、节点类型、是否复用节点或相等元素的稳定顺序。这里采用一个明确可执行的 Java 合同：输入是两条**有限、无环、彼此不共享节点**且按 `int` 值非递减排列的单链表；允许任一输入为 `null`；结果仍非递减，并直接复用原节点，除一个 dummy 节点外不为结果元素分配新节点。每次比较两个当前头节点，把较小者接到结果尾部；值相等时先取第一条链表。时间 O(m+n)，额外空间 O(1)。

## 1 分钟版

- 用 `dummy` 保存结果头的前驱，`tail` 指向当前结果尾部。
- 两条链表都非空时比较 `a.val` 和 `b.val`，把较小节点接到 `tail.next`，并只推进被选中的那条链表。
- 相等时用 `<=` 先取第一条链表，形成明确的稳定 tie-break；排序正确性不依赖这个选择。
- 某一条耗尽后，另一条剩余部分本身已经有序且不小于它自己的当前头，直接整体挂到结果尾部。
- 每个原节点只被访问和接入一次，所以时间 O(m+n)；只维护固定数量引用，额外空间 O(1)。

## 3 分钟版

```java
public final class MergeTwoSortedLists {
    public static final class ListNode {
        public final int val;
        public ListNode next;

        public ListNode(int val) {
            this.val = val;
        }
    }

    public static ListNode merge(ListNode a, ListNode b) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;

        while (a != null && b != null) {
            if (a.val <= b.val) {
                tail.next = a;
                a = a.next;
            } else {
                tail.next = b;
                b = b.next;
            }
            tail = tail.next;
        }

        tail.next = (a != null) ? a : b;
        return dummy.next;
    }
}
```

例如 `a = 1 -> 2 -> 4`，`b = 1 -> 3 -> 4`。第一次相等先接 `a` 的 1，随后接 `b` 的 1，再依次接 2、3、`a` 的 4、`b` 的 4，得到 `1 -> 1 -> 2 -> 3 -> 4 -> 4`。

这里没有“重新排序整个集合”：两个输入已经分别有序，所以只需要维护两个尚未消费区间的最小元素，也就是两个当前头节点。

## 关键细节

- **循环不变量**：每轮开始时，`dummy.next..tail` 已经是所有“已消费节点”按非递减顺序组成的正确前缀；`a` 和 `b` 分别指向两条未消费后缀的最小节点。
- **为什么只比较两个头**：各后缀自身有序，所以全局下一小节点一定在 `a` 或 `b` 的当前头中。
- **为什么剩余链表可以整体挂接**：另一条已经耗尽时，不再存在跨链表竞争；未耗尽后缀自身保持非递减顺序。
- **空链表**：若一开始某条为 `null`，循环不执行，直接返回另一条。
- **重复值**：`<=` 规定相等时第一条链表节点先出现；如果只要求值序列有序，改成 `<` 也不影响正确性，但会改变相等节点的来源顺序。
- **节点复用**：结果节点就是输入节点，因此调用方不应继续把两条原链表当成独立结构使用。
- **共享节点边界**：当前 O(1) 原地合同要求两条输入链表节点集合互不相交；若两条链表共享后缀，直接重连可能破坏结构甚至形成环，必须先重新定义处理语义。
- **复杂度**：最多消费 m+n 个节点，时间 O(m+n)；dummy 和若干引用是常数空间，因此额外空间 O(1)。

## 原理机制

设两条未消费后缀分别是 A、B。因为 A、B 各自非递减，`head(A)` 是 A 中最小值，`head(B)` 是 B 中最小值，因此 `min(head(A), head(B))` 就是 A∪B 中下一项。把它接到结果尾部后，只需推进对应链表，两个后缀仍然保持有序，于是同一推理可以重复到某个后缀为空。

这就是归并排序 merge 阶段的核心不变量：已经输出的是全局最小前缀，尚未输出部分被压缩成两个有序游标。算法不需要随机访问，也不需要额外数组，因此非常适合链表。

## 项目经验版

来源没有项目场景，不能虚构线上使用经历。手撕时应先确认：链表是否保证有序、是否允许修改输入节点、节点值类型、输入是否可能共享节点或带环、相等元素是否要求稳定来源顺序。如果题目要求“输入不可修改”，可以改为逐值创建新节点，但额外空间会变为 O(m+n)；如果允许原地复用，当前实现更节省空间。

## 常见追问

- 问：为什么时间复杂度不是 O(mn)？答：每轮只推进其中一个指针，每个节点最多被消费一次；总推进次数最多 m+n。
- 问：值相等时取哪条链表有影响吗？答：对最终值序列的非递减性没有影响；若关心来源稳定性，需要明确 tie-break。当前实现用 `<=` 先取第一条链表。
- 问：为什么需要 dummy？答：它统一了“结果第一个节点”和后续节点的接入逻辑，不必单独初始化结果头；dummy 本身不进入返回链表。
- 问：能不能递归写？答：可以，递归关系同样是选择较小头后递归合并剩余部分；但递归深度最坏 O(m+n)，会占用调用栈，迭代版额外空间 O(1)。
- 问：如果输入不是有序链表呢？答：这个合同的前提就被破坏，算法不保证输出有序；要么先排序，要么换成针对无序输入的方案，不能把归并逻辑当成通用排序器。
- 问：两条链表共享同一段尾节点怎么办？答：当前原地复用合同明确排除这种输入；共享节点时直接重连有形成自环等风险，需要先检测交点或改用不复用节点的输出合同。

## 易错点

- 接入一个节点后忘记推进对应输入指针，导致死循环。
- 更新 `tail.next` 后忘记移动 `tail`，覆盖之前的链接。
- 某条链表耗尽后继续逐个比较，增加无意义分支甚至空指针错误。
- 说额外空间 O(1)，实现却为每个值创建新节点。
- 没声明输入已排序，却把输出有序当作无条件保证。
- 原地复用节点时忽略“两输入共享节点”的结构边界。
'''

JAVA = r'''public final class MergeTwoSortedLists {
    public static final class ListNode {
        public final int val;
        public ListNode next;
        public ListNode(int val) { this.val = val; }
    }
    public static ListNode merge(ListNode a, ListNode b) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        while (a != null && b != null) {
            if (a.val <= b.val) {
                tail.next = a;
                a = a.next;
            } else {
                tail.next = b;
                b = b.next;
            }
            tail = tail.next;
        }
        tail.next = (a != null) ? a : b;
        return dummy.next;
    }
}
'''

TEST = r'''import java.util.*;

public final class MergeTwoSortedListsTest {
    private static MergeTwoSortedLists.ListNode list(int... xs) {
        MergeTwoSortedLists.ListNode d = new MergeTwoSortedLists.ListNode(0), t = d;
        for (int x : xs) { t.next = new MergeTwoSortedLists.ListNode(x); t = t.next; }
        return d.next;
    }
    private static int[] vals(MergeTwoSortedLists.ListNode h) {
        ArrayList<Integer> a = new ArrayList<>();
        int guard = 0;
        while (h != null) { if (++guard > 10000) throw new AssertionError("cycle"); a.add(h.val); h = h.next; }
        return a.stream().mapToInt(Integer::intValue).toArray();
    }
    private static void eq(int[] got, int[] want, String label) {
        if (!Arrays.equals(got, want)) throw new AssertionError(label + " got=" + Arrays.toString(got));
    }
    private static int[] oracle(int[] a, int[] b) {
        int[] out = new int[a.length + b.length]; int i=0,j=0,k=0;
        while (i<a.length && j<b.length) out[k++] = a[i] <= b[j] ? a[i++] : b[j++];
        while (i<a.length) out[k++] = a[i++]; while (j<b.length) out[k++] = b[j++];
        return out;
    }
    public static void main(String[] args) {
        eq(vals(MergeTwoSortedLists.merge(list(1,2,4), list(1,3,4))), new int[]{1,1,2,3,4,4}, "canonical");
        eq(vals(MergeTwoSortedLists.merge(null, list(1,2))), new int[]{1,2}, "left-empty");
        eq(vals(MergeTwoSortedLists.merge(list(-3,-1,5), null)), new int[]{-3,-1,5}, "right-empty");
        eq(vals(MergeTwoSortedLists.merge(null, null)), new int[]{}, "both-empty");
        eq(vals(MergeTwoSortedLists.merge(list(1,1,1), list(1,1))), new int[]{1,1,1,1,1}, "duplicates");
        MergeTwoSortedLists.ListNode a1 = new MergeTwoSortedLists.ListNode(1);
        MergeTwoSortedLists.ListNode a2 = new MergeTwoSortedLists.ListNode(3); a1.next = a2;
        MergeTwoSortedLists.ListNode b1 = new MergeTwoSortedLists.ListNode(2);
        MergeTwoSortedLists.ListNode b2 = new MergeTwoSortedLists.ListNode(4); b1.next = b2;
        MergeTwoSortedLists.ListNode merged = MergeTwoSortedLists.merge(a1, b1);
        if (merged != a1 || merged.next != b1 || merged.next.next != a2 || merged.next.next.next != b2) throw new AssertionError("must reuse original nodes");
        Random r = new Random(20260830L);
        for (int c=0;c<5000;c++) {
            int n=r.nextInt(25), m=r.nextInt(25); int[] x=new int[n], y=new int[m];
            for(int i=0;i<n;i++) x[i]=r.nextInt(41)-20; for(int i=0;i<m;i++) y[i]=r.nextInt(41)-20;
            Arrays.sort(x); Arrays.sort(y); eq(vals(MergeTwoSortedLists.merge(list(x),list(y))),oracle(x,y),"random-"+c);
        }
        System.out.println("PASS fixed=6 randomized=5000 oracle=two-pointer node-reuse=true empty=true duplicates=true negatives=true");
    }
}
'''


def main() -> int:
    cdir = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    ctx_path = cdir / 'context.json'
    if not ctx_path.exists():
        raise SystemExit('frozen Batch 0059 context missing')
    ctx = json.loads(ctx_path.read_text(encoding='utf-8'))
    if ctx.get('answer_type') != 'coding':
        raise SystemExit(f'answer type drift: {ctx.get("answer_type")}')
    if sorted(ctx.get('canonical', {}).get('question_ids') or []) != sorted(EXPECTED_QIDS):
        raise SystemExit('source ownership drift')
    if set(ctx.get('source_variants') or []) != EXPECTED_VARIANTS:
        raise SystemExit('source wording drift')

    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / 'MergeTwoSortedLists.java').write_text(JAVA, encoding='utf-8')
    (cdir / 'MergeTwoSortedListsTest.java').write_text(TEST, encoding='utf-8')

    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['javac', '-encoding', 'UTF-8', '-d', td, str(cdir / 'MergeTwoSortedLists.java'), str(cdir / 'MergeTwoSortedListsTest.java')], check=True)
        run = subprocess.run(['java', '-cp', td, 'MergeTwoSortedListsTest'], check=True, text=True, stdout=subprocess.PIPE)
    stdout = run.stdout.strip()
    expected = 'PASS fixed=6 randomized=5000 oracle=two-pointer node-reuse=true empty=true duplicates=true negatives=true'
    if stdout != expected:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    sha = hashlib.sha256(CANDIDATE.encode('utf-8')).hexdigest()
    (cdir / 'code_validation.json').write_text(json.dumps({
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'validated_at': DATE,
        'language': 'java',
        'command': 'javac MergeTwoSortedLists.java MergeTwoSortedListsTest.java && java MergeTwoSortedListsTest',
        'result': 'pass',
        'stdout': stdout,
        'checks': ['canonical merge', 'left/right/both empty', 'duplicates', 'negative values', 'original-node reuse', '5000 deterministic randomized oracle comparisons'],
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (cdir / 'writer_research.json').write_text(json.dumps({
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': sha,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': [
            {'source_id': 'repository-source', 'title': 'Batch 0059 frozen repository source context', 'locator': str(ctx_path), 'source_type': 'repository_source_record', 'checked_at': DATE},
            {'source_id': 'fixture', 'title': 'Deterministic merge-two-sorted-lists Java fixture', 'locator': str(cdir / 'code_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
        ],
        'claims': [
            {'claim_id': 'source-contract', 'text': 'All frozen source variants ask only for merging two sorted linked lists; language, node shape, node reuse, tie-break and malformed/shared-node semantics are not preserved source constraints.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '关键细节', '项目经验版']},
            {'claim_id': 'implementation-behavior', 'text': 'Under the explicit finite acyclic disjoint nondecreasing-list contract, the iterative two-pointer implementation returns the sorted merge, handles empty/duplicate/negative inputs, reuses source nodes, and matches an independent array oracle across 5000 deterministic randomized cases.', 'source_ids': ['fixture'], 'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制']},
        ],
        'source_question_coverage': [{'question_id': qid, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版']} for qid in EXPECTED_QIDS],
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    note = f'- [x] `{CID}` source-bounded merge-two-sorted-lists candidate is staged with an explicit finite/acyclic/disjoint/nondecreasing input contract and deterministic OpenJDK validation (`{stdout}`). Writer research is frozen; independent source-first review remains the next gate and no formal promotion is claimed.'
    if note not in text:
        text = text.rstrip() + '\n' + note + '\n'
        task.write_text(text, encoding='utf-8')
    print(stdout)
    print(f'CANDIDATE_SHA256={sha}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
