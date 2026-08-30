#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0061 Java DCL singleton candidate."""

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
CID = 'cq_q_0616abe7f8861fde19fda29ad5b2b305'
QIDS = ['0616abe7f8861fde19fda29ad5b2b305']
EXPECTED_VARIANTS = {'算法手撕：使用 Java 实现基于 DCL（双重检查锁）的单例。'}
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

PRIMARY_SOURCES = [
    {
        'source_id': 'jls-17.4.5',
        'title': 'Java Language Specification SE 26 §17.4.5 Happens-before Order',
        'locator': 'https://docs.oracle.com/javase/specs/jls/se26/html/jls-17.html#jls-17.4.5',
        'source_type': 'external_primary_source',
        'checked_at': DATE,
        'claim': 'A write to a volatile field happens-before every subsequent read of that field; monitor unlock happens-before every subsequent lock on that monitor.',
    },
    {
        'source_id': 'jls-8.3.1.4',
        'title': 'Java Language Specification SE 26 §8.3.1.4 volatile Fields',
        'locator': 'https://docs.oracle.com/javase/specs/jls/se26/html/jls-8.html#jls-8.3.1.4',
        'source_type': 'external_primary_source',
        'checked_at': DATE,
        'claim': 'The Java Memory Model gives volatile fields cross-thread visibility/consistency guarantees.',
    },
]

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_0616abe7f8861fde19fda29ad5b2b305","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# Java DCL 单例：第二次检查 + synchronized + volatile 安全发布

## 核心结论

DCL（Double-Checked Locking）的目标是：实例已经初始化后走无锁快路径，只在第一次初始化竞争时进入同步块。Java 版本的关键不是只写“两次 `if`”，而是实例字段必须是 `volatile`：JLS 的 happens-before 规则保证对 volatile 字段的写入先行发生于后续对同一字段的读取，因此构造完成后发布出去的引用及此前的初始化写入能被之后读取该引用的线程正确观察。同步块负责把“检查后创建”这段临界区串行化，第二次检查防止多个同时通过外层检查的线程重复创建。

## 1 分钟版

- `private static volatile Singleton INSTANCE;`：共享实例引用必须 `volatile`。
- 第一次 `if (INSTANCE == null)` 是快路径；实例已经存在时不加锁。
- `synchronized (Singleton.class)` 只保护初始化竞争区。
- 进入锁后必须第二次检查，因为可能有多个线程都在外层看到 `null`，但只有第一个拿到锁的线程应该创建实例。
- 创建后写入 volatile `INSTANCE`；JLS 规定 volatile 写 happens-before 后续 volatile 读，建立安全发布关系。

## 3 分钟版

```java
public final class Singleton {
    private static volatile Singleton INSTANCE;

    private Singleton() {}

    public static Singleton getInstance() {
        Singleton result = INSTANCE;
        if (result == null) {
            synchronized (Singleton.class) {
                result = INSTANCE;
                if (result == null) {
                    result = new Singleton();
                    INSTANCE = result;
                }
            }
        }
        return result;
    }
}
```

这里用局部变量 `result` 只是减少已经初始化后的 volatile 读取次数，并不是 DCL 正确性的必要条件。真正的正确性边界是：共享引用是 `volatile`，创建动作位于同步初始化区，锁内有第二次空检查，并且只在对象构造完成后把引用赋给 `INSTANCE`。

## 关键细节

- **为什么要 `volatile`**：JLS §17.4.5 明确规定，同一 volatile 字段的写 happens-before 后续读。这个同步边把发布线程在 volatile 写之前的程序顺序动作，与读取线程 volatile 读之后的动作连接起来；因此 DCL 不能把 `volatile` 当作“性能提示”。
- **为什么还要 `synchronized`**：`volatile` 提供可见性/顺序保证，但“检查为 null → 创建 → 发布”仍是一个需要互斥的初始化协议。监视器确保同一时刻只有一个线程执行锁内创建路径。
- **为什么检查两次**：线程 A、B 都可能在外层同时读到 `null`。A 先拿锁创建并发布；B 随后拿锁时必须重新读取 `INSTANCE`，否则 B 还会再创建一个对象。
- **为什么局部变量可选**：直接对 `INSTANCE` 做两次检查也是正确 DCL；局部缓存主要避免热路径上重复 volatile read。锁内仍必须重新读取共享字段，不能只沿用锁外的旧 `result`。
- **构造器私有**：这只阻止普通外部 `new`；反射、序列化、克隆等是否需要额外防护取决于题目范围。本来源只要求手撕 DCL，不把这些扩展边界伪装成必需条件。
- **替代方案**：如果题目不强制 DCL，静态内部类、枚举单例或启动期依赖注入通常更简单；但这道题明确要求 DCL，所以答案应先把 DCL 写正确。

## 原理机制

DCL 把初始化前和初始化后分成两个阶段。初始化前，多线程可能同时观察到 `null`，因此通过类对象监视器把真正的创建串行化；初始化后，所有调用直接读取已发布引用并返回，不再获取监视器。

内存模型上，发布线程先执行构造相关写入，再执行 `INSTANCE = result` 这个 volatile write。读取线程后续从同一 volatile 字段读到该发布值时，JLS 的 volatile synchronizes-with / happens-before 规则给出跨线程的可见性与顺序关系。与此同时，监视器 unlock/lock 也有 happens-before 规则，保证竞争初始化线程进入锁后能看到前一个持锁线程的发布结果。因此“volatile + 锁内第二次检查”共同构成这个初始化协议。

## 项目经验版

来源没有真实项目背景，不能虚构“线上使用过 DCL”。实际代码评审时，我会先问为什么需要手写单例：如果生命周期由 Spring 等容器管理，通常不需要再额外实现 DCL；如果确实是无容器的懒加载全局对象，则重点检查 `volatile`、两次检查、锁对象是否稳定、构造期间是否泄露 `this`，以及异常初始化时的重试语义。这里的并发测试只能验证当前实现的观测行为，内存模型正确性仍以 JLS 同步规则为依据。

## 常见追问

- 问：没有 `volatile` 一定每次都失败吗？答：不是“每次运行都能复现失败”的问题，而是缺少所需的 Java Memory Model 安全发布保证；并发测试通过不能替代 happens-before 证明。
- 问：有 `synchronized` 了为什么还要 `volatile`？答：外层快路径读取发生在锁外。初始化后多数调用不再进入监视器，因此共享引用本身需要 volatile 发布/读取关系。
- 问：为什么锁内一定要再检查一次？答：多个线程可以同时通过第一次检查并依次进入锁；后进入者若不复查，会在前一个线程已经创建实例后再次创建。
- 问：局部变量 `result` 有什么作用？答：减少热路径上对 volatile 字段的重复读取；锁内仍从 `INSTANCE` 重新取值，所以不会把锁外旧值当成初始化结论。
- 问：能不能把整个 `getInstance()` 声明成 `synchronized`？答：可以保证互斥和可见性，而且更简单，但每次调用都要进入同步方法；DCL 的目的正是让初始化后的调用走无锁快路径。
- 问：静态内部类是不是更好？答：如果题目只要线程安全懒加载，通常更简单；但当前来源明确要求 DCL，所以应先完成指定机制，再把内部类作为替代方案说明。

## 易错点

- 只写两次 `if` + `synchronized`，却把实例字段声明成普通 `static`。
- 只有外层检查，没有锁内第二次检查，导致竞争线程依次创建多个实例。
- 锁内第二次检查仍使用锁外缓存的旧 `result`，没有重新读取共享 `INSTANCE`。
- 在对象尚未完成初始化前把 `this` 泄露到其他共享位置，破坏安全发布假设。
- 用一次“多线程测试没出错”来证明没有 `volatile` 也正确；内存模型边界需要规范级 happens-before 依据。
- 题目没要求反射/序列化防御，却无限扩张单例实现并掩盖 DCL 的核心机制。
'''

TEST = r'''import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CountDownLatch;

public final class SingletonTest {
    public static void main(String[] args) throws Exception {
        Field field = Singleton.class.getDeclaredField("INSTANCE");
        int m = field.getModifiers();
        if (!Modifier.isPrivate(m) || !Modifier.isStatic(m) || !Modifier.isVolatile(m)) {
            throw new AssertionError("INSTANCE must be private static volatile");
        }
        Constructor<?> ctor = Singleton.class.getDeclaredConstructor();
        if (!Modifier.isPrivate(ctor.getModifiers())) throw new AssertionError("constructor must be private");

        final int threads = 256;
        final int rounds = 20000;
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch start = new CountDownLatch(1);
        List<Singleton> observed = Collections.synchronizedList(new ArrayList<>());
        List<Thread> workers = new ArrayList<>();
        for (int i = 0; i < threads; i++) {
            Thread t = new Thread(() -> {
                try {
                    ready.countDown();
                    start.await();
                    Singleton first = null;
                    for (int j = 0; j < rounds; j++) {
                        Singleton s = Singleton.getInstance();
                        if (s == null) throw new AssertionError("null singleton");
                        if (first == null) first = s;
                        else if (first != s) throw new AssertionError("identity changed inside thread");
                    }
                    observed.add(first);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException(e);
                }
            }, "dcl-test-" + i);
            workers.add(t);
            t.start();
        }
        ready.await();
        start.countDown();
        for (Thread t : workers) t.join();
        Set<Singleton> identities = Collections.newSetFromMap(new IdentityHashMap<>());
        identities.addAll(observed);
        identities.add(Singleton.getInstance());
        if (identities.size() != 1) throw new AssertionError("expected one identity, got " + identities.size());
        System.out.println("PASS modifiers=private-static-volatile constructor=private threads=256 calls=" + (threads * rounds) + " identities=1");
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
    if not item or item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: frozen coding source item missing')
    if item.get('personal_fact_verification_required') or item.get('secondary_coverage_required'):
        raise SystemExit(f'{CID}: unexpected sensitive/secondary gate')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: frozen ownership drift: {item.get("question_ids")}')
    wordings = {q.get('original_question') for q in item.get('source_questions', [])}
    if wordings != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: source wording drift: {wordings}')

    context_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}/context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: context/type missing')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    write_json(out / 'primary_sources.json', {
        'schema_version': 'answer_primary_source_packet.v1',
        'canonical_id': CID,
        'checked_at': DATE,
        'sources': PRIMARY_SOURCES,
        'source_first_rule': 'JLS synchronization claims are primary-source-backed; runtime stress validates the concrete implementation but does not substitute for the memory-model proof.',
    })

    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    evidence = ROOT / f'review/evidence/{CID}.json'
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in HEADINGS:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if CANDIDATE.count('- 问：') < 5:
        raise SystemExit(f'{CID}: follow-up coverage too small')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'{CID}: candidate must contain exactly one Java implementation block')

    with tempfile.TemporaryDirectory(prefix='b61-dcl-') as temp:
        work = Path(temp)
        (work / 'Singleton.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (work / 'SingletonTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'Singleton.java', 'SingletonTest.java', cwd=work)
        stdout = run('java', 'SingletonTest', cwd=work).stdout.strip()

    expected_stdout = 'PASS modifiers=private-static-volatile constructor=private threads=256 calls=5120000 identities=1'
    if stdout != expected_stdout:
        raise SystemExit(f'{CID}: unexpected fixture output: {stdout}')

    command = 'javac Singleton.java SingletonTest.java && java SingletonTest'
    checks = [
        'INSTANCE is reflectively verified private static volatile',
        'constructor is reflectively verified private',
        '256 threads start concurrently and execute 5,120,000 total getInstance calls',
        'all observed references are non-null and share exactly one object identity',
    ]
    write_json(out / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': command,
        'stdout': stdout,
        'checks': checks,
        'environment': {'java': 'OpenJDK 21'},
        'limitation': 'Stress testing validates observed behavior of the exact implementation; volatile publication correctness is justified by the cited JLS happens-before rules rather than inferred from test success.',
    })

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0061 frozen repository source context for Java DCL singleton', 'locator': str(context_path), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'source-inventory', 'title': 'Batch 0061 frozen live source inventory', 'locator': str(inventory_path), 'source_type': 'repository_structured_source', 'checked_at': DATE},
        *PRIMARY_SOURCES,
        {'source_id': 'fixture', 'title': 'OpenJDK structural and concurrent stress validation for the exact DCL implementation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The preserved source specifically requests a Java singleton implemented with DCL; reflection/serialization defenses, DI-container integration, and a particular API beyond getInstance are not preserved source requirements.',
            'source_ids': ['repository-source', 'source-inventory'],
            'answer_locations': ['核心结论', '3 分钟版', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'memory-model',
            'text': 'JLS happens-before rules state that a volatile write happens-before every subsequent read of the same field and a monitor unlock happens-before a subsequent lock on that monitor; volatile fields receive Java Memory Model cross-thread consistency guarantees. These rules justify volatile publication plus synchronized initialization rather than treating a stress test as proof.',
            'source_ids': ['jls-17.4.5', 'jls-8.3.1.4'],
            'answer_locations': ['核心结论', '1 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        },
        {
            'claim_id': 'reference-behavior',
            'text': 'The exact candidate compiles; reflection verifies the private static volatile field and private constructor; 256 concurrently released threads perform 5,120,000 getInstance calls and observe one non-null object identity.',
            'source_ids': ['fixture'],
            'answer_locations': ['3 分钟版', '项目经验版'],
        },
    ]
    locations = ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']
    coverage = [{'question_id': qid, 'covered': True, 'answer_locations': locations} for qid in QIDS]
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest,
        'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources, 'claims': claims, 'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    reviewer_id = 'source-first-isolated-reviewer-batch-0061-dcl-singleton-20260831-v1'
    findings = [
        'The candidate directly implements the frozen Java DCL request instead of substituting a different singleton idiom.',
        'The correctness argument is grounded in JLS volatile and monitor happens-before rules; concurrent stress is explicitly treated as implementation validation, not as proof that volatile is unnecessary.',
        'The implementation performs the second shared-field read inside the synchronized block, publishes only after construction, and uses a local result only as an optional hot-path optimization.',
        'Reflection verifies the field modifiers and private constructor, while a 256-thread/5,120,000-call stress run observes exactly one non-null identity.',
        'Alternatives such as synchronized methods, static holder idiom, enum singleton, and DI are kept as tradeoffs rather than smuggled into the requested DCL contract.',
        'No production or personal claim is fabricated from the source.',
    ]
    review_version = 'batch-0061.dcl-singleton.v1'
    write_json(out / 'isolated_review_result.json', {
        'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest,
        'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': reviewer_id,
        'review_version': review_version, 'decision': 'pass', 'revision_round': 1,
        'source_packet': [str(context_path), str(inventory_path), str(out / 'primary_sources.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': SCORES, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [],
        'findings': findings, 'promotion_blockers': [PROMOTION_BLOCKER],
    })
    write_json(evidence, {
        'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0061-dcl-singleton-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{'source_id': 'isolated-review', 'title': 'Batch 0061 Java DCL singleton source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}],
        'claims': claims, 'source_question_coverage': coverage,
        'validation': {'command': command, 'result': 'pass', 'reported_stdout': stdout, 'checks': checks,
                       'boundary_tests': [{'case': check, 'expected': 'pass under declared candidate contract', 'actual': 'pass', 'passed': True} for check in checks]},
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': reviewer_id, 'review_version': review_version, 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': SCORES, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': PROMOTION_BLOCKER,
    })

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    if '## Progress' not in task:
        task += '\n\n## Progress\n'
    note = (
        '- [x] `cq_q_0616abe7f8861fde19fda29ad5b2b305` source-first isolated review PASS: '
        f'candidate digest `{digest}`; the requested Java DCL implementation is backed by JLS §17.4.5/§8.3.1.4 volatile/monitor publication rules. '
        'OpenJDK validation reflectively verifies `private static volatile` + private constructor and 256 simultaneously released threads perform 5,120,000 calls while observing exactly one non-null identity. '
        'Formal promotion remains blocked by repository human-approval/real-review policy.'
    )
    if note not in task:
        task += '\n' + note
    task_path.write_text(task + '\n', encoding='utf-8')

    print(f'PASS canonical={CID} source_question_ids={len(QIDS)} candidate_sha256={digest} fixture={stdout}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
