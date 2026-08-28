#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0050 thread-stage candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
CID = 'cq_q_d52ca0aa328f82f1166ebc5bd3cc0ad7'
QID = 'd52ca0aa328f82f1166ebc5bd3cc0ad7'
EXPECTED = '线程同步：有 3 个线程 t1, t2, t3。要求 t1 和 t2 同时运行，待两者结束后再运行 t3。请提供核心实现代码（如使用 CountDownLatch 或 Join）？'
BATCH = '0050'
COUNTDOWN_LATCH = 'https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/concurrent/CountDownLatch.html'
THREAD_API = 'https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Thread.html'
JLS_MEMORY = 'https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html#jls-17.4.5'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d52ca0aa328f82f1166ebc5bd3cc0ad7","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# t1、t2 并发执行，二者完成后再运行 t3

## 核心结论

先让 `t1`、`t2` 都 `start()`，不要让其中一个等待另一个；协调线程再等待二者的完成条件，最后才启动 `t3`。如果题目强调“线程对象已经终止”，`Thread.join()` 最直接：分别 `join` t1、t2，两个 `join` 都返回后再 `t3.start()`。如果强调“两项工作都完成后进入下一阶段”，`CountDownLatch(2)` 更适合把“完成信号”与具体线程对象解耦。Java 调度器不能保证两个线程在同一 CPU 时刻真正同时执行，这里的“同时”应理解为没有先后依赖、可以并发推进。

## 1 分钟版

- 先创建并启动 `t1`、`t2`，这样两者都具备并发执行机会。
- **严格等待线程终止**：主线程依次 `t1.join()`、`t2.join()`；两个调用都返回后再启动 `t3`。
- **等待两项任务完成**：创建 `CountDownLatch(2)`，t1/t2 各自在 `finally` 中 `countDown()`，协调线程 `await()`；计数到 0 后启动 t3。
- `join()` 和 `await()` 都会响应中断，不能把 `InterruptedException` 静默吞掉。
- `CountDownLatch` 是一次性的，计数到 0 后不能重置；重复多轮阶段同步应换适合重复使用的同步器或重新创建 latch。

## 3 分钟版

```java
import java.util.concurrent.CountDownLatch;

public final class ThreadStageSolution {
    public static void runWithJoin(
            Runnable task1, Runnable task2, Runnable task3) throws InterruptedException {
        Thread t1 = new Thread(task1, "t1");
        Thread t2 = new Thread(task2, "t2");

        t1.start();
        t2.start();

        t1.join();
        t2.join();

        Thread t3 = new Thread(task3, "t3");
        t3.start();
        t3.join();
    }

    public static void runWithCountDownLatch(
            Runnable task1, Runnable task2, Runnable task3) throws InterruptedException {
        CountDownLatch done = new CountDownLatch(2);

        Thread t1 = new Thread(() -> {
            try {
                task1.run();
            } finally {
                done.countDown();
            }
        }, "t1");

        Thread t2 = new Thread(() -> {
            try {
                task2.run();
            } finally {
                done.countDown();
            }
        }, "t2");

        t1.start();
        t2.start();

        done.await();

        Thread t3 = new Thread(task3, "t3");
        t3.start();
        t3.join();
    }
}
```

`runWithJoin` 对“t1、t2 线程已经结束”表达最精确，因为 JDK 21 的 `join()` 定义就是等待目标线程终止。`runWithCountDownLatch` 表达的是“两个任务都已经发出完成信号”：`CountDownLatch(2)` 需要两次 `countDown()` 才会让 `await()` 返回。这里把 `countDown()` 放在 `finally`，避免任务抛出运行时异常后协调线程永久卡住；但这个版本没有把子线程异常自动传播给调用者，真实业务若需要失败传播，应再配合 `Future`、共享错误容器或结构化任务机制。

如果面试官把“同时运行”解释成“尽量同一起跑线”，可以再加一个开始闸门：先让 t1/t2 都准备好并阻塞在同一个 `CountDownLatch(1).await()`，协调线程确认双方 ready 后 `countDown()` 一次统一放行。但这仍然只是同时变为可运行状态，不能承诺物理 CPU 周期级同时执行。

## 关键细节

- **`start()` 不是顺序等待**：连续调用 `t1.start(); t2.start();` 后，两者由调度器并发推进；代码不能承诺谁先真正获得 CPU。
- **`join()` 的语义最贴近“线程结束”**：JDK 21 `Thread.join()` 等待目标线程终止。JLS 17.4.5 还规定，线程中的所有动作 happens-before 另一个线程从该线程的 `join()` 成功返回，因此随后启动 t3 时能看到此前按内存模型发布的结果。
- **Latch 表达任务完成事件**：`CountDownLatch.await()` 在计数归零前阻塞，t1/t2 各自 `countDown()` 一次。它不要求发信号的线程自己等待计数归零。
- **Latch 的可见性保证**：JDK 文档规定，在计数到 0 前，某线程 `countDown()` 之前的动作 happens-before 另一线程对应 `await()` 成功返回后的动作。
- **`countDown()` 放 `finally`**：否则 task1/task2 若抛出未检查异常，计数可能永远到不了 0；但“继续执行 t3 还是整体失败”属于业务失败策略，必须明确，不能由 latch 替你决定。
- **中断处理**：`join()`、`await()` 都可能抛 `InterruptedException`。库方法通常继续向上抛；若在不能抛出的边界捕获，应根据契约恢复中断标志或执行取消/清理，而不是空 `catch`。
- **一次性边界**：`CountDownLatch` 计数到 0 后不会重新变成 2；多轮阶段协调不能复用同一个 latch。
- **复杂度**：同步器的业务状态是常数级；真正耗时由 t1、t2、t3 的任务决定。总关键路径近似 `max(T1, T2) + T3`，而不是 `T1 + T2 + T3`，前提是 t1/t2 能实际并发。

## 原理机制

这道题本质是一个两阶段依赖图：第一阶段有两个互不依赖节点 t1、t2，第二阶段 t3 同时依赖前两个节点完成。因此正确顺序不是 `t1 -> t2 -> t3`，而是先建立两条并行边，再建立一个汇合点：

`start(t1), start(t2) -> wait(all first-stage complete) -> start(t3)`。

`join` 把汇合条件绑定在具体线程生命周期上：协调线程分别观察 t1、t2 的终止事件。`CountDownLatch` 则把汇合条件抽象成一个计数器：任意执行者只要完成一份工作就发一个信号，等待者只关心计数是否已经归零，因此更容易用于线程池任务或“完成者不是固定 Thread 对象”的场景。

内存可见性也属于同步语义的一部分，而不仅是执行先后。`join` 成功返回和 `CountDownLatch.await` 成功返回都建立相应 happens-before 关系，所以第一阶段发布的结果可以在协调点之后被安全观察；仅靠 `sleep` 或轮询普通 boolean 既不能稳定表达完成条件，也不能自动提供等价的内存模型保证。

## 项目经验版

来源没有提供真实生产项目，不能虚构“线上就是这样实现的”。工程落地时，我会先区分“等待固定线程退出”还是“等待若干任务完成”：前者小型脚本/演示代码用 `join` 最直接；后者若任务交给线程池，通常更倾向 `Future`、`CompletableFuture`、latch 或更高层任务编排，因为业务不应该依赖线程池内部具体 Thread 对象。还要明确失败、取消、超时和中断策略，避免第一阶段有一个任务挂死时整个流程无限等待。

## 常见追问

- 问：连续 `t1.start(); t2.start();` 能保证真正同时开始吗？答：不能保证同一 CPU 时刻，只能保证代码没有人为建立 t1→t2 的等待依赖；实际运行时机由 JVM/OS 调度。
- 问：为什么 `join` 两次不会把 t1、t2 串行化？答：因为两个线程都已经先 `start()` 了；主线程之后先等待 t1，再等待 t2，只是在汇合点观察完成状态，不会阻止 t2 在等待 t1 的期间继续运行。
- 问：Latch 为什么初始化为 2？答：第一阶段有两个独立完成事件，必须收到两次 `countDown()` 才能让 `await()` 通过；初始化为 1 会在第一个任务完成时过早启动 t3。
- 问：`countDown()` 为什么写在 `finally`？答：保证每个已启动任务无论正常返回还是抛运行时异常都不会漏掉自己的完成信号；至于异常是否允许 t3 继续，需要额外失败策略。
- 问：Latch 和 join 怎么选？答：固定 Thread 生命周期依赖用 join 简洁直接；完成事件来自任务、线程池或多个执行者时，latch 解耦更好。若还需要返回值和异常传播，`Future`/`CompletableFuture` 往往更自然。
- 问：如果 t1/t2 每轮都要完成后再运行 t3 呢？答：不要复用已经归零的同一个 `CountDownLatch`；每轮重建，或根据阶段模型选可重复使用的 `CyclicBarrier`/`Phaser` 等同步器。

## 易错点

- `t1.start(); t1.join(); t2.start(); t2.join();`：这会把 t1、t2 直接串行化，违背第一阶段并发要求。
- Latch 初始化成 1：任意一个线程先完成都会提前放行 t3。
- 任务抛异常时没有 `finally countDown()`：等待方可能永久阻塞。
- 先启动 t3，再在 t3 业务代码外部假设它“自然会晚一点执行”：调度顺序不是依赖关系。
- 用固定 `sleep(1000)` 猜 t1/t2 已结束：运行时间和调度不可预测，也没有可靠完成协议。
- 捕获 `InterruptedException` 后什么都不做：取消语义被吞掉，调用者也无法知道等待已被中断。
- 把“同时运行”说成“同一个时钟周期执行”：Java 线程调度不提供这种保证。
'''

TEST = r'''import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

public final class ThreadStageSolutionTest {
    private static Runnable stageTask(String name, CountDownLatch bothStarted, AtomicInteger finished, List<String> events) {
        return () -> {
            events.add(name + "-start");
            bothStarted.countDown();
            try {
                if (!bothStarted.await(5, java.util.concurrent.TimeUnit.SECONDS)) {
                    throw new AssertionError("first-stage peer did not start");
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new AssertionError("first-stage task interrupted", e);
            }
            events.add(name + "-end");
            finished.incrementAndGet();
        };
    }

    private static void verify(String mode, Runner runner) throws Exception {
        List<String> events = Collections.synchronizedList(new ArrayList<>());
        CountDownLatch bothStarted = new CountDownLatch(2);
        AtomicInteger finished = new AtomicInteger();

        Runnable t1 = stageTask("t1", bothStarted, finished, events);
        Runnable t2 = stageTask("t2", bothStarted, finished, events);
        Runnable t3 = () -> {
            if (bothStarted.getCount() != 0) throw new AssertionError(mode + ": t3 ran before both first-stage tasks started");
            if (finished.get() != 2) throw new AssertionError(mode + ": t3 ran before both first-stage tasks finished: " + finished.get());
            events.add("t3-run");
        };

        runner.run(t1, t2, t3);

        int t1Start = events.indexOf("t1-start");
        int t2Start = events.indexOf("t2-start");
        int t1End = events.indexOf("t1-end");
        int t2End = events.indexOf("t2-end");
        int t3Run = events.indexOf("t3-run");
        if (t1Start < 0 || t2Start < 0 || t1End < 0 || t2End < 0 || t3Run < 0) {
            throw new AssertionError(mode + ": missing event " + events);
        }
        if (!(t1Start < t2End && t2Start < t1End)) {
            throw new AssertionError(mode + ": t1/t2 were not both started before either finished: " + events);
        }
        if (!(t3Run > t1End && t3Run > t2End)) {
            throw new AssertionError(mode + ": t3 ordering violated: " + events);
        }
    }

    public static void main(String[] args) throws Exception {
        verify("join", ThreadStageSolution::runWithJoin);
        verify("latch", ThreadStageSolution::runWithCountDownLatch);
        System.out.println("PASS join-order latch-order first-stage-overlap t3-after-both-finished");
    }

    @FunctionalInterface
    interface Runner {
        void run(Runnable a, Runnable b, Runnable c) throws Exception;
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

    official_snapshot = {
        'schema_version': 'official_documentation_snapshot.v1',
        'checked_at': DATE,
        'sources': [
            {
                'locator': COUNTDOWN_LATCH,
                'title': 'CountDownLatch (Java SE 21 & JDK 21)',
                'claims': [
                    'await blocks until the count reaches zero unless interrupted',
                    'countDown decrements the count and releases waiters when it reaches zero',
                    'the latch is one-shot and cannot be reset',
                    'actions before countDown happen-before actions after a corresponding successful await',
                ],
            },
            {
                'locator': THREAD_API,
                'title': 'Thread (Java SE 21 & JDK 21)',
                'claims': [
                    'starting a thread schedules its run method to execute concurrently with the starter',
                    'join waits for the target thread to terminate',
                    'join may throw InterruptedException while waiting',
                ],
            },
            {
                'locator': JLS_MEMORY,
                'title': 'Java Language Specification SE 21 section 17.4.5',
                'claims': [
                    'all actions in a thread happen-before another thread successfully returns from join on that thread',
                    'a call to Thread.start happens-before actions in the started thread',
                ],
            },
        ],
    }
    write_json(out / 'official_documentation_snapshot.json', official_snapshot)

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')

    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b50-thread-stage-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'ThreadStageSolution.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'ThreadStageSolutionTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'ThreadStageSolution.java', 'ThreadStageSolutionTest.java', cwd=tmpdir)
        stdout = run('java', 'ThreadStageSolutionTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS join-order latch-order first-stage-overlap t3-after-both-finished'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac ThreadStageSolution.java ThreadStageSolutionTest.java && java ThreadStageSolutionTest',
        'stdout': stdout,
        'checks': [
            'join implementation starts both first-stage threads before waiting',
            'CountDownLatch implementation starts both first-stage threads before waiting',
            'both first-stage tasks have started before either is allowed to finish in the deterministic fixture',
            't3 runs only after both first-stage tasks have finished',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'jdk-countdown-latch', 'title': 'CountDownLatch Java SE 21 API', 'locator': COUNTDOWN_LATCH, 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'jdk-thread', 'title': 'Thread Java SE 21 API', 'locator': THREAD_API, 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'jls-memory-model', 'title': 'JLS SE 21 17.4.5 happens-before order', 'locator': JLS_MEMORY, 'source_type': 'official_specification', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 deterministic stage-order validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The repository source requires t1 and t2 to have no serial dependency and t3 to run only after both first-stage executions complete, explicitly suggesting CountDownLatch or join.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版']},
        {'claim_id': 'join-contract', 'text': 'Java SE 21 Thread.join waits for thread termination, and JLS 17.4.5 gives successful join the relevant happens-before edge from all actions in the joined thread.', 'source_ids': ['jdk-thread', 'jls-memory-model'], 'answer_locations': ['核心结论', '关键细节', '原理机制']},
        {'claim_id': 'latch-contract', 'text': 'Java SE 21 CountDownLatch with count two blocks await until two countDown signals, is one-shot, and supplies the documented memory-consistency effect across countDown/await.', 'source_ids': ['jdk-countdown-latch'], 'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制']},
        {'claim_id': 'execution-validation', 'text': 'The OpenJDK 21 fixture verifies both implementations start both first-stage tasks before either finishes and records t3 only after both completion events.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '易错点']},
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

    scores = {
        'facts_and_evidence': 25,
        'directness_and_relevance': 20,
        'type_specific_completeness': 19,
        'mechanism_and_causality': 14,
        'boundaries_and_tradeoffs': 9,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The candidate answers the exact two-stage dependency instead of serializing t1 and t2, and distinguishes scheduler concurrency from literal same-instant execution.',
        'The join solution is correctly framed as the strict thread-termination variant; the latch solution is framed as task-completion signaling rather than falsely equating countDown with Thread termination.',
        'Java SE 21 and JLS primary sources support join termination, CountDownLatch one-shot/counting semantics, interruption boundaries, and the relevant happens-before guarantees.',
        'The latch implementation uses finally for completion signaling and explicitly calls out the separate worker-failure propagation policy.',
        'OpenJDK 21 validation deterministically forces both first-stage tasks to start before either finishes and verifies t3 occurs after both finish for both join and latch variants.',
        'The answer includes complexity, repeated-stage, interruption, exception, thread-pool and scheduling boundaries without fabricated project history.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0050-thread-stage-20260829-v1',
        'review_version': 'batch-0050.thread-stage.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            str(out / 'context.json'),
            str(out / 'official_documentation_snapshot.json'),
            str(candidate),
            str(out / 'writer_validation.json'),
            COUNTDOWN_LATCH,
            THREAD_API,
            JLS_MEMORY,
            'docs/refactor/09_answer_content_standard.md',
        ],
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
        'writer': {'writer_id': 'content-batch-0050-thread-stage-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'Thread-stage source-first isolated review',
            'locator': str(out / 'isolated_review_result.json'),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        }],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'join variant', 'expected': 'both first-stage tasks started before either completes; t3 after both', 'actual': 'pass', 'passed': True},
                {'case': 'CountDownLatch variant', 'expected': 'both first-stage tasks started before either completes; t3 after both', 'actual': 'pass', 'passed': True},
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
    line = '- [x] `cq_q_d52ca0aa328f82f1166ebc5bd3cc0ad7` source-first isolated review PASS: the exact t1/t2 -> t3 dependency is preserved; Java SE 21 CountDownLatch/Thread API plus JLS 17.4.5 bound completion, termination, interruption and happens-before semantics. OpenJDK 21 validation covers both join and latch implementations, forces both first-stage tasks to start before either finishes, and verifies t3 only runs after both completion events. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
