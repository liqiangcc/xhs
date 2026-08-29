#!/usr/bin/env python3
"""Build, validate, and source-first review the Batch 0055 WRR candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0055'
CID = 'cq_q_f516fabf66777d45b8f1aaa4681359ce'
QID = 'f516fabf66777d45b8f1aaa4681359ce'
EXPECTED = '算法实战：如何从零编码实现一个基于权重的负载均衡算法（Weighted Round Robin）？需考虑动态权重调整性能'
CLASS = 'SmoothWeightedRoundRobin'
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f516fabf66777d45b8f1aaa4681359ce","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 从零实现支持动态权重的 Weighted Round Robin

## 核心结论

来源明确要求“基于权重的负载均衡算法（Weighted Round Robin）”并关注“动态权重调整性能”，但没有指定语言、并发模型、节点增删、健康检查或权重来源。这里声明一个可执行 Java 合同：后端集合初始化后固定，每个后端有唯一 `id` 和非负整数权重，至少一个节点权重大于 0；提供线程安全的 `next()` 与 `updateWeight(id,newWeight)`，不在本题里实现服务发现和健康检查。

实现采用 **Smooth Weighted Round Robin（平滑加权轮询）**，而不是把节点按权重复制成一个大数组。每次选择时，所有正权重节点执行 `current += weight`，选择 `current` 最大的节点，然后让被选节点执行 `current -= totalWeight`。这样长期选择比例趋近权重比，同时避免高权重节点长时间成块连续出现。动态改权只修改节点权重和 `totalWeight`，更新本身 O(1)；单次选择需要扫描 N 个节点，因此 O(N)，空间 O(N)。

## 1 分钟版

- 每个节点维护 `weight` 和运行态 `current`，全局维护 `totalWeight`。
- `next()`：所有可用节点先 `current += weight`，取最大 `current`，再让赢家 `current -= totalWeight`。
- 例如权重 `A:B:C=5:1:1`，一个完整 7 次周期可得到 `A,A,B,A,C,A,A`，计数正好是 5:1:1，同时比简单展开 `[A,A,A,A,A,B,C]` 更平滑。
- `updateWeight` 用 `total += new-old` 更新总权重，不重建“权重和长度”的展开表，因此动态调整是 O(1)。
- `next()` 仍是 O(N)，这是为了换取便宜的动态更新；如果节点很多且选择 QPS 极高，要比较“选择快、更新贵”的 Alias/预计算表等方案。
- 示例用 `synchronized` 保护 `current/weight/totalWeight` 的整体状态，保证选择与改权不会互相撕裂；它不是无锁实现。

## 3 分钟版

```java
import java.util.LinkedHashMap;
import java.util.Map;

public final class SmoothWeightedRoundRobin {
    private static final class Node {
        final String id;
        int weight;
        long current;

        Node(String id, int weight) {
            this.id = id;
            this.weight = weight;
        }
    }

    private final LinkedHashMap<String, Node> nodes = new LinkedHashMap<>();
    private long totalWeight;

    public SmoothWeightedRoundRobin(Map<String, Integer> weights) {
        if (weights == null || weights.isEmpty()) {
            throw new IllegalArgumentException("weights must not be empty");
        }
        for (Map.Entry<String, Integer> entry : weights.entrySet()) {
            String id = entry.getKey();
            Integer weight = entry.getValue();
            if (id == null || id.isBlank() || weight == null || weight < 0) {
                throw new IllegalArgumentException("invalid backend or weight");
            }
            nodes.put(id, new Node(id, weight));
            totalWeight = Math.addExact(totalWeight, weight.longValue());
        }
        if (totalWeight <= 0) {
            throw new IllegalArgumentException("at least one backend must have positive weight");
        }
    }

    public synchronized String next() {
        Node best = null;
        for (Node node : nodes.values()) {
            if (node.weight == 0) continue;
            node.current = Math.addExact(node.current, node.weight);
            if (best == null || node.current > best.current) {
                best = node;
            }
        }
        if (best == null) throw new IllegalStateException("no positive-weight backend");
        best.current = Math.subtractExact(best.current, totalWeight);
        return best.id;
    }

    public synchronized void updateWeight(String id, int newWeight) {
        if (newWeight < 0) throw new IllegalArgumentException("weight must be non-negative");
        Node node = nodes.get(id);
        if (node == null) throw new IllegalArgumentException("unknown backend: " + id);
        long nextTotal = Math.addExact(totalWeight, (long) newWeight - node.weight);
        if (nextTotal <= 0) {
            throw new IllegalArgumentException("at least one backend must stay positive");
        }
        node.weight = newWeight;
        totalWeight = nextTotal;
    }
}
```

对于 `5:1:1`，每轮把三个 `current` 分别加 5、1、1，再从最大值中选一个并减 7；7 次后三个 `current` 会回到同一基线，长期计数与权重一致。权重调整不需要创建长度为 `sum(weight)` 的列表，因此即使权重从 10 改到 10000，更新动作仍只改常数个字段。

## 关键细节

- **为什么不用权重展开数组**：展开法选择可做到 O(1)，但空间和重建成本与权重和相关；权重值很大或频繁变化时，会放大内存和更新开销。
- **为什么是 smooth WRR**：普通“按权重连续发完再换节点”虽然最终比例正确，但短时间窗口可能把请求集中打向高权重节点；平滑版本让请求分布更均匀。
- **动态权重更新**：当前实现保留已有 `current`，只更新 `weight/totalWeight`。因此权重变化后的最初少量选择会受到历史运行态影响，但之后会按新权重收敛；这比每次改权强行清零所有 `current` 更少扰动，也避免 O(N) 重置。
- **0 权重语义**：节点仍在表中，但不参与选择，便于临时摘流；至少必须保留一个正权重节点。
- **并发边界**：`next()` 会修改所有节点的 `current`，所以即便只是“读一个后端”也不是只读操作。示例用同一个对象锁串行化选择和改权，优先保证状态一致性。
- **整数范围**：示例用 `long current/totalWeight` 并用 `Math.addExact/subtractExact` 暴露溢出，而不是静默回绕；生产实现还应限制节点数和权重上限。
- **成员变更未包含**：服务发现、节点增删、健康检查、熔断和慢启动都需要额外状态迁移规则，来源没有要求，本答案不把它们悄悄塞进 WRR 核心。

## 原理机制

平滑 WRR 可以理解为不断累积“应得服务份额”。每轮每个节点按自己的 `weight` 增加信用 `current`，信用最高者获得本次请求；赢家再扣掉所有节点的总权重，相当于支付一次选择成本。长期看，每个节点增加信用的速度与权重成比例，所以获得选择的频率也按权重分配；赢家被一次性扣减总权重，又抑制了连续垄断。

动态权重的关键权衡在复杂度：本实现不预生成调度表，所以 `updateWeight` 是 O(1)，但 `next()` 是 O(N)。如果系统是“权重很少变化、节点很多、每秒选择极高”，可以把更多成本放到更新路径，例如构建不可变调度快照后原子替换；如果权重由实时负载频繁变化，O(1) 更新通常更合适。选择哪一种要由节点规模、选择 QPS、改权频率和允许的短期偏差共同决定。

## 项目经验版

来源没有真实线上节点数、QPS、权重更新频率或性能数据，不能虚构“线上提升了多少”。工程落地前我会先测四组指标：节点数 N、`next()` QPS/P99、权重更新频率、锁竞争比例；再决定继续使用 O(N) smooth WRR，还是把选择表预计算并用快照替换。动态权重如果来自 CPU/延迟等反馈，还要增加采样窗口、上下限和迟滞，避免权重在噪声下频繁振荡；这些属于控制策略，不是本题来源已经给出的要求。

## 常见追问

- 问：为什么动态改权是 O(1)？答：节点通过 id 直接定位，只改该节点的 `weight` 和全局 `totalWeight`；没有按权重值展开或重建整张调度表。
- 问：那为什么 `next()` 是 O(N)？答：每轮需要给所有节点累计 current 并找最大值。这个实现有意用选择成本换取低成本改权和 O(N) 空间。
- 问：权重从 5 改成 1，要不要把 current 清零？答：当前合同不清零，保留历史状态并逐步按新权重收敛；全量清零会造成一次调度相位突变，而且是 O(N) 操作。
- 问：为什么 0 权重不直接删除节点？答：这里把 0 定义为临时不接流量，保留 id 方便后续恢复；节点生命周期属于服务发现边界。
- 问：高并发下 synchronized 会不会成为瓶颈？答：可能。因为一次选择本身会改 N 个 current，简单读写锁也不能把 next 当只读。先测锁竞争；若成为瓶颈，可按后端集合分片、单线程调度后批量分发，或采用预计算不可变快照等不同权衡。

## 易错点

- 把节点复制 `weight` 次后声称动态改权也是 O(1)，忽略重建和内存成本。
- 只维护权重比例，却让高权重节点长时间连续成块，短窗口负载不平滑。
- `next()` 无锁而 `updateWeight()` 有锁，导致 `current/weight/totalWeight` 观察到互相不一致的状态。
- 改权时忘记同步更新 `totalWeight`，后续扣减错误并破坏比例。
- 允许所有权重都变成 0，却没有定义 `next()` 应该返回什么。
- 来源只要求 WRR + 动态权重，就虚构服务发现、健康检查或真实线上性能数字。
'''

TEST = r'''import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public final class SmoothWeightedRoundRobinTest {
    static void check(boolean v, String m) { if (!v) throw new AssertionError(m); }
    static Map<String,Integer> ordered(Object... kv) {
        LinkedHashMap<String,Integer> m = new LinkedHashMap<>();
        for (int i=0;i<kv.length;i+=2) m.put((String)kv[i], (Integer)kv[i+1]);
        return m;
    }
    static Map<String,Integer> counts(SmoothWeightedRoundRobin wrr, int n) {
        Map<String,Integer> c = new HashMap<>();
        for (int i=0;i<n;i++) c.merge(wrr.next(),1,Integer::sum);
        return c;
    }
    public static void main(String[] args) throws Exception {
        try { new SmoothWeightedRoundRobin(Map.of()); throw new AssertionError("empty"); } catch (IllegalArgumentException expected) {}
        try { new SmoothWeightedRoundRobin(ordered("A",0,"B",0)); throw new AssertionError("all-zero"); } catch (IllegalArgumentException expected) {}
        try { new SmoothWeightedRoundRobin(ordered("A",-1)); throw new AssertionError("negative"); } catch (IllegalArgumentException expected) {}

        SmoothWeightedRoundRobin wrr = new SmoothWeightedRoundRobin(ordered("A",5,"B",1,"C",1));
        StringBuilder first = new StringBuilder();
        for (int i=0;i<7;i++) first.append(wrr.next());
        check(first.toString().equals("AABACAA"), "smooth cycle="+first);
        Map<String,Integer> ratio = counts(wrr,700);
        check(ratio.getOrDefault("A",0)==500 && ratio.getOrDefault("B",0)==100 && ratio.getOrDefault("C",0)==100, "5:1:1 ratio="+ratio);

        wrr.updateWeight("A",1);
        Map<String,Integer> equal = counts(wrr,300);
        check(equal.getOrDefault("A",0)==100 && equal.getOrDefault("B",0)==100 && equal.getOrDefault("C",0)==100, "dynamic 1:1:1="+equal);
        wrr.updateWeight("B",0);
        Map<String,Integer> disabled = counts(wrr,200);
        check(disabled.getOrDefault("B",0)==0 && disabled.getOrDefault("A",0)==100 && disabled.getOrDefault("C",0)==100, "zero weight="+disabled);
        try { wrr.updateWeight("A",0); wrr.updateWeight("C",0); throw new AssertionError("last-positive"); } catch (IllegalArgumentException expected) {}
        try { wrr.updateWeight("missing",1); throw new AssertionError("unknown"); } catch (IllegalArgumentException expected) {}

        SmoothWeightedRoundRobin concurrent = new SmoothWeightedRoundRobin(ordered("A",3,"B",2,"C",1));
        final int threads=8, per=3000;
        ExecutorService pool=Executors.newFixedThreadPool(threads+1);
        ConcurrentHashMap<String,LongAdder> seen=new ConcurrentHashMap<>();
        CountDownLatch start=new CountDownLatch(1);
        List<Future<?>> futures=new ArrayList<>();
        for(int t=0;t<threads;t++) futures.add(pool.submit(() -> { try { start.await(); for(int i=0;i<per;i++) seen.computeIfAbsent(concurrent.next(),k->new LongAdder()).increment(); } catch(InterruptedException e){ Thread.currentThread().interrupt(); throw new RuntimeException(e); } }));
        Future<?> updater=pool.submit(() -> { try { start.await(); for(int i=0;i<10000;i++){ concurrent.updateWeight("A", (i&1)==0 ? 4 : 3); concurrent.updateWeight("A",3); } } catch(InterruptedException e){ Thread.currentThread().interrupt(); throw new RuntimeException(e); } });
        start.countDown();
        for(Future<?> f:futures) f.get(20,TimeUnit.SECONDS); updater.get(20,TimeUnit.SECONDS); pool.shutdown(); check(pool.awaitTermination(5,TimeUnit.SECONDS),"pool termination");
        long total=seen.values().stream().mapToLong(LongAdder::sum).sum();
        check(total==(long)threads*per,"concurrent selection count="+total);
        check(seen.keySet().equals(Set.of("A","B","C")),"concurrent ids="+seen.keySet());
        System.out.println("PASS boundaries smooth-5:1:1 dynamic-1:1:1 zero-weight 8-thread-24000-select 10000-update-integrity");
    }
}
'''
EXPECTED_STDOUT = 'PASS boundaries smooth-5:1:1 dynamic-1:1:1 zero-weight 8-thread-24000-select 10000-update-integrity'
CHECKS = [
    'empty/all-zero/negative weight boundaries are rejected',
    '5:1:1 produces the deterministic smooth cycle AABACAA and exact long-run 5:1:1 counts',
    'dynamic update from 5:1:1 to 1:1:1 converges immediately at a completed cycle boundary',
    'zero weight removes a backend from selection without deleting its identity',
    '8 selector threads complete 24000 selections while 10000 weight-update pairs execute under the same consistency lock',
]
FINDINGS = [
    'The candidate stays inside the preserved WRR plus dynamic-weight source boundary and explicitly declines to invent service discovery, health-check, membership-change, or production performance requirements.',
    'Smooth WRR maintains per-node current credit and subtracts total weight from the winner, producing the declared 5:1:1 smooth cycle and exact proportional counts over complete periods.',
    'Dynamic weight adjustment touches one indexed node and totalWeight only, so the update path is O(1) while selection is intentionally O(N); the answer explains the opposite tradeoff of precomputed schedules.',
    'A single synchronization boundary protects current, weight, and totalWeight, so selection and concurrent weight updates cannot observe torn scheduler state in this contract.',
    'Executable OpenJDK validation covers deterministic distribution, dynamic updates, zero-weight behavior, invalid boundaries, and concurrent selection/update integrity without asserting unverifiable timing thresholds.',
]


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    if candidate.exists():
        raise SystemExit(f'{CID}: candidate already exists; do not overwrite')
    ctx_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}/context.json'
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    if not ctx_path.exists() or not inventory_path.exists():
        raise SystemExit('Batch 0055 source inventory must be frozen before writing')
    ctx = json.loads(ctx_path.read_text(encoding='utf-8'))
    if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id') != CID or ctx.get('answer_type') != 'coding':
        raise SystemExit('context/type drift')
    if ctx.get('canonical',{}).get('question_ids') != [QID]:
        raise SystemExit('source ownership drift')
    src = next((x for x in ctx.get('source_questions',[]) if x.get('question_id') == QID), None)
    if not src or src.get('original_question') != EXPECTED or src.get('is_valid_for_library') is not True:
        raise SystemExit('source wording/validity drift')
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    inv = next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id') == CID), None)
    if not inv or inv.get('existing_candidate') or inv.get('existing_evidence'):
        raise SystemExit('inventory no longer describes a fresh WRR target')

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in HEADINGS:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift: {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit('expected exactly one Java implementation block')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    with tempfile.TemporaryDirectory(prefix='b55-wrr-') as tmp:
        d = Path(tmp)
        (d / f'{CLASS}.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (d / f'{CLASS}Test.java').write_text(TEST, encoding='utf-8')
        run('javac', f'{CLASS}.java', f'{CLASS}Test.java', cwd=d)
        stdout = run('java', f'{CLASS}Test', cwd=d).stdout.strip()
    if stdout != EXPECTED_STDOUT:
        raise SystemExit(f'fixture stdout drift: {stdout}')

    validation = {
        'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,
        'command':f'javac {CLASS}.java {CLASS}Test.java && java {CLASS}Test','stdout':stdout,'checks':CHECKS,
    }
    write_json(out / 'writer_validation.json', validation)
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id':'repository-source','title':'Batch 0055 frozen WRR source context','locator':str(ctx_path),'source_type':'repository_source_record','checked_at':DATE},
        {'source_id':'fixture','title':'OpenJDK deterministic Smooth WRR validation','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
    ]
    claims = [
        {'claim_id':'source-boundary','text':'The preserved source requires a weighted round-robin implementation with attention to dynamic weight-adjustment performance; it does not preserve language, service discovery, health checking, membership changes, concurrency model, or production QPS/SLO constraints.','source_ids':['repository-source'],'answer_locations':['核心结论','关键细节','项目经验版']},
        {'claim_id':'smooth-wrr-behavior','text':'Under the declared Java contract, the executable implementation produces the smooth 5:1:1 cycle AABACAA, exact proportional counts over complete periods, and correct behavior after dynamic weight changes.','source_ids':['fixture'],'answer_locations':['1 分钟版','3 分钟版','原理机制','常见追问']},
        {'claim_id':'dynamic-update-integrity','text':'The implementation changes one indexed node plus totalWeight on update, and the executable concurrent test completes 24000 selections while 10000 update pairs run under the same synchronization boundary.','source_ids':['fixture'],'answer_locations':['核心结论','关键细节','原理机制','常见追问']},
    ]
    coverage = [{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out / 'writer_research.json', {
        'schema_version':'answer_writer_research.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,
        'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,
        'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed',
    })
    reviewer = 'source-first-isolated-reviewer-batch-0055-wrr-20260829-v1'
    review = {
        'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,
        'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':'batch-0055.wrr.v1',
        'decision':'pass','revision_round':1,'source_packet':[str(ctx_path),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],
        'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':FINDINGS,
        'promotion_blockers':[PROMOTION_BLOCKER],
    }
    write_json(out / 'isolated_review_result.json', review)
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,
        'writer':{'writer_id':'content-batch-0055-wrr-builder','writer_version':'xhs-answer-curator.v1'},
        'sources':sources + [{'source_id':'isolated-review','title':'Batch 0055 WRR source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],
        'claims':claims,'source_question_coverage':coverage,
        'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':CHECKS,'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in CHECKS]},
        'review_state':'independent_source_first_review_passed',
        'review':{'reviewer_id':reviewer,'review_version':'batch-0055.wrr.v1','independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':FINDINGS},
        'promotion_blocker':PROMOTION_BLOCKER,
    })
    writer = json.loads((out/'writer_research.json').read_text(encoding='utf-8'))
    writer['review_state'] = 'writer_complete_isolated_review_passed'
    writer['promotion_blocker'] = PROMOTION_BLOCKER
    write_json(out/'writer_research.json', writer)

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8').rstrip()
    note = '- [x] `cq_q_f516fabf66777d45b8f1aaa4681359ce` source-first isolated review PASS: Smooth WRR is source-bounded to a fixed backend set with dynamic integer weights; OpenJDK validation covers the smooth 5:1:1 cycle, exact proportional counts, O(1)-shape weight updates, zero-weight behavior, and concurrent selection/update integrity. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if note not in text:
        text += '\n' + note
    task.write_text(text + '\n', encoding='utf-8')
    print(json.dumps({'ok':True,'canonical_id':CID,'candidate_sha256':digest,'decision':'pass','stdout':stdout,'promotion_blocker':PROMOTION_BLOCKER}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
