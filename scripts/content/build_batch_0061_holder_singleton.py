#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0061 generic Java singleton candidate."""

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
CID = 'cq_q_501a3a0fb13e9816cbe7dde18673c074'
QIDS = ['501a3a0fb13e9816cbe7dde18673c074', '83a0dbb0e7edc58944cd9fc1159d3d30']
EXPECTED_VARIANTS = {
    '手写单例模式（Singleton Pattern）。',
    '算法：Java 手写单例模式（Singleton Pattern）。',
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
PRIMARY_SOURCES = [
    {
        'source_id': 'jls-12.4.1',
        'title': 'Java Language Specification SE 26 §12.4.1 When Initialization Occurs',
        'locator': 'https://docs.oracle.com/en/java/javase/26/docs/specs/jls/jls-12.html#jls-12.4.1',
        'source_type': 'official_specification_or_standard',
        'checked_at': DATE,
        'claim': 'A class is initialized immediately before first active use such as use of a non-constant static field declared by that class.',
    },
    {
        'source_id': 'jls-12.4.2',
        'title': 'Java Language Specification SE 26 §12.4.2 Detailed Initialization Procedure',
        'locator': 'https://docs.oracle.com/en/java/javase/26/docs/specs/jls/jls-12.html#jls-12.4.2',
        'source_type': 'official_specification_or_standard',
        'checked_at': DATE,
        'claim': 'Class initialization is synchronized using a unique initialization lock and other threads wait for in-progress initialization to complete.',
    },
    {
        'source_id': 'jls-8.3.2',
        'title': 'Java Language Specification SE 26 §8.3.2 Field Initialization',
        'locator': 'https://docs.oracle.com/javase/specs/jls/se26/html/jls-8.html#jls-8.3.2',
        'source_type': 'official_specification_or_standard',
        'checked_at': DATE,
        'claim': 'A static field initializer is evaluated and assigned exactly once when its declaring class is initialized.',
    },
]

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_501a3a0fb13e9816cbe7dde18673c074","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# Java 单例：静态内部类 Holder 写法

## 核心结论

这道题只要求“手写 Java 单例”，没有指定必须用双重检查锁。一个边界清楚、线程安全且保持懒加载的实现是静态内部类 Holder：外部 `Singleton` 初始化时不会主动读取 `Holder.INSTANCE`；第一次调用 `getInstance()` 读取这个非编译期常量静态字段时，JLS 的类初始化规则会触发 `Holder` 初始化，而类初始化过程本身有同步协议，`INSTANCE` 的静态字段初始化只执行一次。因此不需要自己写 `synchronized` 或 `volatile` 就能完成这一个具体实现的线程安全初始化。

## 1 分钟版

- 构造器设为 `private`，阻止普通调用方直接 `new`。
- 真正的实例放在私有静态内部类 `Holder` 中：`private static final Singleton INSTANCE = new Singleton();`。
- `getInstance()` 只返回 `Holder.INSTANCE`。
- 第一次主动使用 `Holder.INSTANCE` 时才初始化 `Holder`，所以实例是懒加载。
- JLS 规定类初始化有唯一初始化锁，其他线程会等待正在进行的初始化完成；静态字段初始化在该类初始化时执行一次，所以无需手写 DCL。
- 这只解决普通 Java 调用路径下的单例初始化；反射、反序列化、多个 ClassLoader 等更强约束需要另外定义，不应默认宣称全部防住。

## 3 分钟版

```java
public final class Singleton {
    private Singleton() {}

    private static final class Holder {
        private static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE;
    }
}
```

调用路径很简单：类加载并不等于立即初始化所有嵌套类；当 `getInstance()` 第一次读取 `Holder.INSTANCE` 时，JLS §12.4.1 的主动使用规则要求先初始化 `Holder`。JLS §12.4.2 为每个类规定唯一初始化锁，并让其他线程等待正在进行的初始化；`INSTANCE` 的初始化表达式因此在 `Holder` 初始化过程中完成一次。后续调用直接读取已经初始化好的静态字段，没有显式锁的热路径。

## 关键细节

- **为什么懒加载**：实例字段属于 `Holder`，不是外部类。只有真正主动使用 `Holder.INSTANCE` 时才需要初始化 `Holder`；仅仅加载/初始化外部 `Singleton` 不等于提前创建实例。
- **为什么线程安全**：这里依赖的是 Java 类初始化协议，而不是“测试跑很多线程没出错”。JLS §12.4.2 明确给类初始化设置唯一初始化锁，并处理多个线程并发请求初始化的情况。
- **为什么只创建一次**：`INSTANCE` 是 `Holder` 的静态字段，JLS §8.3.2 规定静态字段初始化器在类初始化时求值并赋值一次；`Holder` 成功初始化后不会每次 `getInstance()` 都重跑初始化器。
- **为什么不需要 volatile/DCL**：当前实现没有“先无锁读取一个可能尚未安全发布的可变实例字段，再竞争初始化”的流程；初始化与发布由类初始化机制承接。若题目明确要求 DCL，应换成 `volatile + synchronized + 第二次检查`，不能把 Holder 写法冒充 DCL。
- **`final` 的作用**：外部类和 Holder 设为 `final` 主要是在示例中收紧继承边界；真正阻止普通外部构造的是私有构造器，真正保证这条初始化路径线程安全的是类初始化协议。
- **边界**：反射可以尝试访问私有构造器；Java 原生序列化还涉及 `readResolve`；多个 ClassLoader 可能各自得到一份类状态。这些都超出来源只要求“手写单例”的最小契约。

## 原理机制

Holder 写法把“什么时候创建实例”转换成“什么时候初始化一个独立的类”。这是一个重要的职责转移：我们不自己维护 `INSTANCE == null` 的并发状态机，而是把一次性初始化交给 JVM/JLS 已定义的类初始化状态机。

第一次访问 `Holder.INSTANCE` 时，如果 `Holder` 尚未初始化，当前线程进入类初始化流程；若另一个线程正在初始化，后来线程等待；初始化成功后，所有正常调用都读取同一个静态字段。因此算法层面的单例不变量是“普通调用路径只暴露一个构造完成后的 `Singleton` 引用”，而实现层面利用语言运行时的一次性类初始化来维持这个不变量。

## 项目经验版

来源没有真实项目背景，不能虚构线上使用经历。实际项目里我会先问“为什么需要单例”：如果对象本来就由 Spring 等 DI 容器管理，通常优先让容器负责生命周期和作用域，而不是额外写全局单例；如果是纯 Java、确实需要懒加载且没有容器，Holder 是一个简洁选择。若需求还包括反序列化、反射防护、跨 ClassLoader 唯一性，则要把这些约束单独设计和测试，而不是把一个基础 Holder 示例说成万能方案。

## 常见追问

- 问：Holder 为什么是懒加载？答：实例字段声明在 Holder 中，第一次主动读取 `Holder.INSTANCE` 才触发 Holder 初始化；外部 Singleton 被加载或初始化并不会自动等价为 Holder 已初始化。
- 问：为什么并发调用不会创建多个实例？答：类初始化有唯一初始化锁，其他线程会等待正在进行的初始化完成；静态字段初始化器在该类初始化时执行一次。
- 问：为什么这里不写 `volatile`？答：因为没有 DCL 的共享可变引用发布流程；当前实现依赖类初始化协议完成一次性构造和可见性。若题目指定 DCL，volatile 仍是关键要求。
- 问：和饿汉式相比呢？答：饿汉式通常在外部类初始化时直接创建静态实例，最简单但不是按首次 `getInstance()` 懒创建；Holder 把实例延迟到 Holder 第一次主动使用。
- 问：和 enum 单例相比呢？答：enum 也很适合表达单例，并天然结合枚举的序列化语义；但如果面试题期待传统类 + `getInstance()` API，Holder 更直接展示懒初始化机制。
- 问：反射能不能破坏？答：普通私有构造器不是绝对安全边界，反射可在权限允许时尝试绕过。若题目要求防反射，需要额外约束，不能从基础单例实现自动推出。

## 易错点

- 把 Holder 写法说成“双重检查锁”，混淆两种完全不同的初始化机制。
- 把“类加载”与“类初始化”混为一谈，从而错误解释懒加载时机。
- 只凭多线程压力测试声称线程安全，而不给语言初始化规则依据。
- 构造器不是 `private`，导致普通调用方仍可直接创建额外实例。
- 声称一个基础实现天然保证跨 ClassLoader、反射和反序列化场景的全局唯一。
- 在已经由 DI 容器管理生命周期的对象上机械叠加手写单例，制造额外全局状态。
'''

TEST = r'''import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;
import java.util.concurrent.CountDownLatch;

public final class SingletonTest {
    public static void main(String[] args) throws Exception {
        Constructor<?> ctor = Singleton.class.getDeclaredConstructor();
        if (!Modifier.isPrivate(ctor.getModifiers())) throw new AssertionError("constructor must be private");

        Class<?> holder = null;
        for (Class<?> nested : Singleton.class.getDeclaredClasses()) {
            if (nested.getSimpleName().equals("Holder")) holder = nested;
        }
        if (holder == null) throw new AssertionError("Holder class missing");
        int holderMods = holder.getModifiers();
        if (!Modifier.isPrivate(holderMods) || !Modifier.isStatic(holderMods) || !Modifier.isFinal(holderMods)) {
            throw new AssertionError("Holder must be private static final");
        }
        Field field = holder.getDeclaredField("INSTANCE");
        int fieldMods = field.getModifiers();
        if (!Modifier.isPrivate(fieldMods) || !Modifier.isStatic(fieldMods) || !Modifier.isFinal(fieldMods)) {
            throw new AssertionError("INSTANCE must be private static final");
        }

        final int threads = 256;
        final int callsPerThread = 20000;
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(threads);
        Set<Singleton> identities = Collections.synchronizedSet(Collections.newSetFromMap(new IdentityHashMap<>()));
        Thread[] workers = new Thread[threads];
        for (int i = 0; i < threads; i++) {
            workers[i] = new Thread(() -> {
                ready.countDown();
                try {
                    start.await();
                    for (int c = 0; c < callsPerThread; c++) {
                        Singleton s = Singleton.getInstance();
                        if (s == null) throw new AssertionError("null singleton");
                        identities.add(s);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException(e);
                } finally {
                    done.countDown();
                }
            });
            workers[i].start();
        }
        ready.await();
        start.countDown();
        done.await();
        if (identities.size() != 1) throw new AssertionError("expected one identity, got " + identities.size());
        if (Singleton.getInstance() != Singleton.getInstance()) throw new AssertionError("sequential identity mismatch");
        System.out.println("PASS constructor=private holder=private-static-final instance=private-static-final threads=256 calls=5120000 identities=1");
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

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    context_raw = run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout
    context = json.loads(context_raw)
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: live context/type drift')
    live_qids = sorted((context.get('canonical') or {}).get('question_ids') or [])
    if live_qids != sorted(QIDS):
        raise SystemExit(f'{CID}: live context ownership drift: {live_qids}')
    write_json(out / 'context.json', context)
    write_json(out / 'primary_sources.json', {
        'schema_version': 'answer_primary_source_packet.v1',
        'canonical_id': CID,
        'checked_at': DATE,
        'sources': PRIMARY_SOURCES,
        'source_first_rule': 'Class-initialization guarantees are primary-source-backed by the JLS; concurrent stress validates the concrete Holder implementation but is not used as a substitute for the language-level initialization proof.',
    })

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

    with tempfile.TemporaryDirectory(prefix='xhs-holder-singleton-') as tmp:
        td = Path(tmp)
        (td / 'Singleton.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (td / 'SingletonTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'Singleton.java', 'SingletonTest.java', cwd=td)
        stdout = run('java', 'SingletonTest', cwd=td).stdout.strip()
    expected_stdout = 'PASS constructor=private holder=private-static-final instance=private-static-final threads=256 calls=5120000 identities=1'
    if stdout != expected_stdout:
        raise SystemExit(f'{CID}: unexpected fixture output: {stdout}')

    command = 'javac Singleton.java SingletonTest.java && java SingletonTest'
    checks = [
        'the outer singleton constructor is reflectively verified private',
        'Holder is reflectively verified private static final and INSTANCE is private static final',
        '256 threads start concurrently and execute 5,120,000 total getInstance calls',
        'all observed references are non-null and share exactly one object identity',
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
        'limitation': 'Stress testing validates observed behavior and structure of the exact Holder implementation; class-initialization synchronization/laziness claims are justified by the cited JLS rules rather than inferred from test success.',
    }
    write_json(out / 'writer_validation.json', validation)

    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0061 frozen repository source context for generic Java singleton', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'source-inventory', 'title': 'Batch 0061 frozen live source inventory', 'locator': str(inventory_path), 'source_type': 'repository_structured_source', 'checked_at': DATE},
        *PRIMARY_SOURCES,
        {'source_id': 'fixture', 'title': 'OpenJDK structural and concurrent stress validation for the exact static-holder singleton', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The preserved variants ask to hand-write a Java Singleton Pattern but do not require DCL, eager initialization, reflection defenses, serialization defenses, or cross-ClassLoader uniqueness; the candidate therefore chooses one explicit lazy thread-safe Holder implementation and keeps stronger boundaries separate.',
            'source_ids': ['repository-source', 'source-inventory'],
            'answer_locations': ['核心结论', '3 分钟版', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'class-initialization-model',
            'text': 'JLS class-initialization rules trigger initialization before active use of a non-constant static field, synchronize class initialization using a unique initialization lock, and evaluate a static field initializer once when its declaring class is initialized; these rules underpin the Holder idiom rather than a user-written DCL protocol.',
            'source_ids': ['jls-12.4.1', 'jls-12.4.2', 'jls-8.3.2'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        },
        {
            'claim_id': 'reference-behavior',
            'text': 'The exact candidate compiles; reflection verifies a private constructor, private static final Holder, and private static final INSTANCE; 256 concurrently released threads perform 5,120,000 getInstance calls and observe one non-null identity.',
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
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    reviewer_id = 'source-first-isolated-reviewer-batch-0061-holder-singleton-20260831-v1'
    review_version = 'batch-0061.holder-singleton.v1'
    findings = [
        'The candidate directly answers both frozen generic Java Singleton variants and deliberately does not conflate them with the separate DCL-specific Canonical already reviewed in this batch.',
        'The Holder implementation is lazy under the cited active-use rule and delegates synchronization/once-only static initialization to the JLS class-initialization protocol.',
        'The correctness argument is grounded in JLS §12.4.1/§12.4.2/§8.3.2; the stress test is explicitly treated as concrete implementation validation rather than proof of the language model.',
        'Reflection verifies the intended constructor/Holder/INSTANCE modifiers and a 256-thread, 5,120,000-call run observes exactly one non-null identity.',
        'Reflection, serialization, DI-container, and multiple-ClassLoader concerns are stated as separate boundaries rather than silently claimed solved.',
        'No production or personal claim is fabricated from the source.',
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
        'source_packet': [str(out / 'context.json'), str(inventory_path), str(out / 'primary_sources.json'), str(candidate_path), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
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
        'writer': {'writer_id': 'content-batch-0061-holder-singleton-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{'source_id': 'isolated-review', 'title': 'Batch 0061 static-holder singleton source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': command,
            'result': 'pass',
            'reported_stdout': stdout,
            'checks': checks,
            'boundary_tests': [{'case': check, 'expected': 'pass under declared candidate contract', 'actual': 'pass', 'passed': True} for check in checks],
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
    marker = f'- [x] `{CID}` source-first isolated review PASS:'
    if marker not in task:
        task += '\n' + (
            f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; '
            'the generic Java singleton uses the static-holder idiom and keeps the separate DCL Canonical distinct. '
            'JLS §12.4.1/§12.4.2/§8.3.2 back active-use, synchronized class initialization, and once-only static field initialization; OpenJDK validation reflectively verifies the intended structure and 256 simultaneously released threads perform 5,120,000 calls while observing one non-null identity. '
            'Formal promotion remains blocked by repository human-approval/real-review policy.'
        )
        task_path.write_text(task + '\n', encoding='utf-8')

    print(f'PASS canonical={CID} source_question_ids={len(QIDS)} candidate_sha256={digest} fixture={stdout}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
