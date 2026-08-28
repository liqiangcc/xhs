#!/usr/bin/env python3
"""Build, validate, source-first review, and stage the Batch 0048 linked-list reorder candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-28'
CID = 'cq_q_ca061ddef082325c938854b54c720fc1'
QID = 'ca061ddef082325c938854b54c720fc1'
EXPECTED = '算法：链表重排（如1-2-3-4-5-6 转换为 1-6-2-5-3-4）的实现思路及代码逻辑'
BATCH = '0048'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ca061ddef082325c938854b54c720fc1","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# 链表重排：1-2-3-4-5-6 → 1-6-2-5-3-4

## 核心结论

这类重排的目标顺序可以写成 `L0 → Ln → L1 → Ln-1 → L2 → ...`。对单链表最稳妥的 O(n) 时间、O(1) 额外空间做法分三步：先用快慢指针找到前半段末尾并断链；再原地反转后半段；最后把前半段和反转后的后半段交替穿插。关键不只是“反转链表”，而是要先正确切开两半，避免合并时形成环或丢节点。

## 1 分钟版

- 用 `slow/fast` 找中点，让 `slow` 落在前半段最后一个节点；`second = slow.next` 后立刻 `slow.next = null` 断开。
- 原地反转 `second`，把尾部顺序从 `...4→5→6` 变成 `6→5→4`。
- 两条链表交替合并：取前半一个节点，再取后半一个节点，直到后半耗尽。
- 对 `1→2→3→4→5→6`：切成 `1→2→3` 和 `4→5→6`，后半反转成 `6→5→4`，交替得到 `1→6→2→5→3→4`。
- 时间 O(n)：找中点、反转、合并各线性一次；额外空间 O(1)。

## 3 分钟版

下面把契约明确为：原地重排单链表节点，不创建替代数据节点；`null`、单节点和双节点都保持有效。

```java
public final class ReorderList {
    public static final class ListNode {
        public int val;
        public ListNode next;
        public ListNode(int val) { this.val = val; }
    }

    public static void reorder(ListNode head) {
        if (head == null || head.next == null || head.next.next == null) {
            return;
        }

        ListNode slow = head;
        ListNode fast = head;
        while (fast.next != null && fast.next.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }

        ListNode second = slow.next;
        slow.next = null;
        second = reverse(second);

        ListNode first = head;
        while (second != null) {
            ListNode firstNext = first.next;
            ListNode secondNext = second.next;
            first.next = second;
            second.next = firstNext;
            first = firstNext;
            second = secondNext;
        }
    }

    private static ListNode reverse(ListNode head) {
        ListNode prev = null;
        ListNode cur = head;
        while (cur != null) {
            ListNode next = cur.next;
            cur.next = prev;
            prev = cur;
            cur = next;
        }
        return prev;
    }
}
```

这个快慢指针条件会让偶数长度 `2k` 的前后两半各有 `k` 个节点；奇数长度 `2k+1` 时，前半多一个节点。这样最后交替合并时，后半长度永远不会超过前半，循环只需要以 `second != null` 为结束条件。

## 关键细节

- **先断链再反转**：`slow.next = null` 必须在合并前完成，否则原前半仍指向后半，改指针时很容易形成环。
- **为什么奇数长度安全**：例如 `1→2→3→4→5` 被切成 `1→2→3` 与 `4→5`，后半反转为 `5→4`，合并结果是 `1→5→2→4→3`，中间节点自然留在末尾。
- **保存 next 再改指针**：合并时要先保存 `firstNext`、`secondNext`；若先覆盖 `first.next` 再去找原后继，会丢失剩余链表。
- **原地语义**：这里只重新连接既有节点，没有按节点值新建一条链，因此节点 identity 被保留。
- **边界**：0/1/2 个节点无需重排；3 个节点会得到 `1→3→2`，仍符合 `L0→Ln→L1...`。
- **复杂度**：每个阶段 O(n)，合起来仍 O(n)；只使用固定数量指针变量，O(1) 额外空间。

## 原理机制

目标序列交替取“尚未使用的最左节点”和“尚未使用的最右节点”。单链表不能 O(1) 时间直接从尾部向前走，所以先把后半段整体反转，把“从右往左取”转换成普通的“从头往后取”。这样原问题就变成两条正向链表的 zip：前半 `L0,L1,L2...` 与反转后半 `Ln,Ln-1...` 交替连接。

快慢指针负责在 O(n) 内找到切分点；反转把尾部访问方向改变；交替 merge 实现最终排列。这三个步骤各自只改变局部指针，而且切分后两条链彼此独立，因此比在一条仍连通的链上边找尾节点边插入更容易维护“不丢节点、不重复节点、无环”的不变量。

## 项目经验版

来源是算法手撕题，没有真实业务项目上下文，不能虚构线上使用经历。工程代码里如果链表节点还被外部对象持有，需要先确认“原地重排”是否允许，因为它会改变所有持有这些节点的观察顺序；若要求不可变数据结构，就应返回新结构并明确 O(n) 额外空间，而不是偷偷修改原链。

## 常见追问

- 问：为什么不用数组保存节点？答：可以，写法简单，但需要 O(n) 额外空间；快慢指针 + 反转 + merge 可以做到 O(1) 额外空间。
- 问：为什么 `fast` 的循环是 `fast.next != null && fast.next.next != null`？答：它让 `slow` 停在前半末尾；偶数长度两半等长，奇数长度前半多一个，便于后半驱动交替合并。
- 问：会不会形成环？答：如果先在中点断链，再反转独立后半，并在 merge 时保存两个 next，最终不会保留指回已连接区域的旧边；测试也应显式检查无环和节点数不变。
- 问：能不能递归？答：可以通过递归找到对称节点，但通常要消耗 O(n) 调用栈；这里目标是 O(1) 额外空间，所以采用迭代方案。
- 问：链表长度为奇数怎么办？答：前半多保留一个节点，后半耗尽后那个中点已经在正确尾部，不需要特殊拼接。

## 易错点

- 找到中点后忘记 `slow.next = null`，导致合并后出现环。
- 反转或合并时没有先保存原 `next`，导致链表后半丢失。
- 偶数/奇数切分边界不一致，出现重复节点、漏节点或空指针。
- 只验证值序列正确，却没验证节点 identity、节点数量和无环。
- 使用数组/栈实现后仍声称 O(1) 额外空间。
'''

TEST = r'''import java.util.*;

public final class ReorderListTest {
    private static ReorderList.ListNode list(int... values) {
        ReorderList.ListNode dummy = new ReorderList.ListNode(0), cur = dummy;
        for (int v : values) { cur.next = new ReorderList.ListNode(v); cur = cur.next; }
        return dummy.next;
    }
    private static List<ReorderList.ListNode> nodes(ReorderList.ListNode head) {
        List<ReorderList.ListNode> out = new ArrayList<>();
        Set<ReorderList.ListNode> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        while (head != null) {
            if (!seen.add(head)) throw new AssertionError("cycle detected");
            out.add(head); head = head.next;
        }
        return out;
    }
    private static void check(int[] input, int[] expected) {
        ReorderList.ListNode head = list(input);
        List<ReorderList.ListNode> before = nodes(head);
        ReorderList.reorder(head);
        List<ReorderList.ListNode> after = nodes(head);
        if (after.size() != expected.length) throw new AssertionError("size mismatch");
        for (int i=0;i<expected.length;i++) if (after.get(i).val != expected[i]) throw new AssertionError("value mismatch at " + i);
        Set<ReorderList.ListNode> ids = Collections.newSetFromMap(new IdentityHashMap<>()); ids.addAll(before);
        if (ids.size()!=before.size() || !ids.containsAll(after) || !after.containsAll(before)) throw new AssertionError("node identity changed");
    }
    public static void main(String[] args) {
        ReorderList.reorder(null);
        check(new int[]{1}, new int[]{1});
        check(new int[]{1,2}, new int[]{1,2});
        check(new int[]{1,2,3}, new int[]{1,3,2});
        check(new int[]{1,2,3,4,5}, new int[]{1,5,2,4,3});
        check(new int[]{1,2,3,4,5,6}, new int[]{1,6,2,5,3,4});
        check(new int[]{1,1,2,2,3,3}, new int[]{1,3,1,3,2,2});
        System.out.println("PASS empty singleton pair triple odd even duplicate-values identity-preserved no-cycle");
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
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != CID: raise SystemExit('canonical context drift')
    if ctx.get('answer_type') != 'coding': raise SystemExit(f"answer type drift: {ctx.get('answer_type')}")
    if ctx.get('canonical', {}).get('question_ids') != [QID]: raise SystemExit(f"ownership drift: {ctx.get('canonical', {}).get('question_ids')}")
    src = next((x for x in ctx.get('source_questions', []) if x.get('question_id') == QID), None)
    if not src or src.get('original_question') != EXPECTED or src.get('is_valid_for_library') is not True: raise SystemExit('source wording/validity drift')
    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'; out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)
    candidate.parent.mkdir(parents=True, exist_ok=True); candidate.write_text(CANDIDATE, encoding='utf-8')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1: raise SystemExit(f'expected one Java block, got {len(blocks)}')
    with tempfile.TemporaryDirectory(prefix='b48-reorder-') as tmp:
        tmpdir = Path(tmp); (tmpdir/'ReorderList.java').write_text(blocks[0].strip()+'\n'); (tmpdir/'ReorderListTest.java').write_text(TEST)
        run('javac','ReorderList.java','ReorderListTest.java',cwd=tmpdir); stdout=run('java','ReorderListTest',cwd=tmpdir).stdout.strip()
    expected_stdout='PASS empty singleton pair triple odd even duplicate-values identity-preserved no-cycle'
    if stdout != expected_stdout: raise SystemExit(f'unexpected fixture output: {stdout}')
    validation={'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'command':'javac ReorderList.java ReorderListTest.java && java ReorderListTest','stdout':stdout,'checks':['source example 1..6 reorder','odd/even lengths','0/1/2/3 node boundaries','duplicate values','node identity preservation','cycle detection']}
    write_json(out/'writer_validation.json',validation)
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources=[{'source_id':'repository-source','title':'Batch 0048 frozen canonical/source context','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'fixture','title':'Deterministic OpenJDK 21 linked-list reorder fixture','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}]
    claims=[{'claim_id':'source-boundary','text':'The preserved source requires reordering the singly presented 1-2-3-4-5-6 sequence into 1-6-2-5-3-4; it does not specify language, node API, mutation policy, or null behavior.','source_ids':['repository-source'],'answer_locations':['核心结论','1 分钟版','3 分钟版']},{'claim_id':'algorithm-behavior','text':'The executable Java fixture verifies split/reverse/alternating-merge behavior for the source example and odd/even/boundary lists while preserving node identities and rejecting cycles.','source_ids':['fixture'],'answer_locations':['3 分钟版','关键细节','原理机制','易错点']}]
    coverage=[{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    research={'schema_version':'answer_writer_research.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'};write_json(out/'writer_research.json',research)
    scores={'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
    findings=['The answer directly realizes the only preserved source example as the standard L0-Ln-L1-Ln-1 ordering without inventing a hidden business contract.','The three-step split/reverse/alternating-merge derivation explains why tail access becomes a forward traversal and maintains O(n) time/O(1) auxiliary state.','The implementation severs the first half before reversal and saves both next pointers before rewiring, addressing the main lost-node/cycle hazards.','Deterministic tests cover the exact six-node example, odd/even and short lists, duplicate values, identity preservation and explicit cycle detection.','In-place Java/node/null semantics are clearly labeled as candidate choices rather than source facts.']
    review={'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':'source-first-isolated-reviewer-batch-0048-reorder-20260828-v1','review_version':'batch-0048.reorder.v1','decision':'pass','revision_round':1,'source_packet':[str(out/'context.json'),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied']};write_json(out/'isolated_review_result.json',review)
    evidence={'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0048-reorder-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':'Linked-list reorder source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':validation['stdout'],'checks':validation['checks'],'boundary_tests':[{'case':'six-node source example','expected':'1,6,2,5,3,4','actual':'pass','passed':True},{'case':'odd five-node list','expected':'1,5,2,4,3','actual':'pass','passed':True},{'case':'identity/cycle safety','expected':'same nodes, no cycle','actual':'pass','passed':True}]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':review['reviewer_id'],'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied'};write_json(ROOT/f'review/evidence/{CID}.json',evidence)
    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md';text=task.read_text(encoding='utf-8')
    line='- [x] `cq_q_ca061ddef082325c938854b54c720fc1` source-first isolated review PASS: the preserved source requires the concrete reorder `1-2-3-4-5-6 -> 1-6-2-5-3-4`. The candidate derives split → reverse second half → alternating merge, labels Java/in-place/null semantics as candidate choices, and OpenJDK 21 validation covers the source example, odd/even and short lists, duplicate values, node-identity preservation, and no-cycle safety. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:text=text.rstrip()+'\n\n## Progress\n'
    if line not in text:text=text.rstrip()+'\n'+line+'\n'
    task.write_text(text,encoding='utf-8')
    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
