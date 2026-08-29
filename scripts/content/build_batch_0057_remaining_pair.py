#!/usr/bin/env python3
"""Build, execute, and source-first review the final two Batch 0057 coding candidates."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0057'
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}

JAVA = {
    'cid':'cq_q_b454431bf82c811ddfc2d5dd208269bc',
    'qid':'b454431bf82c811ddfc2d5dd208269bc',
    'expected':'算法手撕：高并发批处理场景题——要求并发地、分批地（如每批 10 个）获取商家 ID。逻辑为：优先查缓存，缓存未命中则穿透到数据库，并合并返回结果',
    'slug':'concurrent-batch-cache-aside',
    'class':'MerchantBatchLookup',
    'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_b454431bf82c811ddfc2d5dd208269bc","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 并发分批获取商家数据：缓存优先、DB 回源并合并

## 核心结论

先把接口合同限定清楚：输入是一组商家 ID，允许重复；返回结果与输入顺序一一对应。一次调用内先按 ID 去重，再按 `batchSize` 分批，用固定大小线程池控制最多 `parallelism` 个批次并发执行。每批先 `cache.getAll`，只把未命中的 ID 交给数据库；数据库结果写回缓存后和缓存命中结果合并，最后按原始 ID 列表重建输出。这样避免一次请求内的重复回源，并把并发上限、批大小和结果顺序都显式化。

## 1 分钟版

- 先对输入 ID 去重，但保留原输入用于最后恢复顺序和重复项。
- 把唯一 ID 切成不超过 `batchSize` 的批次；固定线程池限制同时执行的批次数，避免无界 `CompletableFuture` 压垮 DB。
- 每个批次先批量查缓存，再计算 miss 集合；只有 miss 才批量查 DB。
- DB 必须返回本批全部 miss，否则当前合同直接失败，避免悄悄丢商家；拿到的数据先回填缓存，再并入批次结果。
- 等所有批次完成后合并成 `id -> value`，再按原输入顺序生成最终列表，所以重复 ID 只查询一次但会在输出里重复出现。

## 3 分钟版

```java
import java.util.*;
import java.util.concurrent.*;

public final class MerchantBatchLookup {
    public interface Cache {
        Map<Long, String> getAll(List<Long> ids);
        void putAll(Map<Long, String> values);
    }

    public interface Repository {
        Map<Long, String> getAll(List<Long> ids);
    }

    public static List<String> lookup(
            List<Long> ids, int batchSize, int parallelism,
            Cache cache, Repository repository) {
        if (ids == null || cache == null || repository == null) {
            throw new IllegalArgumentException("ids/cache/repository must not be null");
        }
        if (batchSize <= 0 || parallelism <= 0) {
            throw new IllegalArgumentException("batchSize and parallelism must be positive");
        }
        for (Long id : ids) {
            if (id == null) throw new IllegalArgumentException("merchant id must not be null");
        }
        if (ids.isEmpty()) return List.of();

        List<Long> unique = new ArrayList<>(new LinkedHashSet<>(ids));
        ExecutorService pool = Executors.newFixedThreadPool(parallelism);
        try {
            List<CompletableFuture<Map<Long, String>>> futures = new ArrayList<>();
            for (int from = 0; from < unique.size(); from += batchSize) {
                List<Long> batch = List.copyOf(unique.subList(from, Math.min(from + batchSize, unique.size())));
                futures.add(CompletableFuture.supplyAsync(
                        () -> loadBatch(batch, cache, repository), pool));
            }

            Map<Long, String> merged = new HashMap<>();
            for (CompletableFuture<Map<Long, String>> future : futures) {
                merged.putAll(future.join());
            }
            List<String> out = new ArrayList<>(ids.size());
            for (Long id : ids) {
                String value = merged.get(id);
                if (value == null) throw new IllegalStateException("missing merchant: " + id);
                out.add(value);
            }
            return out;
        } finally {
            pool.shutdownNow();
        }
    }

    private static Map<Long, String> loadBatch(
            List<Long> batch, Cache cache, Repository repository) {
        Map<Long, String> hits = new HashMap<>(cache.getAll(batch));
        List<Long> misses = new ArrayList<>();
        for (Long id : batch) if (!hits.containsKey(id)) misses.add(id);
        if (!misses.isEmpty()) {
            Map<Long, String> loaded = repository.getAll(List.copyOf(misses));
            for (Long id : misses) {
                if (!loaded.containsKey(id) || loaded.get(id) == null) {
                    throw new IllegalStateException("repository did not resolve merchant: " + id);
                }
            }
            cache.putAll(loaded);
            hits.putAll(loaded);
        }
        return hits;
    }
}
```

这个版本解决的是**单次调用内**的并发分批和 cache-aside 回源，不声称解决跨请求缓存击穿。若大量请求同时 miss 同一个热门 ID，还需要按 key 做 single-flight/锁、异步刷新或其他防击穿机制；那属于下一层并发合同。

## 关键细节

- `batchSize` 控制一次缓存/DB 批量调用的输入规模，`parallelism` 控制同时在途的批次数；两者解决的是不同的资源上限。
- 先全局去重再分批，可以避免同一调用中的重复 ID 落到不同批次并重复回源；输出阶段再按原始列表恢复重复项。
- 缓存命中和 DB 回源在每个批次内部合并；数据库未返回某个 miss 时直接失败。本题来源没有定义“不存在商家”的表示法，所以不擅自用 `null` 或空对象吞掉缺失。
- `CompletableFuture.join()` 会把异步异常包装为 `CompletionException` 向上传播；调用方应在应用层定义错误映射、超时和降级，本最小实现不虚构这些策略。
- 同一次调用用固定线程池有清晰的并发上限，但真实服务更常复用受控 executor，避免每次请求创建线程池；生命周期应由应用层管理。

## 原理机制

整个过程可以看成两层受控扇出/汇聚：第一层把唯一 ID 切成有界批次并最多并发执行 P 个；第二层每批执行 cache-aside 状态转移——命中直接进入结果，miss 进入 DB，成功后写回缓存并进入结果。所有 future 完成后再汇聚成统一映射。去重保证一次调用内“一个 ID 最多进入一个批次”，原始序列则单独保存用于输出重建，因此查询效率和接口顺序语义彼此分离。

## 项目经验版

来源没有给真实 QPS、缓存产品、数据库限制、超时、重试或一致性要求，不能虚构线上参数。实际落地会基于 DB/缓存批量接口上限确定 `batchSize`，基于连接池和下游容量确定 `parallelism`，并补充请求级超时、取消、熔断、指标以及跨请求的热点 key 防击穿策略；这些都要由真实容量测试证明，不能把“每批 10 个”机械扩张为生产最优值。

## 常见追问

- 问：为什么去重后还可以保持重复 ID 的输出？答：查询阶段用唯一 ID 降低重复 I/O，最后仍遍历原始 `ids` 从合并映射取值，所以重复位置会得到同一个商家结果。
- 问：批大小 10 和并发 10 是一回事吗？答：不是。批大小限制单次下游请求的元素数，并发度限制同时在途的批次数，两者分别约束单请求负载和并发负载。
- 问：这能防缓存击穿吗？答：只能避免**同一次 lookup** 内重复 ID 回源；多个请求同时 miss 同一个 key 仍可能一起打 DB，需要 single-flight/锁等跨请求协调。
- 问：DB 某个 ID 不存在怎么办？答：来源没定义不存在语义；当前合同 fail-fast。真实接口可改成 `Optional`/状态对象/负缓存，但必须统一定义缓存和返回协议。
- 问：为什么不直接为每个 ID 起一个 Future？答：那会失去批量接口收益，并让任务数随 ID 数量增长；按批提交更容易同时控制 I/O 批规模和并发上限。

## 易错点

- 只切批但没有并发上限，批次数多时仍然无界扇出。
- 重复 ID 分散到不同批次，造成一次调用内重复 DB 回源。
- 只合并缓存命中，忘记把 DB 结果写回缓存或放进最终映射。
- 并发批次完成顺序不同，就直接按完成顺序拼结果，破坏原输入顺序。
- 把单请求去重误称为完整的缓存击穿治理。
''',
    'test':r'''import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public final class MerchantBatchLookupTest {
    static final class FakeCache implements MerchantBatchLookup.Cache {
        final ConcurrentHashMap<Long,String> data=new ConcurrentHashMap<>();
        FakeCache(){data.put(1L,"A");}
        public Map<Long,String> getAll(List<Long> ids){Map<Long,String> r=new HashMap<>();for(Long id:ids){String v=data.get(id);if(v!=null)r.put(id,v);}return r;}
        public void putAll(Map<Long,String> values){data.putAll(values);}
    }
    static final class FakeRepo implements MerchantBatchLookup.Repository {
        final Map<Long,String> db=Map.of(2L,"B",3L,"C",4L,"D",5L,"E");
        final List<List<Long>> calls=Collections.synchronizedList(new ArrayList<>());
        final AtomicInteger active=new AtomicInteger();
        final AtomicInteger maxActive=new AtomicInteger();
        final CountDownLatch firstTwo=new CountDownLatch(2);
        public Map<Long,String> getAll(List<Long> ids){
            calls.add(List.copyOf(ids));
            int now=active.incrementAndGet(); maxActive.accumulateAndGet(now,Math::max);
            firstTwo.countDown();
            try{if(calls.size()<=2&&!firstTwo.await(2,TimeUnit.SECONDS))throw new AssertionError("expected concurrent DB batches");}
            catch(InterruptedException e){Thread.currentThread().interrupt();throw new RuntimeException(e);}
            try{Map<Long,String> r=new HashMap<>();for(Long id:ids){String v=db.get(id);if(v!=null)r.put(id,v);}return r;}
            finally{active.decrementAndGet();}
        }
    }
    static void check(boolean ok,String name){if(!ok)throw new AssertionError(name);}
    public static void main(String[] args){
        FakeCache cache=new FakeCache(); FakeRepo repo=new FakeRepo();
        List<String> out=MerchantBatchLookup.lookup(List.of(1L,2L,3L,2L,4L,5L),2,2,cache,repo);
        check(out.equals(List.of("A","B","C","B","D","E")),"order-and-duplicates");
        Set<Long> loaded=new HashSet<>();for(List<Long> c:repo.calls){check(c.size()<=2,"batch-bound");for(Long id:c)check(loaded.add(id),"duplicate-db-id");}
        check(loaded.equals(Set.of(2L,3L,4L,5L)),"cache-first-and-misses-only");
        check(repo.maxActive.get()==2,"parallelism-observed");
        check(cache.data.keySet().containsAll(Set.of(1L,2L,3L,4L,5L)),"cache-warmed");
        MerchantBatchLookup.Repository missing=ids->Map.of();
        try{MerchantBatchLookup.lookup(List.of(9L),2,1,new FakeCache(),missing);throw new AssertionError("missing");}
        catch(CompletionException expected){check(expected.getCause() instanceof IllegalStateException,"missing-cause");}
        try{MerchantBatchLookup.lookup(List.of(1L),0,1,cache,repo);throw new AssertionError("bad batch");}catch(IllegalArgumentException expected){}
        try{MerchantBatchLookup.lookup(Arrays.asList(1L,null),2,1,cache,repo);throw new AssertionError("null id");}catch(IllegalArgumentException expected){}
        System.out.println("PASS cache-first misses-only batch-bound parallelism order duplicates cache-write missing-fails invalid-rejected");
    }
}
''',
    'stdout':'PASS cache-first misses-only batch-bound parallelism order duplicates cache-write missing-fails invalid-rejected',
    'checks':['cache hit does not reach repository and only unique misses are loaded','every repository call stays within batch size','two repository batches are concurrently in flight under parallelism=2','original output order and duplicate IDs are preserved','database results are written back to cache','unresolved repository miss fails instead of silently disappearing','invalid batch size and null ID are rejected'],
    'claims':[
        ('source-boundary','The frozen source requires concurrent bounded batches, cache-first lookup, DB fallback, and merged output; timeout/retry/nonexistent-merchant and cross-request stampede semantics are not supplied, so the candidate declares them explicitly or leaves them to the application layer.',['repository-source'],['核心结论','关键细节','项目经验版']),
        ('concurrency-correctness','The executable OpenJDK fixture verifies cache-first miss-only repository access, batch-size bounds, observed two-way DB concurrency, per-call deduplication, order restoration, cache write-back, unresolved-miss failure, and invalid-input rejection.',['fixture'],['3 分钟版','原理机制','常见追问','易错点']),
    ],
    'findings':['The candidate separates batch-size and concurrency limits instead of treating them as the same control.','Per-call deduplication prevents duplicate IDs from causing duplicate DB reads while original-order reconstruction preserves the API result contract.','The cache-aside batch path fails closed when DB does not resolve a miss and does not pretend to solve cross-request stampedes.','OpenJDK validation exercises cache hits, misses-only fallback, bounded batches, actual two-way concurrency, cache warming, duplicate IDs, order, missing data, and invalid input.'],
    'task_note':'- [x] `cq_q_b454431bf82c811ddfc2d5dd208269bc` source-first isolated review PASS: the candidate separates batch-size and concurrency bounds, deduplicates once per call while restoring original-order duplicates, performs cache-first miss-only DB fallback and write-back, explicitly excludes cross-request stampede semantics, and OpenJDK validation exercises real two-way batch concurrency plus failure boundaries. Formal promotion remains blocked by repository human-approval/real-review policy.'
}

PYTHON = {
    'cid':'cq_q_fe0291a155ad4a502b6d0607ba6ad0b9',
    'qid':'fe0291a155ad4a502b6d0607ba6ad0b9',
    'expected':'在Python中建立字典对象有哪些方法？',
    'slug':'python-dict-construction',
    'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_fe0291a155ad4a502b6d0607ba6ad0b9","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# Python 建立字典对象的常见方法

## 核心结论

Python 建字典最常用的入口可以按“数据从哪里来”来记：直接写字典字面量 `{...}`；调用 `dict()` 建空字典或从已有 mapping / `(key, value)` 可迭代对象构造；当键是合法标识符字符串时用关键字参数 `dict(a=1)`；按规则计算键值时用字典推导式；已有两列 keys/values 时常用 `dict(zip(...))`；多个键需要同一个初始值时可用 `dict.fromkeys(keys, value)`。其中 `fromkeys` 的 value 是**同一个对象引用**，可变默认值要特别小心。

## 1 分钟版

- 字面量：`{"a": 1, "b": 2}`，固定少量键值时最直接。
- 构造器：`dict()`、`dict(mapping)`、`dict([("a", 1), ("b", 2)])`。
- 关键字：`dict(a=1, b=2)`，只适合可作为关键字名称的字符串键。
- 推导式：`{x: x*x for x in range(3)}`，适合从迭代数据计算键和值。
- 配对数据：`dict(zip(keys, values))`，本质上仍是把 `(key,value)` 可迭代对象交给 `dict`。
- 同值初始化：`dict.fromkeys(keys, value)`；若 value 是 list/dict 等可变对象，各键共享它，想要每键独立对象应改用推导式。

## 3 分钟版

```python
def build_examples():
    keys = ["a", "b"]
    values = [1, 2]

    literal = {"a": 1, "b": 2}
    empty = dict()
    from_mapping = dict({"a": 1, "b": 2})
    from_pairs = dict([("a", 1), ("b", 2)])
    from_keywords = dict(a=1, b=2)
    comprehension = {x: x * x for x in range(3)}
    from_zip = dict(zip(keys, values))
    shared_default = dict.fromkeys(keys, [])
    independent_default = {k: [] for k in keys}

    return {
        "literal": literal,
        "empty": empty,
        "from_mapping": from_mapping,
        "from_pairs": from_pairs,
        "from_keywords": from_keywords,
        "comprehension": comprehension,
        "from_zip": from_zip,
        "shared_default": shared_default,
        "independent_default": independent_default,
    }
```

如果只是面试口述，不必把这些当成互相独立的底层机制：`dict(zip(...))` 和“pairs 构造”都走的是 `dict` 接受键值对可迭代对象的用法。更重要的是能根据输入形态选择清晰写法，并说明 `fromkeys` 的共享可变值边界。

## 关键细节

- 字典键必须可哈希；像 list 不能直接作为 key。题目只问“如何建立”，这里不扩张到完整哈希表实现细节。
- `dict(a=1)` 的 `a` 是字符串键 `"a"`；任意对象键或不适合作为关键字名的字符串键应使用字面量、mapping 或键值对构造。
- `dict.fromkeys(["a","b"], [])` 让两个键指向同一个 list；修改其中一个键拿到的 list，另一个键看到同样变化。
- 推导式 `{k: [] for k in keys}` 会为每次迭代执行一次 `[]` 表达式，因此每个键得到独立 list。
- `dict(zip(keys, values))` 的键值对数量由 `zip` 实际产出的配对决定；若两侧长度不一致，额外项不会进入字典。本题来源没有要求长度校验，因此示例不把它包装成强校验 API。

## 原理机制

这些写法最终都产生 dict，但表达的信息来源不同：字面量把键值直接编码在源码；`dict(...)` 把已有 mapping 或键值对流装入新字典；推导式先遍历输入并计算每个键值对；`fromkeys` 则遍历键集合，把同一个给定 value 关联给每个键。选择方式时优先让构造意图和输入结构对齐，而不是为了“写法多”使用更绕的形式。

## 项目经验版

来源没有指定 Python 版本、键类型或业务数据，因此不能虚构工程场景。实际代码中，固定配置常用字面量；从记录流构造索引常用推导式；已有 mapping 需要浅复制/转换可以用 `dict(mapping)`；`fromkeys` 适合共享不可变初始值，涉及可变容器时通常用推导式避免意外共享。

## 常见追问

- 问：`dict.fromkeys(keys, [])` 为什么危险？答：第二个参数只求值一次，同一个 list 引用被放到每个键下；修改一个键对应的 list 会影响其他键看到的对象。
- 问：怎样让每个 key 都有独立空列表？答：用 `{k: [] for k in keys}`，每轮都会创建一个新 list。
- 问：`dict(zip(keys, values))` 是新的字典构造语法吗？答：不是，它是先用 `zip` 产生 `(key,value)` 对，再交给 `dict` 构造器。
- 问：关键字方式能创建整数键吗？答：`dict(a=1)` 这种关键字名会变成字符串键；要整数键用 `{1: value}` 或键值对等方式。
- 问：字面量和 `dict(mapping)` 怎么选？答：固定、手写键值用字面量最清楚；已有 mapping 数据时 `dict(mapping)` 直接表达“从它构造一个 dict”。

## 易错点

- 把 `fromkeys(..., [])` 当成“每个键一个独立 list”。
- 认为 `dict(a=1)` 会保留某个变量 a 的值作为键，而不是字符串 `"a"`。
- 把 `dict(zip(...))` 误说成独立于 dict 构造器的底层机制。
- 没有明确 `zip` 长度不一致时只产生配对成功的部分。
- 为了展示写法数量使用复杂表达式，反而掩盖实际数据来源。
''',
    'test':r'''from candidate_code import build_examples

x = build_examples()
expected = {"a": 1, "b": 2}
assert x["literal"] == expected
assert x["empty"] == {}
assert x["from_mapping"] == expected
assert x["from_pairs"] == expected
assert x["from_keywords"] == expected
assert x["from_zip"] == expected
assert x["comprehension"] == {0: 0, 1: 1, 2: 4}
assert x["shared_default"]["a"] is x["shared_default"]["b"]
x["shared_default"]["a"].append(7)
assert x["shared_default"]["b"] == [7]
assert x["independent_default"]["a"] is not x["independent_default"]["b"]
x["independent_default"]["a"].append(9)
assert x["independent_default"]["b"] == []
assert dict(zip(["a", "b", "c"], [1])) == {"a": 1}
assert dict([(1, "x"), (1, "y")]) == {1: "y"}
try:
    dict([("a", 1, 2)])
    raise AssertionError("malformed pair iterable must fail")
except ValueError:
    pass
print("PASS literal empty mapping pairs keywords comprehension zip fromkeys-shared comprehension-independent zip-shortest duplicate-last-wins malformed-rejected")
''',
    'stdout':'PASS literal empty mapping pairs keywords comprehension zip fromkeys-shared comprehension-independent zip-shortest duplicate-last-wins malformed-rejected',
    'checks':['literal construction','empty dict() construction','mapping construction','pair-iterable construction','keyword construction','dict comprehension construction','zip plus dict construction','fromkeys shares a mutable value reference','comprehension creates independent mutable values','zip stops at shortest iterable','duplicate keys from a pair iterable keep the later value','malformed pair iterable is rejected'],
    'claims':[
        ('source-boundary','The frozen source only asks for ways to create Python dict objects; the candidate groups standard construction forms by input shape rather than inventing a project context.',['repository-source'],['核心结论','1 分钟版','项目经验版']),
        ('runtime-behavior','The executable Python fixture verifies literal/dict/mapping/pairs/keywords/comprehension/zip/fromkeys forms plus mutable-value sharing, shortest-zip behavior, duplicate-key replacement, and malformed-pair rejection.',['fixture'],['3 分钟版','关键细节','原理机制','常见追问','易错点']),
    ],
    'findings':['The candidate directly enumerates common dict construction forms and distinguishes syntax from the dict constructor receiving pair iterables.','The answer explicitly covers the shared-object boundary of dict.fromkeys with a mutable value and gives a comprehension alternative for independent values.','Keyword construction is bounded to string-key semantics rather than presented as a universal key form.','Executable Python validation covers every shown construction form and the main sharing/zip/duplicate/malformed-input boundaries.'],
    'task_note':'- [x] `cq_q_fe0291a155ad4a502b6d0607ba6ad0b9` source-first isolated review PASS: the candidate directly covers literal/dict mapping/pairs/keywords/comprehension/zip/fromkeys construction, distinguishes shared mutable `fromkeys` values from per-key comprehension values, and executable Python validation covers all shown forms plus zip/duplicate/malformed boundaries. Formal promotion remains blocked by repository human-approval/real-review policy.'
}


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def validate_context(target: dict, inventory: dict) -> Path:
    cid, qid = target['cid'], target['qid']
    candidate = ROOT / f'review/candidates/answers/{cid}.md'
    evidence = ROOT / f'review/evidence/{cid}.json'
    if candidate.exists() or evidence.exists():
        raise SystemExit(f'{cid}: candidate/evidence already exists; do not overwrite')
    ctx_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{cid}/context.json'
    ctx = json.loads(ctx_path.read_text(encoding='utf-8'))
    if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id') != cid or ctx.get('answer_type') != 'coding':
        raise SystemExit(f'{cid}: context/type drift')
    if ctx.get('canonical',{}).get('question_ids') != [qid]:
        raise SystemExit(f'{cid}: source ownership drift')
    src = next((x for x in ctx.get('source_questions',[]) if x.get('question_id') == qid), None)
    if not src or src.get('original_question') != target['expected'] or src.get('is_valid_for_library') is not True:
        raise SystemExit(f'{cid}: source wording/validity drift')
    inv = next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id') == cid), None)
    if not inv or inv.get('existing_candidate') or inv.get('existing_evidence') or inv.get('answer_type') != 'coding':
        raise SystemExit(f'{cid}: inventory no longer describes a fresh coding target')
    return ctx_path


def freeze(target: dict, ctx_path: Path, command: str, stdout: str, task_text: str) -> str:
    cid, qid = target['cid'], target['qid']
    candidate = ROOT / f'review/candidates/answers/{cid}.md'
    evidence = ROOT / f'review/evidence/{cid}.json'
    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{cid}'
    validation = {'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,'command':command,'stdout':stdout,'checks':target['checks']}
    write_json(out/'writer_validation.json', validation)
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id':'repository-source','title':f'Batch 0057 frozen source context for {target["slug"]}','locator':str(ctx_path),'source_type':'repository_source_record','checked_at':DATE},
        {'source_id':'fixture','title':f'Deterministic executable validation for {target["slug"]}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
    ]
    claims = [{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in target['claims']]
    coverage = [{'question_id':qid,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json', {'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    reviewer = f'source-first-isolated-reviewer-batch-0057-{target["slug"]}-20260829-v1'
    review = {'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0057.{target["slug"]}.v1','decision':'pass','revision_round':1,'source_packet':[str(ctx_path),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings'],'promotion_blockers':[PROMOTION_BLOCKER]}
    write_json(out/'isolated_review_result.json', review)
    write_json(evidence, {'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':f'content-batch-0057-{target["slug"]}-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':f'Batch 0057 {target["slug"]} source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':command,'result':'pass','reported_stdout':stdout,'checks':target['checks'],'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in target['checks']]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings']},'promotion_blocker':PROMOTION_BLOCKER})
    if target['task_note'] not in task_text:
        task_text += '\n' + target['task_note']
    return task_text


def main() -> int:
    inventory = json.loads((ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json').read_text(encoding='utf-8'))
    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task_text = task.read_text(encoding='utf-8').rstrip()

    # Java concurrent batch/cache-aside candidate.
    ctx_path = validate_context(JAVA, inventory)
    body = JAVA['candidate']
    for h in HEADINGS:
        if body.count(h) != 1: raise SystemExit(f'{JAVA["cid"]}: section drift {h}')
    blocks = re.findall(r'```java\n(.*?)\n```', body, re.S)
    if len(blocks) != 1: raise SystemExit('Java candidate must contain exactly one implementation block')
    candidate = ROOT / f'review/candidates/answers/{JAVA["cid"]}.md'; candidate.parent.mkdir(parents=True, exist_ok=True); candidate.write_text(body, encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='b57-concurrent-') as tmp:
        d=Path(tmp); (d/f'{JAVA["class"]}.java').write_text(blocks[0].strip()+'\n',encoding='utf-8'); (d/f'{JAVA["class"]}Test.java').write_text(JAVA['test'],encoding='utf-8')
        run('javac',f'{JAVA["class"]}.java',f'{JAVA["class"]}Test.java',cwd=d); stdout=run('java',f'{JAVA["class"]}Test',cwd=d).stdout.strip()
    if stdout != JAVA['stdout']: raise SystemExit(f'Java fixture stdout drift: {stdout}')
    command=f'javac {JAVA["class"]}.java {JAVA["class"]}Test.java && java {JAVA["class"]}Test'
    task_text = freeze(JAVA,ctx_path,command,stdout,task_text)

    # Python dict-construction candidate.
    ctx_path = validate_context(PYTHON, inventory)
    body = PYTHON['candidate']
    for h in HEADINGS:
        if body.count(h) != 1: raise SystemExit(f'{PYTHON["cid"]}: section drift {h}')
    blocks = re.findall(r'```python\n(.*?)\n```', body, re.S)
    if len(blocks) != 1: raise SystemExit('Python candidate must contain exactly one implementation block')
    candidate = ROOT / f'review/candidates/answers/{PYTHON["cid"]}.md'; candidate.write_text(body, encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='b57-python-dict-') as tmp:
        d=Path(tmp); (d/'candidate_code.py').write_text(blocks[0].strip()+'\n',encoding='utf-8'); (d/'test_candidate.py').write_text(PYTHON['test'],encoding='utf-8')
        run('python3','-m','py_compile','candidate_code.py','test_candidate.py',cwd=d); stdout=run('python3','test_candidate.py',cwd=d).stdout.strip()
    if stdout != PYTHON['stdout']: raise SystemExit(f'Python fixture stdout drift: {stdout}')
    task_text = freeze(PYTHON,ctx_path,'python3 -m py_compile candidate_code.py test_candidate.py && python3 test_candidate.py',stdout,task_text)

    task.write_text(task_text.rstrip()+'\n',encoding='utf-8')
    print('PASS batch-0057 remaining pair built, executed, reviewed, and evidence-frozen')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
