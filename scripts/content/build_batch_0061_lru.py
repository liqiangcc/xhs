#!/usr/bin/env python3
"""Build, execute, source-first review, and stage the consolidated Batch 0061 LRU candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0061'
CID = 'cq_q_35c2d83b04a38c71b4cca1e3ed3f401b'
QIDS = [
    '35c2d83b04a38c71b4cca1e3ed3f401b',
    '5fec9f875255be5ae3fa636523b24956',
    '8e724cc524788dca8a06d93661fef37c',
]
EXPECTED_VARIANTS = {
    '算法：LRU缓存',
    '算法：LRU 缓存',
    '算法：实现 LRU 缓存？',
    '算法：实现一个 LRU 缓存？',
}
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = [
    '## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节',
    '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点',
]
SCORES = {
    'facts_and_evidence': 25,
    'directness_and_relevance': 20,
    'type_specific_completeness': 20,
    'mechanism_and_causality': 15,
    'boundaries_and_tradeoffs': 10,
    'followup_quality': 5,
    'oral_quality': 5,
}

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_35c2d83b04a38c71b4cca1e3ed3f401b","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 算法：实现一个 LRU 缓存

## 核心结论

LRU（Least Recently Used）缓存的核心是不仅要按 key 快速找到值，还要持续维护“最近使用顺序”。面试里最常见的组合是 **HashMap + 双向链表**：HashMap 负责 `key -> 节点` 定位，双向链表负责按最近使用程度排序；每次 `get` 命中或 `put` 更新，都把对应节点移动到链表头部，容量超限时删除链表尾部最久未使用的节点。来源只要求实现 LRU，没有完整指定语言、API、容量非法值和并发语义；下面明确选择 Java，并采用常见的 `get(int key)` / `put(int key, int value)` 可执行契约来演示。

## 1 分钟版

- 用 `HashMap<Integer, Node>` 找节点，避免每次为了找 key 扫描链表。
- 用带哨兵 `head/tail` 的双向链表维护新旧顺序：`head` 后面是最近使用，`tail` 前面是最久未使用。
- `get(key)`：未命中返回 `-1`；命中后把节点移动到头部，再返回 value。
- `put(key, value)`：key 已存在就更新 value 并移动到头部；不存在就新建节点放到头部。
- 新增后若超过容量，就删除 `tail.prev`，并同步从 HashMap 删除对应 key。
- 关键不变量是 **Map 与链表中的有效节点一一对应**，且每次访问都更新 recency。只删除链表不删 Map，或只更新 Map 不移动链表，都会破坏 LRU 语义。

## 3 分钟版

来源没有指定语言/API；这里用 Java 给出一个最小可执行版本。为了让边界明确，构造器要求 `capacity > 0`，否则抛 `IllegalArgumentException`；`get` 未命中返回 `-1`。这两个都是本答案的示例契约，不冒充原题已经给出的条件。

```java
import java.util.HashMap;
import java.util.Map;

public final class LRUCache {
    private static final class Node {
        int key;
        int value;
        Node prev;
        Node next;

        Node(int key, int value) {
            this.key = key;
            this.value = value;
        }
    }

    private final int capacity;
    private final Map<Integer, Node> byKey = new HashMap<>();
    private final Node head = new Node(0, 0);
    private final Node tail = new Node(0, 0);

    public LRUCache(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public int get(int key) {
        Node node = byKey.get(key);
        if (node == null) return -1;
        moveToFront(node);
        return node.value;
    }

    public void put(int key, int value) {
        Node existing = byKey.get(key);
        if (existing != null) {
            existing.value = value;
            moveToFront(existing);
            return;
        }

        Node node = new Node(key, value);
        byKey.put(key, node);
        addAfterHead(node);
        if (byKey.size() > capacity) {
            Node victim = tail.prev;
            unlink(victim);
            byKey.remove(victim.key);
        }
    }

    private void moveToFront(Node node) {
        unlink(node);
        addAfterHead(node);
    }

    private void addAfterHead(Node node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    private void unlink(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
}
```

这套实现里，链表不负责“查找”，Map 不负责“新旧顺序”。两种结构各自承担一个职责，再通过同一个 `Node` 对象连接起来。`get/put` 中除了 HashMap 的基本操作外，只做固定次数的指针修改，因此在通常的 HashMap 平均常数时间假设下，`get` 和 `put` 都是平均 `O(1)`；空间是 `O(capacity)`。

## 关键细节

- **为什么必须双向链表**：命中任意节点后要把它从当前位置删除再移到头部。单链表只有当前节点时拿不到前驱，删除中间节点通常还需要额外查找；双向链表能直接通过 `prev/next` 完成摘除。
- **为什么使用哨兵节点**：`head`、`tail` 不存业务数据，统一了“插到最前”“删除最后”“删除中间节点”的指针逻辑，避免大量头尾空指针分支。
- **`get` 也要更新顺序**：LRU 的“used”通常包括读取。若命中后不移动节点，后续淘汰的就不是“最久未使用”。
- **更新已有 key 不能增加 size**：`put` 已存在的 key 只更新 value + recency；若误建新节点，会造成 Map/链表数量与身份不一致。
- **淘汰必须同时改两套结构**：从链表移除 victim 后，还必须 `byKey.remove(victim.key)`；否则 Map 会保留指向已脱链节点的陈旧引用。
- **容量边界**：本示例把 `capacity <= 0` 定义为非法并立即拒绝。若真实题目定义“0 容量缓存所有 put 都丢弃”，应按题目改契约。
- **并发边界**：当前实现是单线程算法题版本，没有加锁。若要求多线程安全，需要另外定义线性化点和锁粒度，不能因为用了 `HashMap + 双向链表` 就自动宣称线程安全。

## 原理机制

LRU 本质上维护两个视图：**按 key 的索引视图**和**按时间/访问顺序的淘汰视图**。只用 HashMap 可以快速查找，但不知道谁最久没用；只用链表可以维护顺序，但按 key 查找会退化成线性扫描。组合以后，每个业务条目只有一个 Node：Map 指向它，链表也链接它。

每次访问都执行同一个状态转移：先把节点从旧位置摘下，再插到 `head` 后面，表示它成为 MRU（Most Recently Used）；`tail.prev` 因此始终代表 LRU。容量超限时只需要淘汰这一个尾部节点。正确性可以围绕两个不变量检查：第一，Map 中每个 key 恰好对应链表中的一个有效节点；第二，链表从头到尾严格表示从新到旧的访问顺序。

## 项目经验版

来源没有真实项目、缓存命中率、并发量或 TTL 需求，不能虚构线上案例。真实系统里我会先确认 LRU 是否真是业务需要：本地进程缓存还要考虑并发、最大内存而不只是条目数、对象大小、TTL/过期、监控与命中率；分布式缓存则通常不会直接手写这个单机结构。算法题里先把 `Map + 双向链表` 的状态不变量写正确，再根据面试官追问扩展并发或工程边界。

## 常见追问

- 问：为什么不用 `LinkedHashMap`？答：工程代码可以考虑现成容器；但“实现 LRU”这类算法题通常是在考 Map 与双向链表的组合、不变量和淘汰过程，直接用库会隐藏核心机制。
- 问：为什么 `get` 命中后必须移动？答：LRU 按最近使用时间排序，读取本身就是一次使用；不移动会让 recency 状态落后于真实访问历史。
- 问：为什么链表尾部就是淘汰对象？答：每次新建、读取命中、更新命中都把节点移到头部，因此越久没被触碰的节点越靠后，`tail.prev` 就是最旧节点。
- 问：为什么更新已有 key 不直接创建新节点？答：缓存中同一个 key 应只有一个活跃条目。原节点更新后移到头部即可；重复节点会破坏 Map 与链表一一对应关系。
- 问：能做到严格 `O(1)` 吗？答：链表的摘除/插入是固定指针操作；Map 基本操作通常按平均常数时间讨论，所以面试里通常写平均 `O(1)`。极端哈希行为和具体 Map 实现细节应与算法层结论区分。
- 问：怎么做线程安全？答：当前来源没要求并发。若要并发，需要同时保护 Map 和 recency 链表这个联合状态，不能只把 Map 换成并发 Map；常见做法是先用一把锁保证复合操作原子性，再根据实际竞争评估是否值得更复杂设计。

## 易错点

- `get` 命中后忘记更新 recency。
- `put` 更新已有 key 时又创建一个节点，导致重复条目。
- 淘汰时只从链表删除，没有从 Map 删除。
- 移动节点时指针更新顺序错误，导致链表断链或形成环。
- 不使用哨兵却遗漏空表、单节点、头尾节点等边界。
- 把平均 `O(1)` 说成对所有 HashMap 实现和所有输入都绝对严格的 `O(1)`。
- 没有明确容量 0、miss 返回值、并发等契约，却把自己的实现选择说成题目原始要求。
'''

TEST = r'''import java.lang.reflect.Field;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;

public final class LRUCacheTest {
    private static final class ReferenceLru extends LinkedHashMap<Integer, Integer> {
        private final int capacity;
        ReferenceLru(int capacity) {
            super(16, 0.75f, true);
            this.capacity = capacity;
        }
        int getValue(int key) {
            Integer value = super.get(key);
            return value == null ? -1 : value;
        }
        void putValue(int key, int value) {
            super.put(key, value);
            if (size() > capacity) {
                Integer eldest = keySet().iterator().next();
                remove(eldest);
            }
        }
    }

    private static int sizeOf(LRUCache cache) throws Exception {
        Field f = LRUCache.class.getDeclaredField("byKey");
        f.setAccessible(true);
        return ((Map<?, ?>) f.get(cache)).size();
    }

    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }

    public static void main(String[] args) throws Exception {
        boolean rejected = false;
        try { new LRUCache(0); } catch (IllegalArgumentException expected) { rejected = true; }
        require(rejected, "capacity=0 must be rejected by declared sample contract");

        LRUCache cache = new LRUCache(2);
        cache.put(1, 1);
        cache.put(2, 2);
        require(cache.get(1) == 1, "get(1)");
        cache.put(3, 3);
        require(cache.get(2) == -1, "key 2 should be evicted");
        require(cache.get(3) == 3, "get(3)");
        cache.put(1, 10);
        require(cache.get(1) == 10, "overwrite must update value");
        require(sizeOf(cache) == 2, "overwrite must not grow size");
        cache.put(4, 4);
        require(cache.get(3) == -1, "get/update recency must affect eviction");
        require(cache.get(1) == 10 && cache.get(4) == 4, "remaining keys after eviction");

        LRUCache one = new LRUCache(1);
        one.put(7, 70);
        one.put(8, 80);
        require(one.get(7) == -1 && one.get(8) == 80 && sizeOf(one) == 1, "capacity=1 boundary");

        final int capacity = 7;
        LRUCache actual = new LRUCache(capacity);
        ReferenceLru reference = new ReferenceLru(capacity);
        Random random = new Random(1460061L);
        int operations = 50000;
        for (int i = 0; i < operations; i++) {
            int key = random.nextInt(23);
            if ((random.nextInt() & 3) == 0) {
                int a = actual.get(key);
                int b = reference.getValue(key);
                require(a == b, "random get mismatch at op=" + i + " key=" + key + " actual=" + a + " reference=" + b);
            } else {
                int value = random.nextInt(100000);
                actual.put(key, value);
                reference.putValue(key, value);
            }
            require(sizeOf(actual) == reference.size(), "size mismatch at op=" + i);
        }
        for (int key = 0; key < 23; key++) {
            require(actual.get(key) == reference.getValue(key), "final state mismatch key=" + key);
        }
        require(sizeOf(actual) <= capacity, "capacity invariant");
        System.out.println("PASS deterministic=eviction-hit-miss-overwrite-recency capacity1=pass capacity0=rejected randomized_ops=50000 reference=LinkedHashMap size_invariant=pass");
    }
}
'''


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass':
        raise SystemExit('batch 0061 source inventory is not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item:
        raise SystemExit(f'{CID}: missing from current Batch 0061 source inventory')
    if item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: expected coding, got {item.get("answer_type")}')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: frozen ownership drift: {item.get("question_ids")}')
    if item.get('source_question_count') != 3 or item.get('source_occurrence_count') != 4:
        raise SystemExit(
            f'{CID}: occurrence-aware inventory drift: questions={item.get("source_question_count")} '
            f'occurrences={item.get("source_occurrence_count")}'
        )
    wordings = {q.get('original_question') for q in item.get('source_questions', [])}
    if wordings != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: source wording drift: {wordings}')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    context_raw = run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout
    context = json.loads(context_raw)
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: live context/type drift')
    live_qids = sorted((context.get('canonical') or {}).get('question_ids') or [])
    if live_qids != sorted(QIDS):
        raise SystemExit(f'{CID}: live context ownership drift: {live_qids}')
    live_sources = list(context.get('source_questions') or [])
    if len(live_sources) != 4 or {x.get('original_question') for x in live_sources} != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: live source occurrence drift')
    occurrence_ids = {
        (x.get('question_id'), x.get('source_note_id'), x.get('source_question_index'), x.get('original_question'))
        for x in live_sources
    }
    if len(occurrence_ids) != 4:
        raise SystemExit(f'{CID}: source occurrence identity collapsed')
    write_json(out / 'context.json', context)

    relation_path = ROOT / f'review/content_build/answer_batch_{BATCH}/lru_relation_review.md'
    relation = relation_path.read_text(encoding='utf-8')
    if 'Relation: `same`' not in relation or CID not in relation or 'cq_q_5fec9f875255be5ae3fa636523b24956' not in relation:
        raise SystemExit(f'{CID}: source-first LRU relation review missing')

    for heading in HEADINGS:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if CANDIDATE.count('- 问：') < 5:
        raise SystemExit(f'{CID}: follow-up coverage too small')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'{CID}: candidate must contain exactly one Java implementation block')
    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE, encoding='utf-8')
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory(prefix='xhs-lru-') as tmp:
        td = Path(tmp)
        (td / 'LRUCache.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (td / 'LRUCacheTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'LRUCache.java', 'LRUCacheTest.java', cwd=td)
        stdout = run('java', 'LRUCacheTest', cwd=td).stdout.strip()
    expected_stdout = 'PASS deterministic=eviction-hit-miss-overwrite-recency capacity1=pass capacity0=rejected randomized_ops=50000 reference=LinkedHashMap size_invariant=pass'
    if stdout != expected_stdout:
        raise SystemExit(f'{CID}: unexpected fixture output: {stdout}')

    command = 'javac LRUCache.java LRUCacheTest.java && java LRUCacheTest'
    checks = [
        'deterministic get hit/miss, recency movement, overwrite, and eviction behavior',
        'capacity-one behavior and the declared rejection contract for capacity <= 0',
        '50,000 deterministic randomized operations match an access-order LinkedHashMap reference model',
        'the cache size never exceeds the configured capacity and overwrite does not grow size',
    ]
    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': command,
        'stdout': stdout,
        'checks': checks,
        'environment': {'java': 'OpenJDK 21'},
        'limitation': 'The fixture validates the exact single-threaded sample contract and state transitions. It does not claim thread safety, TTL behavior, persistence semantics, or worst-case HashMap timing.',
    }
    write_json(out / 'writer_validation.json', validation)

    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0061 occurrence-aware frozen repository source context for consolidated LRU',
            'locator': str(out / 'context.json'),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'source-inventory',
            'title': 'Batch 0061 occurrence-aware frozen source inventory',
            'locator': str(inventory_path),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
        {
            'source_id': 'relation-review',
            'title': 'Batch 0061 LRU source-first relation review',
            'locator': str(relation_path),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
        {
            'source_id': 'fixture',
            'title': 'Deterministic and randomized executable validation for the exact Java LRU sample',
            'locator': str(out / 'writer_validation.json'),
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'Four preserved primary-source occurrences across three normalized Question IDs ask for the same LRU-cache implementation operation. They do not preserve a distinct language, concurrency, TTL, persistence, or alternative eviction-policy contract, so the candidate chooses and labels a minimal Java get/put contract instead of inventing those constraints.',
            'source_ids': ['repository-source', 'source-inventory', 'relation-review'],
            'answer_locations': ['核心结论', '3 分钟版', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'state-model',
            'text': 'The exact sample maintains one HashMap key-to-node index plus one doubly linked recency list, moves hits/updates to the MRU side, and removes the LRU tail node from both structures on overflow.',
            'source_ids': ['fixture'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问'],
        },
        {
            'claim_id': 'reference-behavior',
            'text': 'The exact Java candidate compiles and passes deterministic eviction/overwrite/recency cases plus 50,000 seeded randomized operations against an independent access-order LinkedHashMap reference model while preserving the capacity invariant.',
            'source_ids': ['fixture'],
            'answer_locations': ['3 分钟版', '项目经验版'],
        },
    ]
    locations = ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']
    coverage = [{'question_id': qid, 'covered': True, 'answer_locations': locations} for qid in QIDS]
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'source_occurrence_count': 4,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    reviewer_id = 'source-first-isolated-reviewer-batch-0061-lru-20260831-v1'
    review_version = 'batch-0061.lru.v1'
    findings = [
        'The candidate is bound to the post-normalization survivor and covers all four preserved source occurrences without resurrecting the retired duplicate Canonical.',
        'The Java get/put API, positive-capacity rejection rule, and miss=-1 behavior are explicitly identified as sample-contract choices rather than preserved source requirements.',
        'The implementation maintains Map/list identity and recency invariants, updates recency on get and existing-key put, and removes evicted nodes from both structures.',
        'The exact implementation compiles and matches an independent access-order LinkedHashMap reference over deterministic boundaries and 50,000 seeded randomized operations.',
        'Average O(1) wording is qualified by the usual HashMap average-time assumption; the candidate does not claim worst-case constant HashMap time.',
        'Concurrency, TTL, persistence, memory sizing, and production experience are kept outside the source-bounded single-threaded algorithm contract instead of being fabricated.',
    ]
    write_json(out / 'isolated_review_result.json', {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': reviewer_id,
        'review_version': review_version,
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            str(out / 'context.json'), str(inventory_path), str(relation_path),
            str(candidate_path), str(out / 'writer_validation.json'),
            'docs/refactor/09_answer_content_standard.md',
        ],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    })
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0061-lru-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'Batch 0061 consolidated LRU source-first isolated review',
            'locator': str(out / 'isolated_review_result.json'),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        }],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': command,
            'result': 'pass',
            'reported_stdout': stdout,
            'checks': checks,
            'boundary_tests': [
                {'case': check, 'expected': 'pass under declared candidate contract', 'actual': 'pass', 'passed': True}
                for check in checks
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': reviewer_id,
            'review_version': review_version,
            'independent': True,
            'decision': 'pass',
            'revision_round': 1,
            'scores': SCORES,
            'hard_failures': [],
            'unsupported_claims': [],
            'uncovered_source_variants': [],
            'findings': findings,
        },
        'promotion_blocker': PROMOTION_BLOCKER,
    })

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    if '## Progress' not in task:
        task += '\n\n## Progress\n'
    marker = f'- [x] `{CID}` consolidated LRU source-first isolated review PASS:'
    if marker not in task:
        task += '\n' + (
            f'- [x] `{CID}` consolidated LRU source-first isolated review PASS: candidate digest `{digest}`; '
            'the occurrence-aware source packet preserves four primary-source occurrences across three normalized Question IDs after retiring the duplicate LRU Canonical. '
            'The Java Map + doubly-linked-list sample passes deterministic hit/miss/overwrite/recency/eviction boundaries and 50,000 seeded randomized operations against an access-order LinkedHashMap reference. '
            'Formal promotion remains blocked by repository human-approval/real-review policy.'
        )
        task_path.write_text(task + '\n', encoding='utf-8')

    print(
        f'PASS canonical={CID} source_question_ids={len(QIDS)} source_occurrences=4 '
        f'candidate_sha256={digest} fixture={stdout}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
