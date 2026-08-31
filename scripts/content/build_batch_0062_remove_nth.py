#!/usr/bin/env python3
"""Build and validate the source-bounded Batch 0062 remove-nth-from-end candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_d0b70d126320ddd7e4a234f0f3c6066f'
QIDS = ['d0b70d126320ddd7e4a234f0f3c6066f']
EXPECTED_VARIANT = '算法手撕：删除链表倒数第 N 个元素。'
EXPECTED_STDOUT = 'PASS fixed=10 random_cases=30000 oracle=array-delete invalid_n=pass head_delete=pass tail_delete=pass'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d0b70d126320ddd7e4a234f0f3c6066f","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 删除链表倒数第 N 个节点

## 核心结论

这题的核心是把“倒数第 N 个”转成两个指针之间固定 `N` 个节点的距离。这里声明一个可执行 Java 契约：输入是单链表头节点和整数 `n`；`1 <= n <= 链表长度` 时删除倒数第 `n` 个节点并返回新头；`n <= 0`、空链表或 `n` 大于长度时抛 `IllegalArgumentException`。实现使用 dummy 哨兵 + fast/slow：先让 `fast` 从 dummy 向前走 `n` 步，再让两者同步前进直到 `fast` 到尾节点，此时 `slow.next` 正好是待删除节点。

## 1 分钟版

- 加一个 dummy 指向原 head，统一“删除头节点”和“删除中间/尾节点”的代码路径。
- `fast` 先从 dummy 前进 `n` 步，建立 fast 与 slow 的固定间距。
- 然后 `fast`、`slow` 同步右移，直到 `fast.next == null`；这时 `slow.next` 就是倒数第 `n` 个节点。
- 删除只需要 `slow.next = slow.next.next`，最后返回 `dummy.next`。
- 来源没有规定非法 `n` 的行为；本答案显式选择抛异常，避免把未定义边界悄悄解释成“不删除”。

## 3 分钟版

```java
public final class RemoveNthFromEnd {
    public static final class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
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

例如 `1 -> 2 -> 3 -> 4 -> 5`，`n = 2`。fast 先从 dummy 走两步到节点 2；随后 fast 和 slow 同步走，fast 最终到 5 时 slow 到 3，因此 `slow.next` 是 4，删除后得到 `1 -> 2 -> 3 -> 5`。

## 关键细节

- **为什么从 dummy 出发**：如果 `n == length`，目标就是 head；dummy 让 slow 可以停在 head 的前驱位置，不需要额外判断“删头”。
- **间距不变量**：fast 先走 `n` 步后，slow 与 fast 同步移动，二者之间的节点距离保持不变；当 fast 到尾节点时，slow 的下一个节点距尾部正好有 `n-1` 个节点。
- **非法 n**：循环中一旦 fast 提前变成 `null`，说明 `n > length`；`n <= 0` 在入口直接拒绝。来源没给语义，所以异常是本答案明确声明的契约，不是题目事实。
- **删除尾节点**：`n == 1` 时同步阶段结束后 slow 停在倒数第二个节点，赋值自然把尾节点摘掉。
- **复杂度**：每个节点最多被 fast/slow 常数次访问，时间 `O(L)`；除 dummy 与两个指针外不使用与链表长度相关的额外结构，额外空间 `O(1)`。

## 原理机制

如果先遍历得到链表长度 `L`，目标其实是从头数第 `L - n + 1` 个节点；双指针把这两次定位压缩到一次连续扫描。fast 先制造 `n` 的领先距离，此后同步移动相当于让 slow “延迟 n 步”跟随 fast。等 fast 抵达链表末端，slow 的位置就由这个固定距离唯一确定。

真正容易错的是“目标节点”和“目标节点前驱”的定位。单链表删除需要改前驱的 `next`，所以 slow 应停在待删节点前面；dummy 正是为了在“待删节点是 head”时也仍然存在一个统一的前驱。

## 项目经验版

来源只有算法题，没有真实项目、节点所有权、内存管理或并发约束，因此不能虚构线上经历。落地到生产链表结构时还需要看语言和所有权模型：Java 主要是断开引用，C/C++ 还要明确释放责任；并发链表则涉及同步协议。这些都超出当前来源，只作为边界提醒。

## 常见追问

- 问：为什么不能只用一个指针？答：单次从头扫描时，一个指针无法同时知道“距离尾部还有 n 个节点”；提前建立 fast 的领先距离，就把尾部位置转换成 slow 的当前位置。
- 问：为什么要 dummy？答：删除 head 时没有真实前驱，dummy 提供统一前驱，使所有删除都变成修改 `slow.next`。
- 问：`n == 1` 会怎样？答：fast 最终到尾节点时 slow 停在尾节点前驱，直接删除 tail。
- 问：`n == length` 会怎样？答：fast 先走到原 tail，同步阶段不执行，slow 仍在 dummy，于是删除原 head。
- 问：`n > length` 怎么办？答：来源没规定；本契约在 fast 预走阶段检测并抛 `IllegalArgumentException`。
- 问：能否先求长度再删？答：可以，也是 `O(L)`；双指针的价值是不用先单独完成一次长度统计，并自然表达“与尾部保持固定距离”的不变量。

## 易错点

- fast 从 head 而不是 dummy 出发，却仍套用同样循环条件，产生 off-by-one。
- 只考虑删除普通节点，没有覆盖 `n == length` 的删头场景。
- `n == 1` 时让 slow 走过头，导致无法删除尾节点。
- 未定义 `n <= 0` 或 `n > length` 的行为，却把某个实现偶然行为当成题目要求。
- 找到了待删节点本身，却忘记单链表真正需要的是它的前驱节点来改 `next`。
'''

JAVA_IMPL = r'''public final class RemoveNthFromEnd {
    public static final class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    public static ListNode removeNthFromEnd(ListNode head, int n) {
        if (n <= 0) throw new IllegalArgumentException("n must be positive");
        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode fast = dummy, slow = dummy;
        for (int i = 0; i < n; i++) {
            fast = fast.next;
            if (fast == null) throw new IllegalArgumentException("n exceeds list length");
        }
        while (fast.next != null) {
            fast = fast.next;
            slow = slow.next;
        }
        slow.next = slow.next.next;
        return dummy.next;
    }
}
'''

JAVA_TEST = r'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class RemoveNthWriterTest {
    private static final Random RNG = new Random(0x62D0B70DL);

    static RemoveNthFromEnd.ListNode build(int[] values) {
        RemoveNthFromEnd.ListNode dummy = new RemoveNthFromEnd.ListNode(0), tail = dummy;
        for (int v : values) { tail.next = new RemoveNthFromEnd.ListNode(v); tail = tail.next; }
        return dummy.next;
    }
    static int[] values(RemoveNthFromEnd.ListNode head) {
        List<Integer> out = new ArrayList<>();
        for (RemoveNthFromEnd.ListNode p = head; p != null; p = p.next) out.add(p.val);
        int[] a = new int[out.size()]; for (int i=0;i<a.length;i++) a[i]=out.get(i); return a;
    }
    static int[] oracle(int[] input, int n) {
        int[] out = new int[input.length - 1];
        int remove = input.length - n;
        for (int i=0,j=0;i<input.length;i++) if (i != remove) out[j++] = input[i];
        return out;
    }
    static void eq(int[] expected, int[] actual, String label) {
        if (!Arrays.equals(expected, actual)) throw new AssertionError(label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
    }
    static void fixed(int[] input, int n, int[] expected, String label) {
        eq(expected, values(RemoveNthFromEnd.removeNthFromEnd(build(input), n)), label);
    }
    public static void main(String[] args) {
        fixed(new int[]{1},1,new int[]{},"single");
        fixed(new int[]{1,2},1,new int[]{1},"tail-two");
        fixed(new int[]{1,2},2,new int[]{2},"head-two");
        fixed(new int[]{1,2,3,4,5},2,new int[]{1,2,3,5},"example");
        fixed(new int[]{1,2,3,4,5},5,new int[]{2,3,4,5},"delete-head");
        fixed(new int[]{1,2,3,4,5},1,new int[]{1,2,3,4},"delete-tail");
        fixed(new int[]{7,7,7},2,new int[]{7,7},"duplicates");
        fixed(new int[]{-1,0,1},2,new int[]{-1,1},"values-unrestricted");
        fixed(new int[]{9,8,7,6},3,new int[]{9,7,6},"middle");
        fixed(new int[]{42,5,42,5},4,new int[]{5,42,5},"head-duplicate");
        boolean bad0=false,badNeg=false,badLarge=false,badEmpty=false;
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1}),0); } catch (IllegalArgumentException e) { bad0=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1}),-1); } catch (IllegalArgumentException e) { badNeg=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1,2}),3); } catch (IllegalArgumentException e) { badLarge=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(null,1); } catch (IllegalArgumentException e) { badEmpty=true; }
        if (!bad0 || !badNeg || !badLarge || !badEmpty) throw new AssertionError("invalid n/list boundary missing");

        int cases=0;
        for (int t=0;t<30000;t++) {
            int len=1+RNG.nextInt(40), n=1+RNG.nextInt(len);
            int[] input=new int[len]; for(int i=0;i<len;i++) input[i]=RNG.nextInt(15)-7;
            eq(oracle(input,n), values(RemoveNthFromEnd.removeNthFromEnd(build(input),n)), "random-"+t);
            cases++;
        }
        if(cases!=30000) throw new AssertionError("case count");
        System.out.println("PASS fixed=10 random_cases=30000 oracle=array-delete invalid_n=pass head_delete=pass tail_delete=pass");
    }
}
'''


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass': raise SystemExit('batch source inventory not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item or item.get('answer_type') != 'coding' or item.get('question_ids') != QIDS: raise SystemExit(f'{CID}: inventory/type/ownership drift')
    rows = list(item.get('source_questions') or [])
    if item.get('source_question_count') != 1 or item.get('source_occurrence_count') != 2 or len(rows) != 2: raise SystemExit(f'{CID}: occurrence inventory drift')
    if any(x.get('question_id') != QIDS[0] or x.get('original_question') != EXPECTED_VARIANT for x in rows): raise SystemExit(f'{CID}: source wording drift')
    if len({(x.get('source_note_id'),x.get('source_question_index')) for x in rows}) != 2: raise SystemExit(f'{CID}: source occurrences collapsed')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context = json.loads((out/'context.json').read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'coding' or (context.get('canonical') or {}).get('question_ids') != QIDS: raise SystemExit(f'{CID}: context drift')
    ctx_rows = list(context.get('source_questions') or [])
    if len(ctx_rows) != 2 or any(x.get('original_question') != EXPECTED_VARIANT for x in ctx_rows): raise SystemExit(f'{CID}: context occurrences drift')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE.rstrip()+'\n',encoding='utf-8')
    (out/'RemoveNthFromEnd.java').write_text(JAVA_IMPL,encoding='utf-8')
    (out/'RemoveNthWriterTest.java').write_text(JAVA_TEST,encoding='utf-8')
    subprocess.run(['javac','RemoveNthFromEnd.java','RemoveNthWriterTest.java'],cwd=out,check=True)
    proc=subprocess.run(['java','RemoveNthWriterTest'],cwd=out,text=True,capture_output=True,check=True)
    stdout=proc.stdout.strip()
    if stdout != EXPECTED_STDOUT: raise SystemExit(f'writer stdout drift: {stdout!r}')
    for cls in out.glob('*.class'): cls.unlink()
    digest=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    write_json(out/'writer_validation.json',{'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'validator':'batch_0062_remove_nth_writer_fixture','command':'javac RemoveNthFromEnd.java RemoveNthWriterTest.java && java RemoveNthWriterTest','stdout':stdout,'checks':['fixed head/tail/middle/single/duplicate boundaries','invalid n and empty-list behavior follows declared contract','30,000 seeded random valid removals match independent array-index deletion']})
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':CID,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','candidate_sha256':digest,'source_occurrence_count':2,'sources':[{'source_id':'repository-source','title':'Batch 0062 frozen repository source packet for remove-nth-from-end','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'fixture','title':'Remove-nth deterministic and randomized writer validation','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}],'claims':[{'claim_id':'source-boundary','text':'Both preserved primary-source occurrences ask only to remove the Nth element from the end of a linked list; language, node API and invalid-n semantics are not source constraints.','source_ids':['repository-source'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节']},{'claim_id':'algorithm-behavior','text':'Under the declared valid-n Java contract, dummy plus fixed-gap fast/slow pointers matches an array-index deletion oracle on fixed boundaries and 30,000 seeded random cases.','source_ids':['fixture'],'answer_locations':['3 分钟版','关键细节','原理机制','常见追问']}],'source_question_coverage':[{'question_id':QIDS[0],'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问']}],'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    task_path=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task=task_path.read_text(encoding='utf-8').rstrip()
    line=f'- [x] `{CID}` writer stage complete: both frozen primary-source occurrences of the remove-Nth-from-end question are preserved; the candidate declares explicit invalid-`n` behavior and validates dummy + fixed-gap fast/slow deletion over head/tail/middle/single boundaries plus 30,000 seeded random lists against an array-deletion oracle. Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    if line not in task: task_path.write_text(task+'\n'+line+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'canonical_id':CID,'candidate_sha256':digest,'stdout':stdout},ensure_ascii=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
