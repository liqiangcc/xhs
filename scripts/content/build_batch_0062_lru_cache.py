#!/usr/bin/env python3
"""Build and validate the source-bounded Batch 0062 LRU cache candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_9e1c6fe7d0d269300c71151cd8c24a81'
QIDS = ['9e1c6fe7d0d269300c71151cd8c24a81', 'b383dbafe3f6bd7d86fee7a8283bef19']
EXPECTED_VARIANTS = {
    '算法：LRU 缓存淘汰算法',
    '算法：LRU 缓存淘汰算法实现 (LRU Cache)',
}
EXPECTED_STDOUT = 'PASS fixed=14 random_ops=50000 oracle=LinkedHashMap capacity1=pass update_recency=pass miss=null'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_9e1c6fe7d0d269300c71151cd8c24a81","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# LRU 缓存淘汰算法：HashMap + 双向链表

## 核心结论

两条来源都只要求“LRU 缓存淘汰算法 / LRU Cache 实现”，没有固定语言、API、容量为 0 时的行为或 miss 返回值。这里声明一个可执行 Java 契约：构造函数要求 `capacity > 0`；`get(int key)` 命中时返回 `Integer` 并把该 key 提升为最近使用，未命中返回 `null`；`put(int key, int value)` 插入或更新并提升为最近使用；超过容量时淘汰最久未使用项。实现采用 `HashMap<Integer, Node>` 做 key 到节点定位，再用带头尾哨兵的双向链表维护“最近使用 → 最久未使用”顺序，常见情况下 `get/put` 都是期望 `O(1)`，空间 `O(capacity)`。

## 1 分钟版

- LRU 的核心不是“删除最早插入的”，而是删除**最长时间没有被访问或更新**的项。
- `HashMap` 负责按 key 快速找到节点；双向链表负责维护使用顺序。
- 约定链表头部是 MRU（最近使用），尾部是 LRU（最久未使用）。
- `get` 命中后要把节点移动到头部；`put` 更新已有 key 时也要移动到头部。
- 插入新 key 后若 `size > capacity`，删除尾哨兵前一个真实节点，并同步从 `HashMap` 删除。
- 用双向链表是因为已知节点后可以 `O(1)` 摘除；单链表若只有当前节点，通常还需要寻找前驱。

## 3 分钟版

下面给出完整、可编译的 Java 实现。来源没有规定 miss 语义，所以这里明确用 `null`，避免把 `-1` 与合法 value 混在一起：

```java
import java.util.HashMap;
import java.util.Map;

public final class LRUCache {
    private static final class Node {
        final int key;
        int value;
        Node prev;
        Node next;
        Node(int key, int value) {
            this.key = key;
            this.value = value;
        }
    }

    private final int capacity;
    private final Map<Integer, Node> index = new HashMap<>();
    private final Node head = new Node(0, 0);
    private final Node tail = new Node(0, 0);

    public LRUCache(int capacity) {
        if (capacity <= 0) {
            throw new IllegalArgumentException("capacity must be positive");
        }
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public Integer get(int key) {
        Node node = index.get(key);
        if (node == null) return null;
        moveToFront(node);
        return node.value;
    }

    public void put(int key, int value) {
        Node node = index.get(key);
        if (node != null) {
            node.value = value;
            moveToFront(node);
            return;
        }

        Node created = new Node(key, value);
        index.put(key, created);
        addAfterHead(created);
        if (index.size() > capacity) {
            Node victim = tail.prev;
            remove(victim);
            index.remove(victim.key);
        }
    }

    public int size() {
        return index.size();
    }

    private void moveToFront(Node node) {
        remove(node);
        addAfterHead(node);
    }

    private void addAfterHead(Node node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    private static void remove(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
}
```

以容量 2 为例：`put(1)`、`put(2)` 后顺序可以看成 `[2, 1]`；`get(1)` 后变成 `[1, 2]`；再 `put(3)` 时应该淘汰 `2`，因为 `2` 才是此刻最久未使用的节点。这个例子能直接区分 LRU 和 FIFO。

## 关键细节

- **命中也会改变顺序**：如果 `get` 只返回值而不移动节点，最终淘汰的是“最早插入”而不是“最久未使用”。
- **更新已有 key 也算使用**：`put(existingKey, newValue)` 不增加 `size`，但要更新 value 并移动到 MRU。
- **Map 与链表必须原子保持一致**：淘汰节点时既要摘链表，也要删 `Map`；否则会留下幽灵节点或失效索引。
- **为什么用哨兵节点**：`head/tail` 让插入、删除首尾真实节点不需要大量空指针分支，链表不变量更容易维护。
- **容量边界**：本实现把 `capacity <= 0` 定义为调用错误并抛异常；这是本答案的显式契约，不是来源事实。
- **复杂度口径**：链表操作本身是 `O(1)`；`HashMap` 查找/写入通常按期望 `O(1)` 讨论，因此整体常见情况下 `get/put` 为期望 `O(1)`，不能把它表述成所有输入下绝对最坏 `O(1)`。

## 原理机制

LRU 需要同时解决两个维度：一是“按 key 定位”，二是“按最近使用时间排序”。只用 `HashMap` 没有顺序；只用链表按 key 查找又要线性扫描。把两者组合后，Map 指向链表节点，访问某个 key 时可以直接得到节点并在 `O(1)` 链接操作内把它移动到表头；容量超限时，表尾天然就是 LRU victim。

真正需要维护的是一个不变量：所有缓存项恰好各有一个 Map 条目和一个链表节点；从 `head.next` 到 `tail.prev` 的顺序是从 MRU 到 LRU。`get/put` 的每条路径都必须保持这个不变量，淘汰时也必须同时更新两个结构。

## 项目经验版

来源没有真实项目中的缓存容量、并发模型、过期策略或命中率数据，不能虚构“线上就是这样实现”。工程落地时还要明确并发访问、TTL、权重容量、淘汰回调、持久化和监控等需求。若多个线程共享这个结构，还需要额外同步；本答案只实现单线程算法契约，不把线程安全能力偷偷加入原题。

## 常见追问

- 问：为什么不能直接用一个 `HashMap`？答：Map 可以定位 key，但没有“谁最久未使用”的顺序信息，容量满时无法直接得到 victim。
- 问：为什么是双向链表？答：Map 已经拿到目标节点，双向链表可以直接利用 `prev/next` 在 `O(1)` 摘除；单链表通常缺少前驱。
- 问：`get` 为什么要移动节点？答：LRU 的“使用”包含读取命中；读取后该 key 应成为 MRU，否则淘汰顺序会退化成别的策略。
- 问：更新已有 key 会不会触发淘汰？答：不会增加元素数量，因此不会因为这次更新新增超容量；但它会更新 value 并刷新 recency。
- 问：Java 里能不能直接用 `LinkedHashMap`？答：可以利用 access-order 模式快速实现同一策略；面试手撕通常仍需要解释 Map + 双向链表的底层组合和不变量。
- 问：这个实现线程安全吗？答：不是。来源只要求算法实现；共享并发缓存需要额外同步或采用经过验证的并发缓存实现。

## 易错点

- 把 LRU 写成 FIFO，只在插入时维护顺序，读取命中不刷新。
- 更新已有 key 时错误地增加 `size` 或创建第二个链表节点。
- 淘汰时只删链表、不删 Map，或只删 Map、不摘链表。
- 删除首尾节点时空指针分支很多，却没有哨兵节点或统一的 `remove/add` 原语。
- 把 `HashMap` 的期望 `O(1)` 说成任何情况下严格最坏 `O(1)`。
- 没声明容量 0、miss 值、并发语义，却把某种实现选择冒充成原题约束。
'''

JAVA_IMPL = r'''import java.util.HashMap;
import java.util.Map;

public final class LRUCache {
    private static final class Node {
        final int key;
        int value;
        Node prev;
        Node next;
        Node(int key, int value) { this.key = key; this.value = value; }
    }

    private final int capacity;
    private final Map<Integer, Node> index = new HashMap<>();
    private final Node head = new Node(0, 0);
    private final Node tail = new Node(0, 0);

    public LRUCache(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public Integer get(int key) {
        Node node = index.get(key);
        if (node == null) return null;
        moveToFront(node);
        return node.value;
    }

    public void put(int key, int value) {
        Node node = index.get(key);
        if (node != null) {
            node.value = value;
            moveToFront(node);
            return;
        }
        Node created = new Node(key, value);
        index.put(key, created);
        addAfterHead(created);
        if (index.size() > capacity) {
            Node victim = tail.prev;
            remove(victim);
            index.remove(victim.key);
        }
    }

    public int size() { return index.size(); }

    private void moveToFront(Node node) {
        remove(node);
        addAfterHead(node);
    }

    private void addAfterHead(Node node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    private static void remove(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
}
'''

JAVA_TEST = r'''import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;

public final class LRUCacheWriterTest {
    private static final Random RNG = new Random(0x62009E1CL);

    private static final class Oracle extends LinkedHashMap<Integer, Integer> {
        private final int capacity;
        Oracle(int capacity) { super(16, 0.75f, true); this.capacity = capacity; }
        @Override protected boolean removeEldestEntry(Map.Entry<Integer, Integer> eldest) {
            return size() > capacity;
        }
    }

    private static void eq(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        boolean zero = false;
        try { new LRUCache(0); } catch (IllegalArgumentException expected) { zero = true; }
        if (!zero) throw new AssertionError("capacity=0 must be rejected");

        LRUCache c = new LRUCache(2);
        eq(null, c.get(99), "miss");
        c.put(1, 10); c.put(2, 20);
        eq(10, c.get(1), "get-refresh");
        c.put(3, 30);
        eq(null, c.get(2), "evict-lru-after-get");
        eq(10, c.get(1), "keep-refreshed");
        eq(30, c.get(3), "keep-new");
        c.put(1, 11);
        eq(11, c.get(1), "update-value");
        c.put(4, 40);
        eq(null, c.get(3), "update-refreshes-recency");
        eq(2, c.size(), "size-capacity");

        LRUCache one = new LRUCache(1);
        one.put(7, 70); eq(70, one.get(7), "capacity1-hit");
        one.put(8, 80); eq(null, one.get(7), "capacity1-evict"); eq(80, one.get(8), "capacity1-new");

        int operations = 0;
        for (int scenario = 0; scenario < 100; scenario++) {
            int capacity = 1 + RNG.nextInt(8);
            LRUCache actual = new LRUCache(capacity);
            Oracle oracle = new Oracle(capacity);
            for (int step = 0; step < 500; step++) {
                int key = RNG.nextInt(16);
                if (RNG.nextInt(100) < 55) {
                    int value = RNG.nextInt();
                    actual.put(key, value);
                    oracle.put(key, value);
                } else {
                    eq(oracle.get(key), actual.get(key), "random-get-" + scenario + '-' + step);
                }
                if (actual.size() != oracle.size()) {
                    throw new AssertionError("size drift scenario=" + scenario + " step=" + step);
                }
                operations++;
            }
            for (int key = 0; key < 16; key++) {
                eq(oracle.get(key), actual.get(key), "final-key-" + scenario + '-' + key);
            }
        }
        if (operations != 50000) throw new AssertionError("unexpected operation count " + operations);
        System.out.println("PASS fixed=14 random_ops=50000 oracle=LinkedHashMap capacity1=pass update_recency=pass miss=null");
    }
}
'''


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass':
        raise SystemExit('batch 0062 source inventory is not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item or item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: missing/non-coding inventory row')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: ownership drift')
    if {x.get('original_question') for x in item.get('source_questions', [])} != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: source wording drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}' / CID
    out.mkdir(parents=True, exist_ok=True)
    candidate_path = ROOT / 'review/candidates/answers' / f'{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE.rstrip() + '\n', encoding='utf-8')
    (out / 'LRUCache.java').write_text(JAVA_IMPL, encoding='utf-8')
    (out / 'LRUCacheWriterTest.java').write_text(JAVA_TEST, encoding='utf-8')

    subprocess.run(['javac', 'LRUCache.java', 'LRUCacheWriterTest.java'], cwd=out, check=True)
    proc = subprocess.run(['java', 'LRUCacheWriterTest'], cwd=out, check=True, text=True, capture_output=True)
    stdout = proc.stdout.strip()
    if stdout != EXPECTED_STDOUT:
        raise SystemExit(f'unexpected writer fixture stdout: {stdout!r}')
    for cls in out.glob('*.class'):
        cls.unlink()

    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    write_json(out / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'validator': 'batch_0062_lru_cache_writer_fixture',
        'command': 'javac LRUCache.java LRUCacheWriterTest.java && java LRUCacheWriterTest',
        'stdout': stdout,
        'checks': [
            'fixed LRU/FIFO-distinguishing access-order and update-recency boundaries',
            'capacity=1 and invalid non-positive capacity boundaries',
            '50,000 seeded random get/put operations match an independent access-order LinkedHashMap oracle',
        ],
    })
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'candidate_sha256': digest,
        'sources': [
            {
                'source_id': 'repository-source',
                'title': 'Batch 0062 frozen repository context for LRU cache',
                'locator': f'review/content_build/answer_batch_{BATCH}/{CID}/context.json',
                'source_type': 'repository_source_record',
                'checked_at': DATE,
            },
            {
                'source_id': 'writer-fixture',
                'title': 'LRU cache access-order differential validation',
                'locator': f'review/content_build/answer_batch_{BATCH}/{CID}/writer_validation.json',
                'source_type': 'executable_test_or_reproducible_experiment',
                'checked_at': DATE,
            },
        ],
        'claims': [
            {
                'claim_id': 'source-boundary',
                'text': 'Both frozen source variants ask for an LRU cache/eviction implementation; neither fixes the Java API, miss value, zero-capacity behavior, concurrency semantics, or concrete internal data structures.',
                'source_ids': ['repository-source'],
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节'],
            },
            {
                'claim_id': 'implementation-behavior',
                'text': 'Under the declared positive-capacity single-threaded Java contract, the HashMap plus doubly-linked-list implementation matches an independent access-order LinkedHashMap oracle across fixed boundaries and 50,000 seeded random operations.',
                'source_ids': ['writer-fixture'],
                'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问'],
            },
        ],
        'source_question_coverage': [
            {
                'question_id': qid,
                'covered': True,
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问'],
            }
            for qid in QIDS
        ],
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    task_path = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0062.md'
    task = task_path.read_text(encoding='utf-8')
    note = (
        f'- [x] `{CID}` writer stage complete: both frozen LRU source Questions are covered by an explicit positive-capacity single-threaded Java cache contract; '
        'the HashMap + doubly-linked-list implementation validates LRU-vs-FIFO access order, update recency, capacity-one behavior, and 50,000 seeded random operations against an independent access-order LinkedHashMap oracle. '
        'Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    )
    if note not in task:
        task_path.write_text(task.rstrip() + '\n' + note + '\n', encoding='utf-8')

    print(json.dumps({'ok': True, 'canonical_id': CID, 'candidate_sha256': digest, 'stdout': stdout}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
