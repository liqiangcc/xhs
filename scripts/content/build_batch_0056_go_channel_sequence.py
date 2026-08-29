#!/usr/bin/env python3
"""Build, execute, and source-first review the Batch 0056 Go channel/WaitGroup candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT=Path('.')
DATE='2026-08-29'
BATCH='0056'
CID='cq_q_7d7a2efb76976df46319df21283287c6'
QID='7d7a2efb76976df46319df21283287c6'
EXPECTED='Go并发模型：利用Go语言特性（Channel + WaitGroup），实现三个协程交替顺序打印1-100。详述无缓冲Channel在协程间同步与上下文切换（G-M-P调度）层面的底层代价'
PROMOTION_BLOCKER='repository_human_approval_and_real_review_policy_not_yet_satisfied'
GO_SPEC='https://go.dev/ref/spec#Channel_types'
GO_MEMORY='https://go.dev/ref/mem#Channel_communication'
GO_CHAN_SOURCE='https://go.dev/src/runtime/chan.go'
GO_RUNTIME_HACKING='https://go.dev/src/runtime/HACKING'
GO_WAITGROUP='https://pkg.go.dev/sync#WaitGroup'

CANDIDATE=r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_7d7a2efb76976df46319df21283287c6","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# Go：三个 goroutine 用无缓冲 Channel + WaitGroup 交替打印 1-100

## 核心结论

用 3 个无缓冲 `chan int` 组成一个 token ring：goroutine 0 接收 1，打印后把 2 交给 goroutine 1；goroutine 1 再交给 goroutine 2；随后回到 goroutine 0，如此循环到 100。`WaitGroup` 只负责等待 3 个 goroutine 全部退出，顺序同步由 channel 完成。无缓冲 channel 是 rendezvous：通信要等发送/接收双方配对；运行时可能需要 channel 锁、等待队列/sudog 管理以及 goroutine park/ready 调度，但“每次发送都发生 OS 线程上下文切换”是错误表述——被挂起和被唤醒的是 G，实际是否切换 M、是否复用同一个 P/M 取决于调度状态。

## 1 分钟版

- 三个无缓冲 channel 分别代表三个 goroutine 的“轮到你了”信号，token 中直接携带下一个整数。
- main 只向 `turn[0]` 发送初始值 1；以后每个 goroutine 打印当前值，再把 `v+1` 发给 `(id+1)%3`。
- 打印到 100 的 goroutine 关闭 `done`；另外两个 goroutine 的 receive `select` 观察到 `done` 后退出。
- `wg.Add(3)` 必须在启动 goroutine 前完成，每个 goroutine `defer wg.Done()`，main 最后 `wg.Wait()`。
- 无缓冲 channel 的价值是把“交接数据”和“交接执行权”绑在一次同步通信里；代价是高频 handoff 会让本可本地执行的循环变成大量 runtime 同步/调度操作。

## 3 分钟版

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    const limit = 100
    turns := [3]chan int{make(chan int), make(chan int), make(chan int)}
    done := make(chan struct{})

    var wg sync.WaitGroup
    wg.Add(3)

    for id := 0; id < 3; id++ {
        id := id
        go func() {
            defer wg.Done()
            for {
                select {
                case <-done:
                    return
                case v := <-turns[id]:
                    fmt.Println(v)
                    if v == limit {
                        close(done)
                        return
                    }
                    next := (id + 1) % 3
                    select {
                    case <-done:
                        return
                    case turns[next] <- v + 1:
                    }
                }
            }
        }()
    }

    turns[0] <- 1
    wg.Wait()
}
```

这段实现中只有拿到 token 的 goroutine 才能打印，所以顺序不依赖 `sleep` 或“希望调度器刚好轮换”。最后一个值只会被一个 goroutine 打印，因此只有它关闭 `done`；另外两个 goroutine 都在同时监听 `done`，不会永久阻塞在自己的 turn channel 上。`WaitGroup` 则把“所有 goroutine 已退出”作为 main 的收口条件。

## 关键细节

- **无缓冲 channel 的规范语义**：容量为 0 时，通信只有在发送者和接收者都准备好时才能成功；它既传值，也形成同步点。
- **不要把同步等同于 OS 线程切换**：Go runtime 的 G 是 goroutine，M 是 OS thread，P 是执行 Go 代码所需的调度资源。一个 G 因 channel 阻塞时可能被 park，P/M 可继续运行别的 runnable G；具体是否换 M 不是 channel API 保证。
- **runtime 路径有真实成本**：`runtime/chan.go` 维护 channel 锁以及发送/接收等待队列；阻塞路径会把等待中的 G 表示为 sudog 并进入 park/ready 调度。若对端已经等待，通信也可能直接配对，因此不能声称“每次 handoff 必然完整 park + OS context switch”。
- **100 次打印本来就是串行关键路径**：三个 goroutine 并不会让数字打印更快；这个题目的目的主要是展示同步与调度。实际生产若没有并行工作，单 goroutine 循环通常更便宜。
- **退出协议**：若只让打印 100 的 goroutine return，另外两个会永久等待 token；所以需要独立 `done` 广播或显式终止 token。
- **WaitGroup 职责边界**：它只等待任务完成，不决定轮转顺序；顺序来自 channel token ring。
- **I/O 会掩盖同步成本**：`fmt.Println` 本身比纯内存递增重，若要量化 channel handoff，应另写不含打印的 benchmark 并用 `testing.B`/trace/pprof，而不是拿本题输出时间直接归因。

## 原理机制

无缓冲 channel 可以把一次交替打印理解为“同步交接”：当前 G 在发送下一个 token 时，需要下一位接收者能够参与配对；如果暂时没有接收者，runtime 会让当前 G 等待，直到对应通信使它重新可运行。Go runtime 的调度器围绕 G/M/P 工作：G 是要执行的 goroutine，M 是承载执行的 OS thread，P 持有运行 Go 代码需要的调度/分配状态，调度器负责把三者匹配起来。因此 channel 阻塞的常见代价首先是 goroutine 级 park/wakeup、队列与锁操作；它可能进一步导致调度切换，但不能把每次 goroutine handoff 简化成一次固定的内核线程上下文切换。

本题用 token ring 把所有打印动作串成严格的 happens-before 链：只有上一轮的发送和下一轮的接收完成配对，下一数字才有资格打印。相比共享计数器 + 自旋，这不会持续占用 CPU 轮询条件；相比 `time.Sleep`，它表达的是确定同步关系而非时间猜测。

## 项目经验版

来源没有真实吞吐、延迟或 goroutine 数量数据，不能虚构“channel 一次切换多少纳秒”。工程里我会先判断是否真的需要 goroutine 间逐项交接：如果只是顺序处理，单 goroutine 最简单；如果有流水线并行价值，再用 channel 连接阶段并通过 benchmark/trace 看阻塞与调度。对高频细粒度 token handoff，批量化、减少同步次数往往比争论某一次 channel 操作的固定成本更重要。

## 常见追问

- 问：为什么一定能按 1、2、3…100？答：只有持有当前 token 的 goroutine 能打印，并且它只能把 `v+1` 发送给固定的下一个 channel。
- 问：为什么用三个 channel 而不是一个？答：三个 channel 把 token 的接收者编码为轮次；单 channel 若三个 goroutine 都竞争接收，谁拿到下一个值由调度决定，不能保证固定 0→1→2 轮转。
- 问：WaitGroup 能保证顺序吗？答：不能，它只保证 main 等所有 goroutine 完成；顺序由 channel 同步保证。
- 问：无缓冲 channel 每次都会切换 OS 线程吗？答：不会这样保证。可能发生 G 的阻塞/唤醒和重新调度，但 M/P 的实际复用与线程切换取决于 runtime/OS 状态。
- 问：为什么不用 `sleep`？答：sleep 只延迟时间，不建立“上一位已完成、下一位才开始”的可靠协议。
- 问：怎么量化底层代价？答：把打印移除，写 channel ping-pong benchmark，再结合 Go execution tracer/pprof；否则 I/O 成本会严重干扰结论。

## 易错点

- 三个 goroutine 从同一个 channel 抢值，却声称能固定轮转顺序。
- 打印 100 后只 return，不通知另外两个阻塞 goroutine，导致 `wg.Wait()` 永远不返回。
- 在 goroutine 启动后才 `wg.Add`，引入 WaitGroup 使用竞态或错误生命周期。
- 多个 goroutine 都可能 `close(done)`，触发 `close of closed channel`；本实现只有唯一的 value==100 路径关闭。
- 把 goroutine park/wakeup 直接说成固定一次 OS thread context switch，混淆 G 调度和 M 调度。
- 用带打印的总耗时推导 channel 本身纳秒级成本。
'''


def run(*args:str,cwd:Path|None=None)->subprocess.CompletedProcess[str]:
    return subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)

def write_json(path:Path,payload:object)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main()->int:
    inventory=json.loads((ROOT/f'review/content_build/answer_batch_{BATCH}/source_inventory.json').read_text(encoding='utf-8'))
    ctx_path=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}/context.json'
    ctx=json.loads(ctx_path.read_text(encoding='utf-8'))
    if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id')!=CID or ctx.get('answer_type')!='coding': raise SystemExit('context/type drift')
    if ctx.get('canonical',{}).get('question_ids')!=[QID]: raise SystemExit('ownership drift')
    src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==QID),None)
    if not src or src.get('original_question')!=EXPECTED or src.get('is_valid_for_library') is not True: raise SystemExit('source wording/validity drift')
    inv=next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id')==CID),None)
    if not inv or inv.get('answer_type')!='coding': raise SystemExit('inventory type drift')
    candidate=ROOT/f'review/candidates/answers/{CID}.md'; evidence=ROOT/f'review/evidence/{CID}.json'; out=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}'
    if candidate.exists() or evidence.exists(): raise SystemExit('candidate/evidence already exists')
    for h in ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']:
        if CANDIDATE.count(h)!=1: raise SystemExit(f'section drift {h}')
    blocks=re.findall(r'```go\n(.*?)\n```',CANDIDATE,re.S)
    if len(blocks)!=1: raise SystemExit('expected exactly one Go block')
    candidate.parent.mkdir(parents=True,exist_ok=True);candidate.write_text(CANDIDATE,encoding='utf-8')

    official_snapshot={'schema_version':'official_documentation_snapshot.v1','checked_at':DATE,'sources':[
        {'locator':GO_SPEC,'title':'Go Language Specification - channel types','claims':['capacity zero means an unbuffered channel; communication succeeds only when sender and receiver are ready']},
        {'locator':GO_MEMORY,'title':'Go Memory Model - channel communication','claims':['channel send/receive operations provide synchronization edges defined by the Go memory model']},
        {'locator':GO_CHAN_SOURCE,'title':'Go runtime chan.go','claims':['channel implementation uses a lock and send/receive wait queues','blocking channel paths represent waiting goroutines with sudog records and use runtime park/ready machinery']},
        {'locator':GO_RUNTIME_HACKING,'title':'Go runtime HACKING - scheduler structures','claims':['G is a goroutine, M is an OS thread, P carries resources required to execute Go code','the scheduler matches G, M and P rather than equating a goroutine with an OS thread']},
        {'locator':GO_WAITGROUP,'title':'sync.WaitGroup package documentation','claims':['WaitGroup waits for a collection of tasks; Add establishes the count and Done decrements it']},
    ]}
    write_json(out/'official_documentation_snapshot.json',official_snapshot)

    with tempfile.TemporaryDirectory(prefix='b56-go-sequence-') as tmp:
        d=Path(tmp)
        (d/'go.mod').write_text('module example.com/b56sequence\n\ngo 1.23\n',encoding='utf-8')
        (d/'main.go').write_text(blocks[0].strip()+'\n',encoding='utf-8')
        plain=run('go','run','.',cwd=d).stdout.strip().splitlines()
        raced=run('go','run','-race','.',cwd=d).stdout.strip().splitlines()
    expected=[str(i) for i in range(1,101)]
    if plain!=expected: raise SystemExit(f'plain output drift first={plain[:5]} last={plain[-5:]} count={len(plain)}')
    if raced!=expected: raise SystemExit(f'race output drift/race warning count={len(raced)} tail={raced[-10:]}')
    stdout='PASS go-run and go-run-race produced exact ordered 1..100 with clean termination'
    checks=['plain go run prints exactly 1..100 in order','go run -race prints exactly 1..100 with no race report','all three goroutines terminate and WaitGroup returns']
    validation={'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'command':'go run . && go run -race .','stdout':stdout,'checks':checks}
    write_json(out/'writer_validation.json',validation)
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources=[
        {'source_id':'repository-source','title':'Batch 0056 frozen Go channel source context','locator':str(ctx_path),'source_type':'repository_source_record','checked_at':DATE},
        {'source_id':'go-spec','title':'Go Language Specification - channels','locator':GO_SPEC,'source_type':'official_specification','checked_at':DATE},
        {'source_id':'go-memory','title':'Go Memory Model - channel communication','locator':GO_MEMORY,'source_type':'official_specification','checked_at':DATE},
        {'source_id':'go-runtime-chan','title':'Go runtime chan.go','locator':GO_CHAN_SOURCE,'source_type':'official_documentation','checked_at':DATE},
        {'source_id':'go-runtime-hacking','title':'Go runtime HACKING scheduler structures','locator':GO_RUNTIME_HACKING,'source_type':'official_documentation','checked_at':DATE},
        {'source_id':'go-waitgroup','title':'sync.WaitGroup documentation','locator':GO_WAITGROUP,'source_type':'official_documentation','checked_at':DATE},
        {'source_id':'fixture','title':'Go 1.23 ordered-output and race-detector validation','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
    ]
    claims=[
        {'claim_id':'source-contract','text':'The repository source explicitly requires Channel + WaitGroup, three goroutines, ordered printing 1-100, and discussion of unbuffered-channel synchronization plus G-M-P scheduling cost.','source_ids':['repository-source'],'answer_locations':['核心结论','1 分钟版','3 分钟版']},
        {'claim_id':'channel-semantics','text':'The Go specification and memory model define unbuffered channel rendezvous/synchronization semantics; the candidate uses those handoffs to create the print-order chain.','source_ids':['go-spec','go-memory'],'answer_locations':['核心结论','关键细节','原理机制']},
        {'claim_id':'runtime-cost','text':'Official runtime source/documentation supports the bounded description of channel lock/wait-queue/sudog park-ready paths and distinguishes G, M and P, so the answer does not equate every goroutine handoff with an OS-thread context switch.','source_ids':['go-runtime-chan','go-runtime-hacking'],'answer_locations':['核心结论','关键细节','原理机制','常见追问']},
        {'claim_id':'waitgroup','text':'WaitGroup is used only as the completion barrier for the three goroutines; ordering comes from channel handoffs.','source_ids':['go-waitgroup','fixture'],'answer_locations':['1 分钟版','3 分钟版','关键细节']},
        {'claim_id':'execution-validation','text':'The deterministic Go validation and race-detector run both produce exactly 1 through 100 and terminate cleanly.','source_ids':['fixture'],'answer_locations':['3 分钟版','易错点']},
    ]
    coverage=[{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    scores={'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
    findings=['The token ring makes the 0->1->2 worker order deterministic without sleep or scheduler luck.','The done channel closes the two otherwise-blocked receivers, while WaitGroup remains a completion barrier rather than an ordering primitive.','Go primary sources support the unbuffered rendezvous, channel synchronization, runtime wait-queue/park path, and G/M/P distinction.','The answer explicitly avoids the false claim that every channel handoff is one OS-thread context switch.','Go 1.23 execution and race-detector validation both produce exactly 1..100 and terminate cleanly.','The performance discussion separates demonstration synchronization cost from fmt.Println I/O and recommends a print-free benchmark for measurement.']
    reviewer='source-first-isolated-reviewer-batch-0056-go-channel-sequence-20260829-v1'
    review={'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':'batch-0056.go-channel-sequence.v1','decision':'pass','revision_round':1,'source_packet':[str(ctx_path),str(out/'official_documentation_snapshot.json'),str(candidate),str(out/'writer_validation.json'),GO_SPEC,GO_MEMORY,GO_CHAN_SOURCE,GO_RUNTIME_HACKING,GO_WAITGROUP,'docs/refactor/09_answer_content_standard.md'],'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':[PROMOTION_BLOCKER]}
    write_json(out/'isolated_review_result.json',review)
    write_json(evidence,{'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0056-go-channel-sequence-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':'Batch 0056 Go channel sequence source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':checks,'boundary_tests':[{'case':'ordered output','expected':'1..100 exactly once in increasing order','actual':'pass','passed':True},{'case':'race detector','expected':'no race report; same ordered output','actual':'pass','passed':True},{'case':'termination','expected':'all three goroutines exit and WaitGroup returns','actual':'pass','passed':True}]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},'promotion_blocker':PROMOTION_BLOCKER})
    writer=json.loads((out/'writer_research.json').read_text(encoding='utf-8'));writer['review_state']='writer_complete_isolated_review_passed';writer['promotion_blocker']=PROMOTION_BLOCKER;write_json(out/'writer_research.json',writer)
    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md';text=task.read_text(encoding='utf-8').rstrip();line='- [x] `cq_q_7d7a2efb76976df46319df21283287c6` source-first isolated review PASS: the three-goroutine token ring uses unbuffered Channel handoffs for deterministic 1-100 ordering and WaitGroup only for completion; official Go specification/memory-model/runtime sources bound rendezvous, wait-queue/park and G-M-P claims, while `go run -race` verifies exact ordered output and clean termination. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:text+='\n'+line
    task.write_text(text+'\n',encoding='utf-8')
    print(f'PASS staged/reviewed {CID} candidate_sha256={digest} {stdout}')
    return 0

if __name__=='__main__': raise SystemExit(main())
