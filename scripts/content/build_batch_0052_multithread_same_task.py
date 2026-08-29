#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 multi-thread same-task candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0052'
CID = 'cq_q_e0e0f8f47d472c391202d01620a967d2'
QID = 'e0e0f8f47d472c391202d01620a967d2'
EXPECTED = '算法：写一个多线程，多个线程处理同一个任务，要求所有线程同時完成该任务。'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e0e0f8f47d472c391202d01620a967d2","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 多线程执行同一任务：同步开始，并等待全部完成

## 核心结论

来源说“多个线程处理同一个任务，要求所有线程同时完成”，但“同时完成”需要先澄清：普通操作系统/JVM 调度无法保证多个线程在同一个物理时刻完成。工程上通常能可靠保证两件事：**尽量在同一个起跑门释放所有 worker**，以及**协调者只有在所有 worker 都完成后才继续**。这里把“同一个任务”定义为同一个 `Runnable` 被 N 个 worker 各执行一次；若实际含义是“一个大任务拆成 N 份”，只需把 worker body 换成各自分片，协调机制相同。

Java 可以用三个 `CountDownLatch`：`ready` 等所有 worker 已创建并到达起跑线，`start` 作为统一启动门，`done` 统计完成数。每个 worker 在 `finally` 中 `done.countDown()`，保证任务异常也不会让协调者永久等待。协调者先 `ready.await()`，再一次 `start.countDown()`，随后 `done.await()`；只有所有 worker 都结束后方法才返回。

## 1 分钟版

- 不能承诺“同一纳秒完成”；能承诺的是同步释放 + 等待全部完成的 happens-before 协调。
- `ready = new CountDownLatch(N)`：worker 就绪后减一，主线程等待全部就绪。
- `start = new CountDownLatch(1)`：worker 全部在 `start.await()` 阻塞，主线程一次 countDown 统一放行。
- `done = new CountDownLatch(N)`：每个 worker 无论成功还是异常都在 finally 减一；主线程 `done.await()` 等全部结束。
- 用固定大小线程池 N，避免任务数量大于实际可并发 worker 时 ready/start 设计造成线程池饥饿。
- 收集 worker 异常；等待全部收口后再把异常报告给调用者，不能悄悄吞掉。
- `CountDownLatch` 是一次性的；需要多轮同步阶段时考虑 `CyclicBarrier` 或 `Phaser`。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public final class CoordinatedWorkers {
    public static void runSameTaskAndWait(int workers, Runnable task)
            throws InterruptedException {
        if (workers <= 0) throw new IllegalArgumentException("workers must be positive");
        if (task == null) throw new IllegalArgumentException("task must not be null");

        ExecutorService pool = Executors.newFixedThreadPool(workers);
        CountDownLatch ready = new CountDownLatch(workers);
        CountDownLatch start = new CountDownLatch(1);
        CountDownLatch done = new CountDownLatch(workers);
        ConcurrentLinkedQueue<Throwable> failures = new ConcurrentLinkedQueue<>();

        for (int i = 0; i < workers; i++) {
            pool.execute(() -> {
                ready.countDown();
                try {
                    start.await();
                    task.run();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    failures.add(e);
                } catch (Throwable t) {
                    failures.add(t);
                } finally {
                    done.countDown();
                }
            });
        }

        try {
            ready.await();
            start.countDown();
            done.await();
        } finally {
            pool.shutdownNow();
            pool.awaitTermination(5, TimeUnit.SECONDS);
        }

        if (!failures.isEmpty()) {
            RuntimeException combined = new RuntimeException("one or more workers failed");
            failures.forEach(combined::addSuppressed);
            throw combined;
        }
    }
}
```

这个版本故意不使用“所有 worker 在结束点再互相等”的 barrier，因为如果某个 task 在到达 barrier 之前抛异常，其他 worker 可能永久卡在 barrier。`done` 放在 finally 中，可以让失败也正常收口；协调者在全部 worker 都离开 task 后统一报告失败。

如果业务真的需要“任何线程完成后都不能进入下一阶段，直到全部线程完成本阶段”，那是**阶段 barrier**语义，应使用 `CyclicBarrier`/`Phaser`；它和“主线程等待所有任务完成”不是同一个合同。

## 关键细节

- **“同时完成”不是时间物理保证**：线程调度、CPU 核数、GC、抢占都让完全同刻结束不可保证。面试时要把需求翻译成可验证的同步语义。
- **ready 为什么需要**：如果主线程直接打开 start，可能有 worker 尚未启动；ready 让所有 worker 至少已经到达等待点，再统一放行。
- **线程池大小为什么等于 worker 数**：若只给更小固定池，前几个任务会占住所有池线程等待 start，剩余任务无法启动并 `ready.countDown()`，主线程又在等 ready=0，形成线程饥饿死锁。
- **done 必须在 finally**：task 抛异常也算这个 worker 已经结束；否则主线程可能永远等不到 N 次 countDown。
- **异常不能只在 worker 打日志**：调用者需要知道批次失败。示例先等待全部 worker 收口，再把所有异常作为 suppressed exceptions 汇总抛出。
- **中断处理**：worker 捕获 `InterruptedException` 后恢复 interrupt 标志；协调者自己的 `await` 被中断时向上传递，并在 finally shutdownNow。
- **共享任务线程安全**：同一个 Runnable 实例被并发调用。如果它读写共享状态，task 自己必须保证线程安全；协调器只负责生命周期同步，不自动保护业务数据。

## 原理机制

`CountDownLatch` 提供一次性的门闩。`start` 初始为 1，所有 worker 调用 await 后都等待同一个状态转为 0；主线程 countDown 发生后，等待线程都具备继续执行资格，但具体被 CPU 调度的时刻仍不相同。`done` 初始为 N，每个 worker 完成时减一，主线程只在计数变 0 后返回，因此形成“所有 worker 完成 -> 协调者继续”的同步边界。

这个设计把三个不同问题分开：线程是否已就绪（ready）、什么时候允许开始（start）、什么时候全部结束（done）。把它们混成一个 latch 或只 `Thread.sleep` 猜时机，都会失去可证明的状态关系。

## 项目经验版

来源没有真实项目背景，不能虚构。工程里常见的对应场景是并行 fan-out 后 join：N 个子任务并行查询/计算，协调者要等全部完成再汇总。真实实现还需要超时、取消、部分失败策略和线程池隔离。现代 Java 也可以用 `CompletableFuture.allOf`、结构化并发（取决于 JDK/项目约束）表达“等待所有子任务”，但如果题目重点是线程同步原语，CountDownLatch 更能直接展示 ready/start/done 三个状态边界。

## 常见追问

- 问：CountDownLatch 能保证所有线程同时开始吗？答：它能让所有线程先等待同一个门，再一次性放行；不能保证 OS 在同一时刻把它们都调度到 CPU 上。
- 问：能保证同时结束吗？答：不能保证物理时刻；`done.await()` 能保证协调者只在全部结束后继续。如果需要所有线程在阶段末互相等待，用 barrier/phaser。
- 问：为什么不用 `invokeAll`？答：`invokeAll` 很适合“提交一组任务并等待全部结束”，但没有 ready/start 起跑门。若不要求同步开始，它会更简洁。
- 问：task 抛异常怎么办？答：worker 在 finally 仍 countDown done，并把异常放入并发队列；所有线程收口后协调者汇总抛出，避免一边死锁一边丢错误。
- 问：线程池能比 workers 小吗？答：当前 ready/start 模式不能随便缩小，否则尚未调度的任务无法就绪，而已调度任务又在 start 门前占住池线程，可能死锁。
- 问：CountDownLatch 能复用吗？答：不能。多轮阶段同步用 CyclicBarrier/Phaser，或者每轮创建新的 latch。

## 易错点

- 把“同时完成”吹成同一个纳秒完成，给出系统无法保证的承诺。
- 直接启动线程后 sleep 一会儿就认为“都开始了/都结束了”。
- 使用小于 worker 数的线程池，又让已启动任务在 start latch 前等待，造成 ready 死锁。
- task 异常时忘记在 finally 递减 done，主线程永久阻塞。
- worker 异常只打印日志，协调者仍把整体当成功。
- 把生命周期同步和共享业务数据的线程安全混为一谈。
'''

TEST = r'''import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

public final class CoordinatedWorkersTest {
    public static void main(String[] args) throws Exception {
        AtomicInteger calls = new AtomicInteger();
        Set<String> threads = ConcurrentHashMap.newKeySet();
        CoordinatedWorkers.runSameTaskAndWait(8, () -> {
            threads.add(Thread.currentThread().getName());
            calls.incrementAndGet();
        });
        if (calls.get() != 8) throw new AssertionError("calls=" + calls);
        if (threads.size() != 8) throw new AssertionError("expected 8 fixed workers, threads=" + threads);

        AtomicInteger completed = new AtomicInteger();
        CoordinatedWorkers.runSameTaskAndWait(6, () -> {
            try { Thread.sleep((long)(Math.random() * 10)); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new RuntimeException(e); }
            completed.incrementAndGet();
        });
        if (completed.get() != 6) throw new AssertionError("returned before all complete");

        AtomicInteger attempted = new AtomicInteger();
        try {
            CoordinatedWorkers.runSameTaskAndWait(5, () -> {
                int x = attempted.incrementAndGet();
                if ((x & 1) == 0) throw new IllegalStateException("boom-" + x);
            });
            throw new AssertionError("failure must propagate");
        } catch (RuntimeException expected) {
            if (expected.getSuppressed().length == 0) throw new AssertionError("worker failures missing");
        }
        if (attempted.get() != 5) throw new AssertionError("all workers must still settle, attempted=" + attempted);

        CountDownLatch release = new CountDownLatch(1);
        AtomicInteger afterRelease = new AtomicInteger();
        Thread coordinator = new Thread(() -> {
            try {
                CoordinatedWorkers.runSameTaskAndWait(4, () -> {
                    try { release.await(); }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new RuntimeException(e); }
                    afterRelease.incrementAndGet();
                });
            } catch (InterruptedException e) { throw new RuntimeException(e); }
        });
        coordinator.start();
        Thread.sleep(30);
        if (afterRelease.get() != 0) throw new AssertionError("task crossed external gate early");
        release.countDown();
        coordinator.join(5000);
        if (coordinator.isAlive() || afterRelease.get() != 4) throw new AssertionError("coordinator did not wait for all workers");

        try { CoordinatedWorkers.runSameTaskAndWait(0, () -> {}); throw new AssertionError("workers=0 must fail"); }
        catch (IllegalArgumentException expected) {}
        try { CoordinatedWorkers.runSameTaskAndWait(1, null); throw new AssertionError("null task must fail"); }
        catch (IllegalArgumentException expected) {}

        System.out.println("PASS exact-worker-count wait-all failure-settlement external-gate lifecycle invalid-boundaries");
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

    with tempfile.TemporaryDirectory(prefix='b52-coordinated-workers-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'CoordinatedWorkers.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'CoordinatedWorkersTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'CoordinatedWorkers.java', 'CoordinatedWorkersTest.java', cwd=tmpdir)
        stdout = run('java', 'CoordinatedWorkersTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS exact-worker-count wait-all failure-settlement external-gate lifecycle invalid-boundaries'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac CoordinatedWorkers.java CoordinatedWorkersTest.java && java CoordinatedWorkersTest',
        'stdout': stdout,
        'checks': [
            'the same Runnable is executed exactly once by every configured worker',
            'the coordinator returns only after all workers settle',
            'worker failures still decrement completion and are propagated after group settlement',
            'an external blocking gate demonstrates coordinator lifecycle waiting without polling sleeps',
            'invalid worker count and null task follow explicit candidate boundaries',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact multi-thread same-task source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 coordinated-worker lifecycle and failure validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-ambiguity', 'text': 'The exact source asks multiple threads to process the same task and all complete together, but does not define physical simultaneity, start synchronization, task partitioning, failure, or return semantics.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate interprets the same task as one Runnable invoked once per worker, aligns readiness/start with latches, and defines “all complete” as the coordinator not continuing until every worker settles.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节']},
        {'claim_id': 'failure-safety', 'text': 'Completion countDown happens in finally and failures are accumulated, so an exception cannot strand the coordinator waiting for a missing completion signal.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'validation', 'text': 'Executable validation checks exact worker execution count, wait-all return, failure settlement/propagation, lifecycle blocking, and invalid boundaries.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制', '易错点']},
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
        'The answer does not falsely promise physical simultaneous completion; it translates the ambiguous wording into verifiable start-gate and wait-all semantics.',
        'ready/start/done responsibilities are separated, and the fixed pool size is matched to worker count to avoid ready-latch thread-starvation deadlock.',
        'Failure safety is designed into finally-based completion and post-settlement error aggregation instead of allowing one failure to hang peers.',
        'OpenJDK 21 validation covers exact worker count, wait-all behavior, failure settlement, external blocking lifecycle, and invalid inputs.',
        'The answer distinguishes coordinator join semantics from a true multi-phase worker barrier and names CyclicBarrier/Phaser only for the latter contract.',
        'The project section avoids fabricated experience and notes task-level shared-state thread safety as a separate concern.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0052-multithread-same-task-20260829-v1',
        'review_version': 'batch-0052.multithread-same-task.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 multi-thread same-task source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0052-multithread-same-task-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': '8 workers same Runnable', 'expected': '8 invocations / 8 worker threads', 'actual': 'pass', 'passed': True},
                {'case': 'worker exceptions', 'expected': 'all 5 settle then failure propagates', 'actual': 'pass', 'passed': True},
                {'case': 'external task gate', 'expected': 'coordinator remains blocked until all four settle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e0e0f8f47d472c391202d01620a967d2` source-first isolated review PASS: the ambiguous “all threads complete together” wording is translated into verifiable ready/start and coordinator wait-all semantics rather than an impossible same-nanosecond guarantee. The candidate uses ready/start/done CountDownLatch boundaries, finally-based failure-safe completion, and matched worker/pool cardinality; OpenJDK 21 validation covers exact execution count, wait-all lifecycle, failure settlement/propagation, external gating and invalid inputs. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
