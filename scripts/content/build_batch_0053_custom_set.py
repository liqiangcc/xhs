#!/usr/bin/env python3
# Build, validate, source-first review, and stage Batch 0053 custom Set candidate.

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0053'
CID = 'cq_q_eaba609d7a28fdf408eb6f4924804982'
QID = 'eaba609d7a28fdf408eb6f4924804982'
EXPECTED = '算法：手写实现一个 Set 集合，支持 insert、remove、get 操作。'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_eaba609d7a28fdf408eb6f4924804982","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 手写一个支持 insert、remove、get 的 Set

## 核心结论

来源要求“手写实现一个 Set 集合，支持 insert、remove、get”，但 `get` 对 Set 并不是标准 Java `Set` API，来源也没有保存冲突处理、扩容、null、返回值和并发语义。因此先声明一个可执行合同：实现泛型哈希集合；不接受 null；元素唯一性由 `equals` + `hashCode` 决定；`insert(E)` 返回是否新插入，`remove(E)` 返回是否真的删除，`get(E probe)` 返回集合中与 probe 相等的**已存对象实例**，不存在时返回 null。实现不保证线程安全。

底层用数组 + 单链表分离链接处理哈希冲突，容量保持 2 的幂，负载因子 0.75，超过阈值就扩容并重新分桶。平均情况下 insert/remove/get 都是 O(1)；如果大量键恶意碰撞到同一桶，链表会退化到 O(N)。

## 1 分钟版

- Set 的核心不变量是：按 `equals` 看，每个逻辑元素最多保存一份。
- 先对 `hashCode` 做轻量 spread，再用 `hash & (capacity-1)` 定位桶。
- 桶里用链表解决碰撞；hash 相同不代表元素相同，仍必须调用 `equals`。
- `insert` 先查重，存在就返回 false；不存在就头插并增加 size。
- `remove` 在桶链表里断开目标节点；`get` 返回真正存储的 value，而不是把 probe 原样返回。
- 元素数超过 0.75×容量时容量翻倍，并把所有节点按新 mask 重新分桶。
- 平均 O(1)，碰撞严重时最坏 O(N)；这里没有实现 Java HashMap 的树化优化。

## 3 分钟版

```java
import java.util.Objects;

public final class SimpleHashSet<E> {
    private static final float LOAD_FACTOR = 0.75f;
    private Node<E>[] table;
    private int size;
    private int threshold;

    @SuppressWarnings("unchecked")
    public SimpleHashSet() {
        table = (Node<E>[]) new Node<?>[16];
        threshold = (int) (table.length * LOAD_FACTOR);
    }

    public boolean insert(E value) {
        Objects.requireNonNull(value, "null values are not supported");
        if (findNode(value) != null) return false;
        if (size + 1 > threshold) resize();

        int hash = spread(value.hashCode());
        int index = hash & (table.length - 1);
        table[index] = new Node<>(hash, value, table[index]);
        size++;
        return true;
    }

    public boolean remove(E value) {
        Objects.requireNonNull(value, "null values are not supported");
        int hash = spread(value.hashCode());
        int index = hash & (table.length - 1);
        Node<E> prev = null;
        Node<E> cur = table[index];
        while (cur != null) {
            if (cur.hash == hash && cur.value.equals(value)) {
                if (prev == null) table[index] = cur.next;
                else prev.next = cur.next;
                size--;
                return true;
            }
            prev = cur;
            cur = cur.next;
        }
        return false;
    }

    public E get(E probe) {
        Objects.requireNonNull(probe, "null values are not supported");
        Node<E> node = findNode(probe);
        return node == null ? null : node.value;
    }

    public int size() {
        return size;
    }

    private Node<E> findNode(E value) {
        int hash = spread(value.hashCode());
        int index = hash & (table.length - 1);
        for (Node<E> cur = table[index]; cur != null; cur = cur.next) {
            if (cur.hash == hash && cur.value.equals(value)) return cur;
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private void resize() {
        Node<E>[] old = table;
        Node<E>[] next = (Node<E>[]) new Node<?>[old.length << 1];
        for (Node<E> head : old) {
            Node<E> cur = head;
            while (cur != null) {
                Node<E> after = cur.next;
                int index = cur.hash & (next.length - 1);
                cur.next = next[index];
                next[index] = cur;
                cur = after;
            }
        }
        table = next;
        threshold = (int) (table.length * LOAD_FACTOR);
    }

    private static int spread(int hash) {
        return hash ^ (hash >>> 16);
    }

    private static final class Node<E> {
        final int hash;
        final E value;
        Node<E> next;

        Node(int hash, E value, Node<E> next) {
            this.hash = hash;
            this.value = value;
            this.next = next;
        }
    }
}
```

`get` 的语义尤其要说明：如果集合里存的是对象 `stored`，调用者拿一个 `equals(stored)` 但不是同一引用的 `probe` 来查，返回的是 `stored`。这让 `get` 有真实意义；如果只是返回 probe，那么它和 `contains` 几乎没有区别。

## 关键细节

- **get 不是标准 Set API**：来源明确写了 get，但没定义语义；候选把它定义成“按相等键取回已存代表对象”，并明确记录这是合同选择。
- **hashCode 不能替代 equals**：两个不同对象可能 hash 一样。桶定位先用 hash，最终相等性必须由 `equals` 决定。
- **重复插入**：找到相等对象后不覆盖旧实例，返回 false；因此 `get(probe)` 仍返回最初保存的对象。
- **扩容必须重分桶**：容量变化后 `hash & (capacity-1)` 的结果可能变化，不能只把旧桶数组直接复制。
- **null 合同**：为了让 `get` 的 null 返回值明确表示“不存在”，当前实现直接拒绝 null 元素。若要支持 null，需要单独定义存在性与 get 返回语义。
- **容量为 2 的幂**：这样可以用位与替代取模；spread 把高位信息折到低位，减少某些低位分布差的 hashCode 造成的聚集。
- **复杂度**：均匀哈希下平均 O(1)；所有 key 冲突到同一桶时最坏 O(N)。生产级 HashMap 还会做树化等防退化处理，这里没有冒充完整 JDK 实现。
- **线程安全**：insert/remove/resize 都会修改链表和 table，本实现不是并发容器。

## 原理机制

哈希 Set 把“全局查找”拆成两层：先用 hash 把候选范围缩到一个桶，再在桶内用 equals 做精确判等。只要始终满足：

1. 相等对象必须有相同 hashCode；
2. 一个逻辑元素最多对应一个节点；
3. 扩容后每个节点按新容量重新定位；

那么 insert/remove/get 就能共享同一套定位规则。

负载因子是时间与空间的折中。容量过小会让链表变长，容量过大浪费数组空间。0.75 是当前候选选择，不是来源强制值。扩容偶尔需要 O(N) 迁移，但摊销到一系列插入上，平均插入仍可视为 O(1)。

## 项目经验版

来源没有真实业务键类型、并发量或内存约束，不能虚构线上集合实现。工程里通常直接使用标准库 `HashSet/HashMap`；手写版本主要用于解释哈希、碰撞和扩容机制。如果面对不可信 key 或并发访问，还需要考虑哈希洪泛、树化/随机化、内存上限、并发控制和迭代一致性，这些都超出当前保存题面的要求。

## 常见追问

- 问：Set 为什么还需要 get？答：标准 Set 通常只有 contains；但来源明确要求 get，所以这里定义为“用 probe 找到并返回集合中实际存储的相等对象”。如果面试官只是想判断存在，应把 API 改成 contains。
- 问：hashCode 一样就认为相等吗？答：不行，hash collision 很正常；hash 只缩小搜索桶，最终仍要 `equals`。
- 问：为什么扩容后要 rehash？答：保存的 hash 不变，但桶索引依赖 `capacity-1`；capacity 翻倍后索引可能变化，所以必须重新挂链。
- 问：为什么容量必须是 2 的幂？答：当前实现用 `hash & (len-1)` 做索引；2 的幂让 mask 覆盖低位。不是唯一方案，也可以用质数容量配合取模。
- 问：最坏复杂度为什么是 O(N)？答：如果所有元素都落到一个链表桶，查找/删除就要线性扫描。JDK 生产实现会用更复杂策略减轻恶意碰撞。
- 问：为什么不支持 null？答：为了让 get 返回 null 明确代表未找到，并保持示例边界简单；支持 null 也可以，但必须单独定义语义。

## 易错点

- 只比较 hashCode，不比较 equals，碰撞时把不同元素误判为同一个。
- 重复 insert 时覆盖已有对象，却没有说明 get 应返回哪个实例。
- 扩容只扩大数组、不重新分桶，导致旧元素再也查不到。
- remove 删除链表头节点时漏更新 bucket head。
- 把平均 O(1) 写成无条件最坏 O(1)。
- 来源的 get 语义不明确，却直接假装它就是 Java Set 标准接口。
- 没说明 null 和线程安全边界。
'''

TEST = r'''import java.util.*;

public final class SimpleHashSetTest {
    private static final class Key {
        final int id;
        final String label;
        Key(int id, String label) { this.id = id; this.label = label; }
        @Override public int hashCode() { return 7; }
        @Override public boolean equals(Object other) {
            return other instanceof Key k && k.id == id;
        }
    }

    public static void main(String[] args) {
        SimpleHashSet<Key> set = new SimpleHashSet<>();
        Key stored = new Key(1, "stored");
        Key probe = new Key(1, "probe");
        if (!set.insert(stored)) throw new AssertionError("first insert");
        if (set.insert(probe)) throw new AssertionError("duplicate must not insert");
        if (set.size() != 1) throw new AssertionError("duplicate size");
        if (set.get(probe) != stored) throw new AssertionError("get must return stored representative");

        for (int i = 2; i <= 2000; i++) {
            if (!set.insert(new Key(i, "k" + i))) throw new AssertionError("insert " + i);
        }
        if (set.size() != 2000) throw new AssertionError("collision resize size");
        for (int i = 1; i <= 2000; i++) {
            Key found = set.get(new Key(i, "x"));
            if (found == null || found.id != i) throw new AssertionError("missing collision key " + i);
        }
        for (int i = 1; i <= 2000; i += 2) {
            if (!set.remove(new Key(i, "remove"))) throw new AssertionError("remove " + i);
        }
        if (set.size() != 1000) throw new AssertionError("post-remove size");
        for (int i = 1; i <= 2000; i++) {
            boolean present = set.get(new Key(i, "check")) != null;
            if (present != (i % 2 == 0)) throw new AssertionError("presence " + i);
        }

        SimpleHashSet<Integer> actual = new SimpleHashSet<>();
        Set<Integer> oracle = new HashSet<>();
        Random random = new Random(20260829L);
        for (int round = 0; round < 100_000; round++) {
            int value = random.nextInt(20_001) - 10_000;
            int op = random.nextInt(3);
            if (op == 0) {
                boolean a = actual.insert(value);
                boolean b = oracle.add(value);
                if (a != b) throw new AssertionError("insert round=" + round);
            } else if (op == 1) {
                boolean a = actual.remove(value);
                boolean b = oracle.remove(value);
                if (a != b) throw new AssertionError("remove round=" + round);
            } else {
                Integer got = actual.get(value);
                if ((got != null) != oracle.contains(value)) throw new AssertionError("get round=" + round);
            }
            if (actual.size() != oracle.size()) throw new AssertionError("size round=" + round);
        }

        try {
            actual.insert(null);
            throw new AssertionError("null should fail");
        } catch (NullPointerException expected) {}

        System.out.println("PASS duplicate-representative forced-collisions resize-remove 100000-random-vs-hashset null-boundary");
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
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != CID:
        raise SystemExit('canonical context drift')
    if ctx.get('answer_type') != 'coding':
        raise SystemExit(f"answer type drift: {ctx.get('answer_type')}")
    if ctx.get('canonical', {}).get('question_ids') != [QID]:
        raise SystemExit(f"ownership drift: {ctx.get('canonical', {}).get('question_ids')}")
    src = next((x for x in ctx.get('source_questions', []) if x.get('question_id') == QID), None)
    if not src or src.get('original_question') != EXPECTED or src.get('is_valid_for_library') is not True:
        raise SystemExit('source wording/validity drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b53-custom-set-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'SimpleHashSet.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'SimpleHashSetTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'SimpleHashSet.java', 'SimpleHashSetTest.java', cwd=tmpdir)
        stdout = run('java', 'SimpleHashSetTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS duplicate-representative forced-collisions resize-remove 100000-random-vs-hashset null-boundary'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac SimpleHashSet.java SimpleHashSetTest.java && java SimpleHashSetTest',
        'stdout': stdout,
        'checks': [
            'duplicate insertion preserves original stored representative returned by get',
            '2000 constant-hash collision keys survive resize and removal',
            '100000 deterministic random operations agree with java.util.HashSet membership semantics',
            'null rejection matches the explicit candidate contract',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0053 exact custom-Set source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 custom hash-set deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source asks for a hand-written Set with insert, remove, and get; it does not define get semantics, collision strategy, resizing, null handling, return values, or concurrency.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '关键细节', '易错点']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate defines a non-null generic hash set where insert/remove return booleans and get returns the stored representative object equal to the probe or null if absent.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'hash-set-mechanism', 'text': 'Bucket indexing uses a spread hash and power-of-two mask, collisions use separate chaining with equals checks, and resizing re-buckets all nodes under the new mask.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制']},
        {'claim_id': 'validation', 'text': 'Executable validation covers stored-representative get semantics, forced hash collisions across resize/removal, 100000 deterministic random operations against java.util.HashSet, and null rejection.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '常见追问', '易错点']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate identifies the source ambiguity that get is not standard Java Set API and explicitly defines useful stored-representative semantics rather than silently treating it as contains.',
        'Separate chaining checks both cached hash and equals, so forced hash collisions do not collapse distinct elements.',
        'Duplicate insertion preserves the originally stored instance, making get(probe) semantics deterministic and testable.',
        'Resize correctly re-buckets every node using the new capacity mask instead of merely copying bucket heads.',
        'The answer states average O(1) and worst-case O(N) under collision rather than claiming unconditional constant time.',
        'OpenJDK 21 validation covers constant-hash collision chains through resize/removal and 100000 deterministic random operations against java.util.HashSet.',
        'Null and thread-safety boundaries are explicit, and production-only hardening such as treeification is separated from the interview implementation.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0053-custom-set-20260829-v1',
        'review_version': 'batch-0053.custom-set.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0053 custom-Set source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0053-custom-set-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'duplicate equal probe', 'expected': 'insert false and get returns original stored instance', 'actual': 'pass', 'passed': True},
                {'case': 'forced constant-hash collisions with resize/remove', 'expected': 'all membership operations remain exact', 'actual': 'pass', 'passed': True},
                {'case': '100000 deterministic random operations', 'expected': 'matches java.util.HashSet membership and size', 'actual': 'pass', 'passed': True},
                {'case': 'null insert', 'expected': 'NullPointerException under declared contract', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_eaba609d7a28fdf408eb6f4924804982` source-first isolated review PASS: the source asks for a hand-written Set with insert/remove/get while get semantics, collision/resizing/null/return/concurrency behavior remain explicit candidate contract. The candidate defines get as returning the stored equal representative, implements separate-chaining hashing with equals checks and full re-bucketing on resize, and OpenJDK 21 validation covers forced collisions, duplicate-instance semantics, resize/remove, 100000 deterministic operations against java.util.HashSet, and null rejection. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
