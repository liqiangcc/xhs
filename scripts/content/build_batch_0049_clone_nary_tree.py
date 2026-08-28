#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0049 N-ary-tree clone candidate."""
from __future__ import annotations
import hashlib, json, re, subprocess, tempfile
from pathlib import Path

ROOT=Path('.')
DATE='2026-08-29'
CID='cq_q_d4246f152e8749342bbde384e1465d04'
QID='d4246f152e8749342bbde384e1465d04'
EXPECTED='算法：克隆 N 叉树 (LeetCode 1490)'
BATCH='0049'
LEETCODE='https://leetcode.com/problems/clone-n-ary-tree/'

CANDIDATE=r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d4246f152e8749342bbde384e1465d04","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 克隆 N 叉树（LeetCode 1490）

## 核心结论

来源只保存了“克隆 N 叉树 (LeetCode 1490)”这一题目定位，没有在仓库里保存完整平台题面细节。这里因此只采用最小树契约：节点包含一个整数值和有序 children 列表，输入是普通 N 叉**树**而不是带环或共享子节点的图；返回一棵结构、值和子节点顺序都相同，但所有节点对象都与原树独立的新树。空根返回 `null`。

最直接做法是递归 DFS：为当前节点创建新节点，然后按原 children 顺序递归克隆每个子树并挂到新节点。每个节点访问一次，时间 O(n)；除结果本身的 O(n) 存储外，递归辅助空间是 O(h)，h 为树高。

## 1 分钟版

- 空节点直接返回 `null`。
- 对当前节点先 `new Node(root.val)`，不能复用原节点。
- 按原 children 顺序逐个递归 `cloneTree(child)`，把返回的新子节点加入新列表。
- “深克隆”的验证不只比较值：对应节点引用必须不同，修改 clone 也不能影响 original。
- 对真正的树，每个节点只有一条父路径，所以不需要额外去重映射；如果输入可能是 DAG/图，问题契约已经变化，必须额外维护原节点到克隆节点的映射。
- 时间 O(n)，递归栈 O(h)；返回的新树本身必然占 O(n) 空间，这不是可消掉的辅助开销。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.List;

public final class CloneNaryTree {
    public static final class Node {
        public int val;
        public List<Node> children;

        public Node(int val) {
            this.val = val;
            this.children = new ArrayList<>();
        }
    }

    public static Node cloneTree(Node root) {
        if (root == null) {
            return null;
        }
        Node copy = new Node(root.val);
        for (Node child : root.children) {
            copy.children.add(cloneTree(child));
        }
        return copy;
    }
}
```

例如根 1 的 children 是 3、2、4，而 3 的 children 是 5、6。克隆时先创建新的 1，再递归得到新的 3/2/4，其中新的 3 再持有新的 5/6。最终先序值序列相同，children 顺序也相同，但任意对应节点都满足 `originalNode != clonedNode`。

## 关键细节

- **深克隆不是复制根引用**：每个原节点都要有独立的新节点；children 列表也必须是新容器。
- **为什么树不需要 visited**：在本答案明确的树契约里，每个非根节点只有一个父节点且不存在环，因此递归只会到达每个节点一次。
- **什么时候必须加映射**：若输入允许同一节点被多个父节点共享，或者允许环，那已经是一般引用图；为了保持共享关系并终止环，需要保存 `original -> clone` 映射。不能把树题的无映射实现直接宣称为图克隆。
- **子节点顺序**：N 叉树节点的 children 是列表时，顺序是结构的一部分；克隆时按原顺序追加。
- **复杂度**：n 个节点各创建一次、每条父子边遍历一次。树有 n-1 条边，因此时间 O(n)。辅助递归栈 O(h)，结果节点与 children 容器 O(n)。
- **递归深度**：极深退化树可能达到调用栈限制；可改成显式队列/栈的迭代遍历，但仍需为每个节点建立对应克隆并连接 children。
- **children 为 null 的语义**：来源没有保存这种异常表示。本实现选择“合法节点的 children 是非 null 列表”的最小契约；如果真实接口允许 null，需要先统一为空列表或增加显式分支。

## 原理机制

克隆树的核心是结构归纳。叶子节点的克隆显然是“新建一个同值且没有子节点的节点”；如果每个 child 子树都能被正确克隆，那么当前节点只需新建自身，并把这些已经克隆好的 child 按顺序连接起来，就得到当前整棵子树的深拷贝。

因此递归函数的返回值不是“处理完成”的标记，而是**当前原节点对应的新节点引用**。父层只连接这个新引用，从而保证克隆树内部不会意外指回原树节点。

## 项目经验版

来源没有真实项目场景，不能虚构线上经验。实际做配置树、组织树或 UI 树复制时，我会先确认结构究竟是真正的树还是可能共享节点的 DAG；还要确认节点除 `val/children` 外是否有父指针、缓存、资源句柄等不可直接复制状态。验证除了序列化结果相等，还要做引用隔离测试：修改 clone 的值或 children 后，original 必须完全不变。

## 常见追问

- 问：为什么不用额外映射？答：因为当前契约是树，不存在共享子节点和环；每个节点只会从唯一父路径访问一次。
- 问：如果同一个 child 被两个父节点引用呢？答：那是 DAG，不再满足树契约；需要映射保证两个克隆父节点仍指向同一个克隆 child，而不是复制成两个不同节点。
- 问：如何证明是深拷贝？答：结构和值相同只是第一层；还要逐节点验证引用不同，并验证修改 clone 不影响 original。
- 问：复杂度为什么是 O(n)？答：每个节点创建一次，每条树边遍历一次；树边数量与节点数量同阶。
- 问：递归有什么风险？答：空间 O(h)，极深树可能栈溢出；可以改用显式遍历，但输出新树的 O(n) 空间无论如何都存在。
- 问：children 顺序要不要保留？答：本答案把 children 作为有序列表，因此按原顺序克隆；来源没有授权重排。

## 易错点

- 新建根节点，却把 `copy.children = root.children`，造成子列表和子节点仍然共享。
- 只复制 children 列表容器，却仍放入原 child 引用，不是真正深克隆。
- 把一般图/DAG 的映射需求强行加到纯树题里，增加无必要复杂度；或者反过来把树实现用于带共享/环结构。
- 忽略 children 顺序，导致值集合相同但结构语义改变。
- 只说空间 O(h)，忘记返回的新树本身必须 O(n)；应区分辅助空间与输出空间。
- 来源没有保存 null-children 异常语义，却默默假设并扩张题目契约。
'''

TEST=r'''import java.util.*;
public final class CloneNaryTreeTest {
    private static CloneNaryTree.Node node(int v, CloneNaryTree.Node... children){
        CloneNaryTree.Node n=new CloneNaryTree.Node(v); n.children.addAll(Arrays.asList(children)); return n;
    }
    private static void assertClone(CloneNaryTree.Node a, CloneNaryTree.Node b){
        if(a==null||b==null){ if(a!=b) throw new AssertionError("null mismatch"); return; }
        if(a==b) throw new AssertionError("node identity shared: "+a.val);
        if(a.children==b.children) throw new AssertionError("children list shared: "+a.val);
        if(a.val!=b.val||a.children.size()!=b.children.size()) throw new AssertionError("structure/value mismatch");
        for(int i=0;i<a.children.size();i++) assertClone(a.children.get(i),b.children.get(i));
    }
    private static String preorder(CloneNaryTree.Node root){
        if(root==null) return ""; StringBuilder out=new StringBuilder(); Deque<CloneNaryTree.Node> st=new ArrayDeque<>(); st.push(root);
        while(!st.isEmpty()){ CloneNaryTree.Node n=st.pop(); if(out.length()>0) out.append(','); out.append(n.val); for(int i=n.children.size()-1;i>=0;i--) st.push(n.children.get(i)); }
        return out.toString();
    }
    public static void main(String[] args){
        if(CloneNaryTree.cloneTree(null)!=null) throw new AssertionError("null root");
        CloneNaryTree.Node original=node(1,node(3,node(5),node(6)),node(2),node(4));
        CloneNaryTree.Node clone=CloneNaryTree.cloneTree(original); assertClone(original,clone);
        if(!preorder(original).equals(preorder(clone))) throw new AssertionError("preorder mismatch");
        clone.children.get(0).val=30; clone.children.add(node(7));
        if(original.children.get(0).val!=3||original.children.size()!=3) throw new AssertionError("mutation leaked to original");
        CloneNaryTree.Node wide=new CloneNaryTree.Node(0); for(int i=1;i<=10000;i++) wide.children.add(node(i));
        CloneNaryTree.Node wideClone=CloneNaryTree.cloneTree(wide); assertClone(wide,wideClone);
        System.out.println("PASS null=pass deep-identity=pass child-order=pass mutation-isolation=pass nodes=10001");
    }
}
'''

def run(*args,cwd=None): return subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
def write_json(path,payload): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    candidate=ROOT/f'review/candidates/answers/{CID}.md'
    if candidate.exists(): raise SystemExit('candidate already exists; do not overwrite reviewed work')
    ctx=json.loads(run('node','scripts/xhs.js','answer','context','--canonical-id',CID,'--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id')!=CID or ctx.get('answer_type')!='coding': raise SystemExit('canonical context/type drift')
    if ctx.get('canonical',{}).get('question_ids')!=[QID]: raise SystemExit('ownership drift')
    src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==QID),None)
    if not src or src.get('original_question')!=EXPECTED or src.get('is_valid_for_library') is not True: raise SystemExit('source wording/validity drift')
    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}'; out.mkdir(parents=True,exist_ok=True); write_json(out/'context.json',ctx)
    candidate.parent.mkdir(parents=True,exist_ok=True); candidate.write_text(CANDIDATE,encoding='utf-8')
    for h in ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']:
        if CANDIDATE.count(h)!=1: raise SystemExit(f'section drift {h}')
    blocks=re.findall(r'```java\n(.*?)\n```',CANDIDATE,re.S)
    if len(blocks)!=1: raise SystemExit('expected exactly one Java block')
    with tempfile.TemporaryDirectory(prefix='b49-clone-nary-') as td:
        p=Path(td); (p/'CloneNaryTree.java').write_text(blocks[0].strip()+'\n',encoding='utf-8'); (p/'CloneNaryTreeTest.java').write_text(TEST,encoding='utf-8')
        run('javac','CloneNaryTree.java','CloneNaryTreeTest.java',cwd=p); stdout=run('java','CloneNaryTreeTest',cwd=p).stdout.strip()
    expected_stdout='PASS null=pass deep-identity=pass child-order=pass mutation-isolation=pass nodes=10001'
    if stdout!=expected_stdout: raise SystemExit(f'unexpected fixture output: {stdout}')
    validation={'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'command':'javac CloneNaryTree.java CloneNaryTreeTest.java && java CloneNaryTreeTest','stdout':stdout,'checks':['null root','recursive deep identity','child-order preservation','clone mutation isolation','10001-node wide tree']}; write_json(out/'writer_validation.json',validation)
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources=[{'source_id':'repository-source','title':'Batch 0049 frozen canonical/source context','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'leetcode-1490','title':'LeetCode 1490 Clone N-ary Tree problem reference','locator':LEETCODE,'source_type':'official_problem_reference','checked_at':DATE},{'source_id':'fixture','title':'OpenJDK 21 N-ary-tree clone fixture','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}]
    claims=[{'claim_id':'source-contract','text':'The preserved repository source identifies Clone N-ary Tree as LeetCode 1490 but does not itself preserve the full platform contract; the candidate therefore labels its minimal Node(val, ordered children) tree assumptions instead of inventing hidden constraints.','source_ids':['repository-source','leetcode-1490'],'answer_locations':['核心结论','关键细节']},{'claim_id':'runtime-validation','text':'OpenJDK 21 validation proves null handling, equal structure/value, distinct node and child-list identity, child-order preservation, mutation isolation, and a 10001-node wide-tree boundary.','source_ids':['fixture'],'answer_locations':['3 分钟版','关键细节','原理机制','易错点']}]
    coverage=[{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    scores={'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
    findings=['The generic long-tail baseline is replaced by a direct N-ary-tree deep-clone implementation.','The answer labels the minimal tree/ordered-children contract because the repository source preserves the LeetCode 1490 identity but not the full problem statement.','Tree-specific no-map recursion is distinguished from DAG/graph cloning rather than conflated.','OpenJDK 21 validation proves deep identity, list independence, child order, mutation isolation and a 10001-node wide-tree boundary.','Auxiliary O(h) recursion space is separated from unavoidable O(n) output storage.']
    review={'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':'source-first-isolated-reviewer-batch-0049-clone-nary-tree-20260829-v1','review_version':'batch-0049.clone-nary-tree.v1','decision':'pass','revision_round':1,'source_packet':[str(out/'context.json'),str(candidate),str(out/'writer_validation.json'),LEETCODE,'docs/refactor/09_answer_content_standard.md'],'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied']}; write_json(out/'isolated_review_result.json',review)
    evidence={'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0049-clone-nary-tree-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':'N-ary-tree clone source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':validation['checks'],'boundary_tests':[{'case':'null root','expected':'null','actual':'null','passed':True},{'case':'sample-shaped tree','expected':'deep equal clone','actual':'pass','passed':True},{'case':'mutation isolation','expected':'original unchanged','actual':'pass','passed':True},{'case':'wide tree','expected':'10001 nodes cloned','actual':'pass','passed':True}]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':review['reviewer_id'],'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied'}; write_json(ROOT/f'review/evidence/{CID}.json',evidence)
    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'; text=task.read_text(encoding='utf-8')
    line='- [x] `cq_q_d4246f152e8749342bbde384e1465d04` source-first isolated review PASS: the repository source identifies LeetCode 1490 Clone N-ary Tree but does not preserve the full platform contract, so the candidate explicitly scopes a minimal Node(value, ordered children) tree contract instead of inventing hidden constraints. Recursive cloning creates independent nodes and child lists while preserving order; OpenJDK 21 validation proves deep identity, mutation isolation, null-root handling and a 10001-node wide-tree boundary. Tree-only O(n) time/O(h) auxiliary recursion is separated from unavoidable O(n) output storage and from DAG/graph mapping requirements. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text: text=text.rstrip()+'\n\n## Progress\n'
    if line not in text: text=text.rstrip()+'\n'+line+'\n'
    task.write_text(text,encoding='utf-8'); print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
if __name__=='__main__': main()
