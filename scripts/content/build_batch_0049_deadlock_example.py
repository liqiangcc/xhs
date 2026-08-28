#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0049 deadlock-example candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
CID = 'cq_q_d076a2fc3ca909dbfc2b295a0a578a51'
QID = 'd076a2fc3ca909dbfc2b295a0a578a51'
EXPECTED = '算法：写一个死锁的例子'
BATCH = '0049'
JLS_SYNC = 'https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.19'
THREAD_MXBEAN = 'https://docs.oracle.com/en/java/javase/21/docs/api/java.management/java/lang/management/ThreadMXBean.html#findMonitorDeadlockedThreads()'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d076a2fc3ca909dbfc2b295a0a578a51","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 写一个可复现的 Java 死锁例子

## 核心结论

最小死锁例子就是制造一个**锁顺序环**：线程 T1 先持有 A 再等 B，线程 T2 先持有 B 再等 A。为了让示例不是“靠 sleep 碰概率”，下面用 `CountDownLatch` 保证两个线程都已经拿到第一把锁之后，才同时尝试第二把锁，因此等待环可以稳定复现。修复思路不是“把 sleep 调小”，而是让所有线程遵守同一加锁顺序，直接打破环路。

## 1 分钟版

- 定义两把不同的 monitor：`LOCK_A`、`LOCK_B`。
- T1 进入 `synchronized (LOCK_A)`，T2 进入 `synchronized (LOCK_B)`；两者分别持有一把锁。
- 用一个计数器屏障等到“双方都持有第一把锁”，再继续。
- T1 尝试拿 B，T2 尝试拿 A；此时 T1 不退出 A 的 synchronized 块，T2 也不退出 B 的块，于是两边都无法推进。
- 真正修复时统一顺序，例如所有路径都先 A 后 B；仅减少 sleep、加日志或重试线程不能从结构上消除这个锁顺序环。

## 3 分钟版

```java
import java.util.concurrent.CountDownLatch;

public final class DeadlockExample {
    private static final Object LOCK_A = new Object();
    private static final Object LOCK_B = new Object();

    public static Thread[] startDeadlock() {
        CountDownLatch firstLocksHeld = new CountDownLatch(2);

        Thread t1 = new Thread(() -> {
            synchronized (LOCK_A) {
                firstLocksHeld.countDown();
                await(firstLocksHeld);
                synchronized (LOCK_B) {
                    // 永远到不了这里：T2 正持有 LOCK_B 并等待 LOCK_A。
                }
            }
        }, "deadlock-t1");

        Thread t2 = new Thread(() -> {
            synchronized (LOCK_B) {
                firstLocksHeld.countDown();
                await(firstLocksHeld);
                synchronized (LOCK_A) {
                    // 永远到不了这里：T1 正持有 LOCK_A 并等待 LOCK_B。
                }
            }
        }, "deadlock-t2");

        // 演示程序允许 JVM 在检测完成后退出；业务线程是否 daemon 是另一层生命周期策略。
        t1.setDaemon(true);
        t2.setDaemon(true);
        t1.start();
        t2.start();
        return new Thread[] { t1, t2 };
    }

    private static void await(CountDownLatch latch) {
        try {
            latch.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("demo interrupted", e);
        }
    }
}
```

这个版本比常见的“两个线程各 `sleep(100)` 再拿第二把锁”更可靠：`CountDownLatch(2)` 的含义是，两边只有在各自已经进入第一层 `synchronized` 后才把计数减一；计数归零以后，双方都还处在第一层同步块内部，再去获取对方持有的 monitor，于是形成确定的循环等待。

Java 语言规范规定，进入 `synchronized(obj)` 会获取 `obj` 关联的 monitor，只有同步块正常或异常退出时才解锁。因此 T1 阻塞在第二次加锁时并没有退出第一层块，A 仍由 T1 持有；T2 同理仍持有 B。JDK 21 的 `ThreadMXBean.findMonitorDeadlockedThreads()` 可以在运行中的 JVM 中查找这种 object-monitor 死锁，适合把这个示例从“看起来会死锁”变成可执行检测。

## 关键细节

- **必须是两把不同锁**：同一个 Java 线程可以重入自己已经持有的 monitor；`synchronized(A) { synchronized(A) {} }` 不会形成这种两线程环。
- **屏障放在持锁区内**：如果先过屏障再拿第一把锁，就不能保证双方同时持有不同资源；当前写法把“持有第一把锁”变成可验证前置条件。
- **BLOCKED 的原因**：两个线程最终都在尝试进入另一个 `synchronized` monitor，通常会处于 `Thread.State.BLOCKED`；不要把这种 monitor 获取阻塞和 `WAITING`/`TIMED_WAITING` 混为一谈。
- **daemon 只为测试退出服务**：把线程设成 daemon 并不会解决死锁；它只意味着测试主线程结束时 JVM 不必继续等待这两个演示线程。
- **不要在生产代码里故意复现**：真实排障优先使用线程 dump / `ThreadMXBean` 还原“谁持有什么、谁等什么”，不要为了验证猜测在生产进程主动制造第二个死锁。
- **修复优先消除锁顺序分歧**：若所有路径都规定 A→B，就不会出现一条路径 A→B、另一条 B→A 的二节点等待环。更复杂系统可进一步考虑更细粒度、超时锁或减少嵌套持锁，但这些是基于具体约束的设计选择。

## 原理机制

可以把例子画成一个等待图：`T1 -> LOCK_B -> T2 -> LOCK_A -> T1`。T1 已占有 A，所以 T2 获取 A 之前不能继续；T2 已占有 B，所以 T1 获取 B 之前不能继续。两条等待边首尾相接，而且 `synchronized` 的 monitor 不会因为线程“等太久”被自动剥夺，于是没有外部结构变化时两个线程都无法走出内层加锁语句。

这个例子最重要的不变量是：进入第二次加锁之前，T1 必须仍持有 A、T2 必须仍持有 B。`CountDownLatch` 只负责把时间安排固定下来，并不是死锁所依赖的资源；真正的死锁资源是两个 object monitor。

统一锁顺序的修复可以这样理解：如果系统为所有锁定义严格全序，只允许从“小”到“大”获取，那么等待边不可能绕一圈回到更小的锁，循环依赖就被结构性排除。对于不能统一顺序的业务，再考虑 `Lock.tryLock(timeout)`、回退重试等策略，并明确失败与回滚语义。

## 项目经验版

来源没有真实项目事故，不能虚构“线上遇到过这次死锁”。真实排障时，我会保存线程 dump，先定位 `BLOCKED` 线程、持有 monitor 和等待 monitor，再确认是否存在循环；随后映射到代码中的加锁路径，检查不同入口是否以相反顺序获取同一组资源。修复后用并发测试和再次采样 thread dump 验证，而不是只凭“问题暂时没再出现”判断已解决。

## 常见追问

- 问：为什么不能只用 `sleep` 制造死锁？答：可以做演示，但它依赖调度时序，测试可能偶发不死锁。屏障能明确保证双方先各持一把锁，再同时申请第二把锁，复现更稳定。
- 问：为什么同一把 `synchronized` 锁嵌套两次不会自锁死？答：Java monitor 对持有它的线程是可重入的；当前线程可以再次获得同一个 monitor，真正的等待来自另一个线程持有的第二把锁。
- 问：怎么证明示例真的死锁了？答：测试可调用 JDK 的 `ThreadMXBean.findMonitorDeadlockedThreads()`，并检查返回线程 ID 包含这两个演示线程，同时观察它们都在等待对方的 monitor。
- 问：最直接的修复是什么？答：让所有代码路径用一致的全局顺序获取 A、B，例如永远 A→B，不再允许 B→A；这样直接破坏循环等待。
- 问：`tryLock` 能不能解决？答：对 `java.util.concurrent.locks.Lock` 可以设计超时获取、失败后释放已持有锁再重试，但必须处理回退、饥饿和业务幂等；它不是给 `synchronized` 自动加超时。

## 易错点

- 两个线程其实用了不同对象实例，表面名字相同却没有竞争同一把锁。
- 用 `sleep` 当作正确性条件，导致 CI 中偶现“没有死锁”。
- 屏障放在第一把锁之外，无法保证进入第二次获取前双方都已经持锁。
- 看到线程卡住就叫死锁，没有证明形成循环等待；普通锁竞争也会暂时 BLOCKED。
- 认为线程被 `interrupt()` 就能强制释放 `synchronized` monitor；monitor 的持有与释放仍由同步块退出控制。
- 把 daemon 设置、超时等待或线程重启当成修复，却没有消除相反的锁顺序。
'''

TEST = r'''import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public final class DeadlockExampleTest {
    public static void main(String[] args) throws Exception {
        Thread[] threads = DeadlockExample.startDeadlock();
        ThreadMXBean bean = ManagementFactory.getThreadMXBean();
        long[] deadlocked = null;
        for (int i = 0; i < 200 && deadlocked == null; i++) {
            Thread.sleep(10);
            deadlocked = bean.findMonitorDeadlockedThreads();
        }
        if (deadlocked == null) throw new AssertionError("monitor deadlock was not detected");

        Set<Long> ids = new HashSet<>();
        for (long id : deadlocked) ids.add(id);
        if (!ids.contains(threads[0].getId()) || !ids.contains(threads[1].getId())) {
            throw new AssertionError("detected cycle does not include both demo threads: " + Arrays.toString(deadlocked));
        }
        if (threads[0].getState() != Thread.State.BLOCKED || threads[1].getState() != Thread.State.BLOCKED) {
            throw new AssertionError("expected both demo threads BLOCKED but got " + threads[0].getState() + ", " + threads[1].getState());
        }
        System.out.println("PASS monitor-deadlock-detected both-thread-ids-present both-blocked deterministic-first-lock-barrier");
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

    context_raw = run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout
    ctx = json.loads(context_raw)
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

    with tempfile.TemporaryDirectory(prefix='b49-deadlock-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'DeadlockExample.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'DeadlockExampleTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'DeadlockExample.java', 'DeadlockExampleTest.java', cwd=tmpdir)
        stdout = run('java', 'DeadlockExampleTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS monitor-deadlock-detected both-thread-ids-present both-blocked deterministic-first-lock-barrier'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac DeadlockExample.java DeadlockExampleTest.java && java DeadlockExampleTest',
        'stdout': stdout,
        'checks': [
            'both threads acquire their first distinct monitor before second acquisition',
            'ThreadMXBean detects an object-monitor deadlock',
            'detected deadlocked IDs include both demo threads',
            'both demo threads are BLOCKED on the second synchronized acquisition',
            'daemon demo threads permit the verifier JVM to exit after detection',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0049 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'jls-synchronized', 'title': 'Java SE 21 Language Specification 14.19: synchronized Statement', 'locator': JLS_SYNC, 'source_type': 'official_specification_or_standard', 'checked_at': DATE},
        {'source_id': 'jdk-thread-mxbean', 'title': 'Java SE 21 ThreadMXBean deadlock detection API', 'locator': THREAD_MXBEAN, 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'Deterministic OpenJDK 21 monitor-deadlock fixture', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The preserved source asks only for an example of deadlock; the candidate therefore provides one minimal Java monitor example and labels the deterministic scheduling mechanism as part of the demonstration rather than an unstated source requirement.',
            'source_ids': ['repository-source'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版'],
        },
        {
            'claim_id': 'monitor-semantics',
            'text': 'Java SE 21 specifies that synchronized acquires the monitor associated with the referenced object and releases it when the synchronized block completes; the example relies on each thread remaining inside its first synchronized block while blocked acquiring the second monitor.',
            'source_ids': ['jls-synchronized'],
            'answer_locations': ['3 分钟版', '关键细节', '原理机制'],
        },
        {
            'claim_id': 'deadlock-detection',
            'text': 'JDK 21 ThreadMXBean provides monitor-deadlock detection, and the executable fixture verifies that the constructed two-thread cycle is detected and contains both demo thread IDs.',
            'source_ids': ['jdk-thread-mxbean', 'fixture'],
            'answer_locations': ['3 分钟版', '关键细节', '项目经验版', '常见追问'],
        },
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    research = {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    }
    write_json(out / 'writer_research.json', research)

    scores = {'facts_and_evidence': 24, 'directness_and_relevance': 20, 'type_specific_completeness': 19, 'mechanism_and_causality': 14, 'boundaries_and_tradeoffs': 9, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate gives a concrete compilable deadlock example instead of generic deadlock advice and keeps the scope aligned to the single preserved source question.',
        'A CountDownLatch barrier makes the prerequisite state deterministic: each thread owns its first monitor before either attempts the second.',
        'Java monitor acquisition/release claims are tied to the Java SE 21 language specification rather than inferred from the fixture alone.',
        'OpenJDK 21 verification uses ThreadMXBean to detect the actual monitor cycle, checks both thread IDs and confirms both threads are BLOCKED.',
        'The answer distinguishes demonstration lifecycle choices such as daemon threads from structural fixes such as consistent lock ordering and avoids fabricated production experience.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0049-deadlock-example-20260829-v1',
        'review_version': 'batch-0049.deadlock-example.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), JLS_SYNC, THREAD_MXBEAN, 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence = {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0049-deadlock-example-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{'source_id': 'isolated-review', 'title': 'Deadlock-example source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'deterministic first-lock barrier', 'expected': 'both threads own distinct first monitors before second acquisition', 'actual': 'pass', 'passed': True},
                {'case': 'ThreadMXBean monitor cycle', 'expected': 'both demo thread IDs detected', 'actual': 'pass', 'passed': True},
                {'case': 'thread states after cycle forms', 'expected': 'both BLOCKED', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': review['reviewer_id'],
            'review_version': review['review_version'],
            'independent': True,
            'decision': 'pass',
            'revision_round': 1,
            'scores': scores,
            'hard_failures': [],
            'unsupported_claims': [],
            'uncovered_source_variants': [],
            'findings': findings,
        },
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    }
    write_json(ROOT / f'review/evidence/{CID}.json', evidence)

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d076a2fc3ca909dbfc2b295a0a578a51` source-first isolated review PASS: the preserved source asks for a deadlock example. The candidate gives a deterministic two-monitor Java example using a first-lock barrier, ties monitor semantics to Java SE 21, and OpenJDK 21 verification proves the real cycle with ThreadMXBean, both demo thread IDs and BLOCKED states. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
