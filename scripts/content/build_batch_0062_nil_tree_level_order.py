#!/usr/bin/env python3
"""Build and validate the source-bounded Batch 0062 nil-tree level-order candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path('.')
DATE='2026-08-31'
BATCH='0062'
CID='cq_q_00bc3ebd89c0d03aae8db0a36cd747e2'
QID='00bc3ebd89c0d03aae8db0a36cd747e2'
EXPECTED_VARIANT='算法：根据包含 nil 节点的数组生成二叉树，并完成层序遍历'
EXPECTED_STDOUT='PASS fixed=9 random_cases=25000 oracle=encode-rebuild-levels invalid_unreachable=pass nil_root=pass'

CANDIDATE=r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_00bc3ebd89c0d03aae8db0a36cd747e2","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 根据包含 nil 节点的数组生成二叉树，并完成层序遍历

## 核心结论

题面只说“包含 nil 节点的数组生成二叉树并层序遍历”，但没有说明数组编码规则；这里必须先把 `nil` 的语义说清楚。本答案采用常见的**按非 nil 父节点逐个消费左右孩子槽位的层序编码**，并用 Go 表达：输入 `[]*int`，第 0 项是根；随后从队列头部依次取非 nil 父节点，每个父节点最多消费两个后续槽位，`nil` 表示该孩子缺失。若队列已空但后面还有非 nil 值，则该值不可达，输入视为非法。构树后再做标准 BFS，输出 `[][]int`，每层一个切片。

## 1 分钟版

- 先定义编码契约：数组不是简单的“下标 `2i+1/2i+2` 完全二叉树公式”，而是按层序队列给每个真实父节点依次消费左、右两个孩子槽位。
- 空数组返回空树；首元素是 `nil` 时只有后续全为 `nil` 才接受，否则存在不可达非 nil 节点，返回错误。
- 构树时维护父节点队列；遇到非 nil 子槽就创建节点并入队，遇到 nil 只表示该方向没有孩子。
- 队列耗尽后检查剩余输入，任何非 nil 都说明编码非法；尾部多余 nil 可以忽略。
- 层序遍历再用一个 BFS 队列，每轮先冻结当前队列长度，消费恰好这一层并把孩子加入下一层。
- 构树和遍历都只线性访问可达节点/输入槽：时间 `O(m+n)`；构树队列和遍历队列的峰值空间都与树宽有关。

## 3 分钟版

```go
package treebuild

import "fmt"

type Node struct {
    Val         int
    Left, Right *Node
}

func BuildLevelOrder(vals []*int) (*Node, error) {
    if len(vals) == 0 {
        return nil, nil
    }
    if vals[0] == nil {
        for _, v := range vals[1:] {
            if v != nil {
                return nil, fmt.Errorf("unreachable non-nil node after nil root")
            }
        }
        return nil, nil
    }

    root := &Node{Val: *vals[0]}
    queue := []*Node{root}
    next := 1
    for len(queue) > 0 && next < len(vals) {
        parent := queue[0]
        queue = queue[1:]

        if next < len(vals) {
            if vals[next] != nil {
                parent.Left = &Node{Val: *vals[next]}
                queue = append(queue, parent.Left)
            }
            next++
        }
        if next < len(vals) {
            if vals[next] != nil {
                parent.Right = &Node{Val: *vals[next]}
                queue = append(queue, parent.Right)
            }
            next++
        }
    }
    for ; next < len(vals); next++ {
        if vals[next] != nil {
            return nil, fmt.Errorf("unreachable non-nil node at slot %d", next)
        }
    }
    return root, nil
}

func LevelOrder(root *Node) [][]int {
    if root == nil {
        return [][]int{}
    }
    result := make([][]int, 0)
    queue := []*Node{root}
    for len(queue) > 0 {
        width := len(queue)
        level := make([]int, 0, width)
        for i := 0; i < width; i++ {
            node := queue[0]
            queue = queue[1:]
            level = append(level, node.Val)
            if node.Left != nil {
                queue = append(queue, node.Left)
            }
            if node.Right != nil {
                queue = append(queue, node.Right)
            }
        }
        result = append(result, level)
    }
    return result
}
```

例如 `[1,2,3,nil,4,nil,5]`：根为 1；给父节点 1 消费 2、3；给父节点 2 消费 nil、4；给父节点 3 消费 nil、5。得到的层序结果是 `[[1],[2,3],[4,5]]`。这里的 `nil` 会占用一个孩子槽，但自身不会入父节点队列。

## 关键细节

- **先确认编码，不要猜**：另一种常见约定是完全二叉树数组下标公式 `left=2*i+1/right=2*i+2`。它和这里的“非 nil 父节点队列消费”在稀疏树上可能得到不同结果，必须由题目或接口契约决定。
- **nil 不入队**：`nil` 只占一个孩子槽；如果把 nil 也当父节点继续消费两个槽，就会把后续位置整体错位。
- **不可达输入**：例如 `[1,nil,nil,2]` 中根的两个孩子都为空，父队列已经耗尽，末尾 2 无法挂到任何节点，所以本契约返回错误而不是静默丢弃。
- **nil 根**：`[nil]` 或 `[nil,nil,nil]` 表示空树；`[nil,1]` 非法，因为 1 没有可达父节点。
- **层边界**：遍历时必须在每轮开始保存 `width := len(queue)`，然后只消费这 `width` 个节点；不能边 append 子节点边把它们也算进当前层。
- **重复值**：节点身份由位置/指针决定，不由值决定；两个值相同的节点仍需分别输出。
- **复杂度**：若输入槽数为 `m`、可达节点数为 `n`，构树 `O(m)`、遍历 `O(n)`；队列峰值是当前树宽度 `O(w)`，输出本身占 `O(n)`。

## 原理机制

构树过程本质上是在恢复一棵按 BFS 序列化的树。父节点队列保存“还有孩子槽待消费的真实节点”；每弹出一个父节点，就从输入游标顺序读取最多两个槽。非 nil 子节点成为新的待处理父节点，nil 只关闭对应的一条边。这个不变量保证输入游标单调前进且每个真实父节点恰好拥有左右两个槽位的解释机会。

遍历阶段是另一个 BFS：队列在一轮开始时恰好保存当前层节点，冻结长度后消费这些节点并把它们的非 nil 孩子追加到队尾，因此下一轮队列恰好对应下一层。

## 项目经验版

来源没有真实业务格式或线上序列化协议，不能虚构“项目里就是这种编码”。工程落地时最重要的是把编码写进接口契约并做 round-trip 测试：例如 JSON 中究竟用 `null`、缺字段还是稀疏数组表达空孩子；非法不可达槽位是拒绝、告警还是兼容忽略，都应由协议定义，而不是在构树函数里猜。

## 常见追问

- 问：为什么不能直接用 `2*i+1` 和 `2*i+2`？答：那对应另一种完全二叉树下标编码；当前答案声明的是“只给真实父节点消费孩子槽”的层序序列化，稀疏树上两者语义不同。
- 问：`nil` 节点为什么不进入队列？答：它表示边不存在，不是一个真实父节点；若入队会错误消耗后续孩子槽。
- 问：为什么 `[1,nil,nil,2]` 要报错？答：根已经没有任何真实孩子，父节点队列耗尽，2 没有可挂载的位置；本契约选择显式拒绝数据损坏。
- 问：尾部多几个 nil 怎么办？答：它们不引入不可达真实节点，本契约允许忽略；若协议要求严格最短编码，也可以改成拒绝，关键是先定义。
- 问：层序遍历怎么区分每一层？答：每轮开始冻结当前队列长度，只处理这些旧节点；本轮新增孩子留给下一轮。
- 问：如果只要一维 BFS 结果呢？答：构树不变，遍历时不需要冻结层长度或创建 `level`，按出队顺序直接追加到一个切片即可。

## 易错点

- 没说明数组编码规则，就默认 `2*i+1/2*i+2` 或默认队列消费。
- 把 nil 槽也加入父节点队列，导致后续孩子整体错位。
- 父队列耗尽后直接忽略剩余非 nil 输入，掩盖非法编码。
- BFS 中不冻结当前层长度，把下一层节点混入当前层。
- 用节点值判断是否重复，错误丢失值相同但位置不同的节点。
'''

GO_IMPL=r'''package treebuild

import "fmt"

type Node struct { Val int; Left, Right *Node }

func BuildLevelOrder(vals []*int) (*Node,error) {
    if len(vals)==0 { return nil,nil }
    if vals[0]==nil {
        for _,v:=range vals[1:] { if v!=nil { return nil,fmt.Errorf("unreachable non-nil node after nil root") } }
        return nil,nil
    }
    root:=&Node{Val:*vals[0]}; queue:=[]*Node{root}; next:=1
    for len(queue)>0 && next<len(vals) {
        p:=queue[0]; queue=queue[1:]
        if next<len(vals) { if vals[next]!=nil { p.Left=&Node{Val:*vals[next]}; queue=append(queue,p.Left) }; next++ }
        if next<len(vals) { if vals[next]!=nil { p.Right=&Node{Val:*vals[next]}; queue=append(queue,p.Right) }; next++ }
    }
    for ;next<len(vals);next++ { if vals[next]!=nil { return nil,fmt.Errorf("unreachable non-nil node at slot %d",next) } }
    return root,nil
}

func LevelOrder(root *Node) [][]int {
    if root==nil { return [][]int{} }
    result:=make([][]int,0); queue:=[]*Node{root}
    for len(queue)>0 { width:=len(queue); level:=make([]int,0,width); for i:=0;i<width;i++ { n:=queue[0]; queue=queue[1:]; level=append(level,n.Val); if n.Left!=nil { queue=append(queue,n.Left) }; if n.Right!=nil { queue=append(queue,n.Right) } }; result=append(result,level) }
    return result
}
'''

GO_TEST=r'''package treebuild

import (
    "fmt"
    "math/rand"
    "reflect"
    "testing"
)

func ip(v int)*int { x:=v; return &x }

func oracleLevels(root *Node) [][]int {
    out:=[][]int{}
    var dfs func(*Node,int)
    dfs=func(n *Node,d int){ if n==nil{return}; for len(out)<=d { out=append(out,[]int{}) }; out[d]=append(out[d],n.Val); dfs(n.Left,d+1); dfs(n.Right,d+1) }
    dfs(root,0); return out
}

func encode(root *Node) []*int {
    if root==nil { return []*int{} }
    vals:=[]*int{ip(root.Val)}; q:=[]*Node{root}
    for len(q)>0 { p:=q[0]; q=q[1:]; if p.Left!=nil { vals=append(vals,ip(p.Left.Val)); q=append(q,p.Left) } else { vals=append(vals,nil) }; if p.Right!=nil { vals=append(vals,ip(p.Right.Val)); q=append(q,p.Right) } else { vals=append(vals,nil) } }
    for len(vals)>1 && vals[len(vals)-1]==nil { vals=vals[:len(vals)-1] }
    return vals
}

func randomTree(r *rand.Rand,max int)*Node { if max<=0||r.Intn(5)==0{return nil}; root:=&Node{Val:r.Intn(21)-10}; q:=[]*Node{root}; count:=1; for len(q)>0&&count<max { p:=q[0];q=q[1:]; if count<max&&r.Intn(100)<62 { p.Left=&Node{Val:r.Intn(21)-10};q=append(q,p.Left);count++ }; if count<max&&r.Intn(100)<62 { p.Right=&Node{Val:r.Intn(21)-10};q=append(q,p.Right);count++ } }; return root }

func TestWriter(t *testing.T){
    fixed:=[]struct{vals []*int; want [][]int; invalid bool}{
        {[]*int{},[][]int{},false},
        {[]*int{nil},[][]int{},false},
        {[]*int{nil,nil,nil},[][]int{},false},
        {[]*int{nil,ip(1)},nil,true},
        {[]*int{ip(1)},[][]int{{1}},false},
        {[]*int{ip(1),ip(2),ip(3),nil,ip(4),nil,ip(5)},[][]int{{1},{2,3},{4,5}},false},
        {[]*int{ip(1),nil,nil,ip(2)},nil,true},
        {[]*int{ip(1),ip(2),nil,ip(3)},[][]int{{1},{2},{3}},false},
        {[]*int{ip(7),ip(7),ip(7)},[][]int{{7},{7,7}},false},
    }
    for i,c:=range fixed { root,err:=BuildLevelOrder(c.vals); if c.invalid { if err==nil { t.Fatalf("fixed %d expected error",i) }; continue }; if err!=nil { t.Fatalf("fixed %d err=%v",i,err) }; if got:=LevelOrder(root); !reflect.DeepEqual(got,c.want) { t.Fatalf("fixed %d got=%v want=%v",i,got,c.want) } }
    r:=rand.New(rand.NewSource(0x6200BC3E)); for i:=0;i<25000;i++ { original:=randomTree(r,1+r.Intn(80)); vals:=encode(original); rebuilt,err:=BuildLevelOrder(vals); if err!=nil { t.Fatalf("random %d err=%v",i,err) }; want:=oracleLevels(original); got:=LevelOrder(rebuilt); if !reflect.DeepEqual(got,want) { t.Fatalf("random %d got=%v want=%v vals=%v",i,got,want,vals) } }
    fmt.Println("PASS fixed=9 random_cases=25000 oracle=encode-rebuild-levels invalid_unreachable=pass nil_root=pass")
}
'''


def write_json(path,payload): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(args,cwd=None): return subprocess.run(args,cwd=cwd,text=True,capture_output=True,check=False)

def main():
    inventory_path=ROOT/f'review/content_build/answer_batch_{BATCH}/source_inventory.json'; inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result')!='pass': raise SystemExit('batch 0062 source inventory is not passing')
    item=next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id')==CID),None)
    if not item or item.get('answer_type')!='coding': raise SystemExit(f'{CID}: missing/non-coding inventory item')
    if item.get('question_ids')!=[QID] or item.get('source_question_count')!=1 or item.get('source_occurrence_count')!=1: raise SystemExit(f'{CID}: inventory ownership/occurrence drift')
    if {x.get('original_question') for x in item.get('source_questions',[])}!={EXPECTED_VARIANT}: raise SystemExit(f'{CID}: source wording drift')
    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}'; out.mkdir(parents=True,exist_ok=True)
    p=run(['node','scripts/xhs.js','answer','context','--canonical-id',CID,'--noWrite']);
    if p.returncode!=0: raise SystemExit(p.stderr or p.stdout)
    context=json.loads(p.stdout); write_json(out/'context.json',context)
    if not context.get('ok') or context.get('answer_type')!='coding': raise SystemExit(f'{CID}: context/type drift')
    if (context.get('canonical') or {}).get('question_ids')!=[QID]: raise SystemExit(f'{CID}: context ownership drift')
    rows=list(context.get('source_questions') or [])
    if len(rows)!=1 or rows[0].get('original_question')!=EXPECTED_VARIANT: raise SystemExit(f'{CID}: context source drift')
    candidate_path=ROOT/f'review/candidates/answers/{CID}.md'; candidate_path.parent.mkdir(parents=True,exist_ok=True); candidate_path.write_text(CANDIDATE,encoding='utf-8')
    (out/'treebuild.go').write_text(GO_IMPL,encoding='utf-8'); (out/'treebuild_test.go').write_text(GO_TEST,encoding='utf-8'); (out/'go.mod').write_text('module example.com/xhs/treebuild\n\ngo 1.23\n',encoding='utf-8')
    p=run(['go','test','-run','TestWriter','-v','.'],cwd=out)
    if p.returncode!=0: raise SystemExit(p.stderr or p.stdout)
    stdout_lines=[line.strip() for line in p.stdout.splitlines() if line.startswith('PASS fixed=')]
    if stdout_lines!=[EXPECTED_STDOUT]: raise SystemExit(f'{CID}: validation stdout drift: {stdout_lines!r}\n{p.stdout}')
    digest=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    write_json(out/'writer_validation.json',{'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'validator':'batch_0062_nil_tree_level_order_writer_fixture','command':'go test -run TestWriter -v .','stdout':EXPECTED_STDOUT,'checks':['empty/nil-root/single/sparse/duplicate-value fixed boundaries','unreachable non-nil slots are rejected','25,000 seeded random trees are encoded, rebuilt and compared to an independent DFS-by-depth level oracle','nil slots consume child positions without entering the parent queue']})
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':CID,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','candidate_sha256':digest,'source_occurrence_count':1,'sources':[{'source_id':'repository-source','title':'Batch 0062 frozen repository source packet for nil-tree construction and level order','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'fixture','title':'Go nil-tree build and level-order deterministic/randomized validation','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}],'claims':[{'claim_id':'source-boundary','text':'The source asks to build a binary tree from an array containing nil nodes and perform level-order traversal; the exact array encoding rule and API are not preserved source constraints.','source_ids':['repository-source'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节']},{'claim_id':'declared-encoding','text':'Under the explicitly declared queue-consumption encoding, the Go implementation reconstructs valid sparse trees, rejects unreachable non-nil slots and produces the same level groups as an independent DFS-by-depth oracle across fixed and 25,000 seeded random trees.','source_ids':['fixture'],'answer_locations':['3 分钟版','关键细节','原理机制','常见追问']}],'source_question_coverage':[{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问']}],'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    task_path=ROOT/'tasks/answer-batches/TASK-20260711-0313-answer-batch-0062.md'; task=task_path.read_text(encoding='utf-8')
    line='- [x] `cq_q_00bc3ebd89c0d03aae8db0a36cd747e2` writer stage complete: the frozen nil-tree source Question is covered by an explicit Go queue-consumption encoding contract; the implementation rejects unreachable non-nil slots and validates fixed nil/sparse/duplicate boundaries plus 25,000 seeded random encode→rebuild cases against an independent DFS-by-depth level oracle. Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    if line not in task: task=task.rstrip()+'\n'+line+'\n'; task_path.write_text(task,encoding='utf-8')
    print(f'PASS {CID} digest={digest} validation={EXPECTED_STDOUT}'); return 0

if __name__=='__main__': raise SystemExit(main())
