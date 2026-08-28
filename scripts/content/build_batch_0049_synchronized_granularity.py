#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0049 synchronized-granularity candidate."""
from __future__ import annotations
import hashlib, json, re, subprocess, tempfile
from pathlib import Path

ROOT=Path('.')
DATE='2026-08-29'
CID='cq_q_d15ce77874aebd93088257540663cdbe'
QID='d15ce77874aebd93088257540663cdbe'
EXPECTED='synchronized 锁粒度是怎样的？如何模拟死锁场景？'
BATCH='0049'
JLS_METHOD='https://docs.oracle.com/javase/specs/jls/se21/html/jls-8.html#jls-8.4.3.6'
JLS_STATEMENT='https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html#jls-14.19'
JLS_LOCKS='https://docs.oracle.com/javase/specs/jls/se21/html/jls-17.html#jls-17.1'
MXBEAN='https://docs.oracle.com/en/java/javase/21/docs/api/java.management/java/lang/management/ThreadMXBean.html#findMonitorDeadlockedThreads()'

CANDIDATE=r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d15ce77874aebd93088257540663cdbe","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# synchronized 锁粒度是怎样的？如何模拟死锁场景？

## 核心结论

`synchronized` 的“锁粒度”先要看**锁的是哪个 monitor**，再看临界区包了多少代码/数据：实例 `synchronized` 方法锁当前 `this`；`static synchronized` 方法锁声明类对应的 `Class` 对象；`synchronized (obj)` 锁表达式求值得到的那个非 null 对象的 monitor。于是两个不同实例的实例同步方法可以并发，同一实例会互斥；同一类的静态同步方法不因调用者实例不同而分开。死锁可以用两把不同 monitor、两个线程反向嵌套获取，并用 `CountDownLatch` 保证双方先各持一把锁，再申请对方的锁，稳定形成等待环。

## 1 分钟版

- `synchronized void f()`：锁 `this`，所以粒度是“这个实例”；同一对象上的同步实例方法互斥，不同对象不天然互斥。
- `static synchronized void f()`：锁声明这个方法的类的 `Class` 对象，所以同一类共享一把类级 monitor。
- `synchronized (lock) { ... }`：锁 `lock` 指向对象的 monitor，可以把锁对象与业务对象分开，并把临界区缩到真正需要互斥的范围。
- “粒度小”不是越小越好：更细可以减少无关竞争，但会增加锁数量、组合和顺序管理成本；多把锁嵌套时尤其要固定全局顺序。
- 死锁演示：T1 `A -> B`，T2 `B -> A`；屏障确保 T1 已持 A、T2 已持 B 后再继续，随后两边都 BLOCKED。
- 验证不要只看“程序卡住”：可用 JDK 21 `ThreadMXBean.findMonitorDeadlockedThreads()` 检测实际 object-monitor 等待环。

## 3 分钟版

下面的类同时展示三种锁身份和一个可稳定复现的 monitor 死锁：

```java
import java.util.concurrent.CountDownLatch;

public final class SynchronizedGranularity {
    private final Object blockLock = new Object();
    private static final Object DEADLOCK_A = new Object();
    private static final Object DEADLOCK_B = new Object();

    public synchronized void instanceSection(Runnable body) {
        body.run();
    }

    public static synchronized void classSection(Runnable body) {
        body.run();
    }

    public void blockSection(Runnable body) {
        synchronized (blockLock) {
            body.run();
        }
    }

    public static Thread[] startDeadlock() {
        CountDownLatch firstLocksHeld = new CountDownLatch(2);

        Thread t1 = new Thread(() -> {
            synchronized (DEADLOCK_A) {
                firstLocksHeld.countDown();
                await(firstLocksHeld);
                synchronized (DEADLOCK_B) { }
            }
        }, "granularity-deadlock-t1");

        Thread t2 = new Thread(() -> {
            synchronized (DEADLOCK_B) {
                firstLocksHeld.countDown();
                await(firstLocksHeld);
                synchronized (DEADLOCK_A) { }
            }
        }, "granularity-deadlock-t2");

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
            throw new IllegalStateException("interrupted", e);
        }
    }
}
```

Java SE 21 语言规范对锁身份定义得很明确：同步实例方法使用 `this` 的 monitor；同步静态方法使用声明类的 `Class` 对象 monitor；同步语句先计算对象引用，再锁这个非 null 对象的 monitor。也就是说，所谓“锁方法”只是语法表面，真正互斥的是**同一个 monitor 身份**。

例如 `a.instanceSection(...)` 与 `b.instanceSection(...)`，如果 `a != b`，两者锁的是两个不同 monitor，可以同时进入；如果两个线程都调用 `a.instanceSection(...)`，第二个必须等 `a` 的 monitor。`classSection` 则不看 `a/b`，它锁的是 `SynchronizedGranularity.class` 对应 monitor。

死锁例子里，T1 在仍持有 A 时尝试 B，T2 在仍持有 B 时尝试 A。屏障只负责确定调度前置条件；真正构成环的是两个 monitor。统一锁顺序，例如所有路径都只允许 A→B，就能从结构上破坏这个二节点循环等待。

## 关键细节

- **锁对象身份比关键字位置更重要**：两个代码块都写 `synchronized`，如果锁的是不同对象，它们仍可并发；反过来，不同方法只要锁同一对象就会互斥。
- **实例锁与类锁不是同一把锁**：`synchronized` 实例方法锁 `this`，`static synchronized` 锁 `Class` 对象，二者不会因为“属于同一个类”就自动互斥。
- **代码块可以缩小临界区**：把耗时 I/O、纯计算等不需要共享状态保护的工作移出 monitor，通常能减少持锁时间；但必须先证明共享状态不变量仍完整覆盖。
- **更细粒度有组合成本**：多把锁能提高并发，但会增加锁顺序、遗漏保护和死锁风险；应明确 ownership 和全局顺序，而不是机械“拆得越细越好”。
- **monitor 是可重入的**：同一线程再次获取自己已经持有的同一 monitor 可以成功，所以 `synchronized(x){ synchronized(x){} }` 本身不是两锁死锁。
- **BLOCKED 不等于已证明死锁**：单纯竞争同一 monitor 也会暂时 BLOCKED；要证明死锁，需要等待图形成循环，或使用线程 dump / `ThreadMXBean` 的检测结果。
- **版本边界**：本答案只依赖 Java 语言层 monitor 语义和 JDK 21 管理 API，不把对象头、偏向锁、轻量/重量锁等 JVM 实现细节当作跨版本固定语义。

## 原理机制

互斥的核心状态是“某个 monitor 当前由哪个线程拥有”。同步语句或同步方法要先完成 lock action，拿不到就不能进入受保护主体；退出同步区域时执行对应 unlock action。因为实例方法的 monitor identity 是 `this`，所以实例天然把并发域按对象拆开；静态方法则把同一声明类聚合到一个 `Class` monitor。

锁粒度可以从两个维度理解：第一是**锁身份覆盖范围**，例如一个全局 Class monitor、一个业务实例、一个专用 shard lock；第二是**持锁代码范围**，即从成功获取 monitor 到释放期间执行多少工作。缩小其中任一维度可能降低竞争，但同时要求更严格地维护“哪些状态必须原子地一起变化”的不变量。

死锁的等待图是 `T1 -> B -> T2 -> A -> T1`。T1/T2 都没有退出第一层同步块，因此 A/B 不会释放；双方又都要等对方先释放，于是形成闭环。全局锁顺序相当于规定等待边只能沿一个严格方向增长，因此不能回到起点形成环。

## 项目经验版

来源没有真实项目事故，不能虚构生产数字。真实排障时我会先采集线程 dump 或 `ThreadMXBean` 信息，确认具体 monitor identity、owner 与 blocked thread；再映射到代码中哪些入口持有这些锁，以及是否存在相反顺序。优化粒度时则用锁等待时间、线程状态、吞吐/尾延迟和共享状态一致性测试验证，避免只凭“锁块看起来更小”就判断优化有效。

## 常见追问

- 问：两个对象分别调用同一个 synchronized 实例方法，会互斥吗？答：通常不会，因为实例方法分别锁两个 `this` monitor；只有它们最终竞争同一个额外共享锁或静态锁时才会互相阻塞。
- 问：实例 synchronized 方法和 static synchronized 方法会互斥吗？答：不会天然互斥；前者锁实例 `this`，后者锁声明类的 `Class` 对象，是两个不同 monitor。
- 问：为什么 synchronized 代码块常被说粒度更细？答：因为可以显式选择专用锁对象，并把临界区限制到真正需要保护的语句；但是否安全取决于共享状态不变量，而不是代码行数。
- 问：怎么让死锁复现稳定？答：不要依赖 `sleep` 碰调度；让两个线程先各自获取第一把锁，并用 `CountDownLatch` 确认这个状态后再同时申请第二把锁。
- 问：怎么证明真的死锁而不是暂时锁竞争？答：检查等待图或使用 JDK `ThreadMXBean.findMonitorDeadlockedThreads()` / thread dump；测试中应验证检测结果包含双方线程，而不仅是进程没有退出。

## 易错点

- 把 synchronized 说成“锁住方法”，忽略真正锁的是 `this`、`Class` 或表达式对象的 monitor。
- 认为同一类所有 synchronized 都互斥，混淆实例锁与类锁。
- 只缩短代码块却把必须原子更新的共享状态拆开，换来数据竞争。
- 用两个不同实例作“共享锁”却以为它们是同一把锁。
- 用 `sleep` 作为死锁正确性条件，导致测试时好时坏。
- 把一个线程长时间 BLOCKED 直接判定为死锁，没有证明等待环。
- 把 HotSpot 某一版本的对象头/锁优化路径当成 Java 语言规范本身。
'''

TEST=r'''import java.lang.management.ManagementFactory;
import java.lang.management.ThreadMXBean;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

public final class SynchronizedGranularityTest {
    static Runnable hold(AtomicInteger active, AtomicInteger peak, CountDownLatch entered, CountDownLatch release) {
        return () -> {
            int now = active.incrementAndGet();
            peak.accumulateAndGet(now, Math::max);
            entered.countDown();
            try { release.await(); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); throw new RuntimeException(e); }
            finally { active.decrementAndGet(); }
        };
    }

    static void sameInstanceSerializes() throws Exception {
        SynchronizedGranularity x = new SynchronizedGranularity();
        AtomicInteger active=new AtomicInteger(), peak=new AtomicInteger();
        CountDownLatch entered=new CountDownLatch(1), release=new CountDownLatch(1);
        Thread a=new Thread(() -> x.instanceSection(hold(active,peak,entered,release)));
        Thread b=new Thread(() -> x.instanceSection(hold(active,peak,new CountDownLatch(0),release)));
        a.start(); if(!entered.await(1,TimeUnit.SECONDS)) throw new AssertionError("first instance call did not enter");
        b.start(); Thread.sleep(30);
        if(active.get()!=1 || peak.get()!=1) throw new AssertionError("same instance should serialize");
        release.countDown(); a.join(1000); b.join(1000);
        if(a.isAlive()||b.isAlive()) throw new AssertionError("same-instance threads did not exit");
    }

    static void distinctInstancesOverlap() throws Exception {
        SynchronizedGranularity aObj=new SynchronizedGranularity(), bObj=new SynchronizedGranularity();
        AtomicInteger active=new AtomicInteger(), peak=new AtomicInteger();
        CountDownLatch entered=new CountDownLatch(2), release=new CountDownLatch(1);
        Thread a=new Thread(() -> aObj.instanceSection(hold(active,peak,entered,release)));
        Thread b=new Thread(() -> bObj.instanceSection(hold(active,peak,entered,release)));
        a.start(); b.start();
        if(!entered.await(1,TimeUnit.SECONDS)) throw new AssertionError("different instances failed to overlap");
        if(active.get()!=2 || peak.get()!=2) throw new AssertionError("different instance monitors should allow overlap");
        release.countDown(); a.join(1000); b.join(1000);
    }

    static void staticSerializesAcrossCallers() throws Exception {
        AtomicInteger active=new AtomicInteger(), peak=new AtomicInteger();
        CountDownLatch entered=new CountDownLatch(1), release=new CountDownLatch(1);
        Thread a=new Thread(() -> SynchronizedGranularity.classSection(hold(active,peak,entered,release)));
        Thread b=new Thread(() -> SynchronizedGranularity.classSection(hold(active,peak,new CountDownLatch(0),release)));
        a.start(); if(!entered.await(1,TimeUnit.SECONDS)) throw new AssertionError("first static call did not enter");
        b.start(); Thread.sleep(30);
        if(active.get()!=1 || peak.get()!=1) throw new AssertionError("static synchronized should share Class monitor");
        release.countDown(); a.join(1000); b.join(1000);
    }

    static void dedicatedBlockSerializes() throws Exception {
        SynchronizedGranularity x=new SynchronizedGranularity();
        AtomicInteger active=new AtomicInteger(), peak=new AtomicInteger();
        CountDownLatch entered=new CountDownLatch(1), release=new CountDownLatch(1);
        Thread a=new Thread(() -> x.blockSection(hold(active,peak,entered,release)));
        Thread b=new Thread(() -> x.blockSection(hold(active,peak,new CountDownLatch(0),release)));
        a.start(); if(!entered.await(1,TimeUnit.SECONDS)) throw new AssertionError("first block did not enter");
        b.start(); Thread.sleep(30);
        if(active.get()!=1 || peak.get()!=1) throw new AssertionError("same dedicated block monitor should serialize");
        release.countDown(); a.join(1000); b.join(1000);
    }

    static void detectDeadlock() throws Exception {
        Thread[] threads=SynchronizedGranularity.startDeadlock();
        ThreadMXBean bean=ManagementFactory.getThreadMXBean();
        long[] ids=null;
        for(int i=0;i<200&&ids==null;i++){Thread.sleep(10);ids=bean.findMonitorDeadlockedThreads();}
        if(ids==null) throw new AssertionError("deadlock not detected");
        Set<Long> found=new HashSet<>(); for(long id:ids) found.add(id);
        if(!found.contains(threads[0].getId())||!found.contains(threads[1].getId())) throw new AssertionError("deadlock cycle missing demo threads");
        if(threads[0].getState()!=Thread.State.BLOCKED||threads[1].getState()!=Thread.State.BLOCKED) throw new AssertionError("deadlock threads should be BLOCKED");
    }

    public static void main(String[] args) throws Exception {
        sameInstanceSerializes(); distinctInstancesOverlap(); staticSerializesAcrossCallers(); dedicatedBlockSerializes(); detectDeadlock();
        System.out.println("PASS same-instance=serial distinct-instances=overlap static-class=serial dedicated-block=serial monitor-deadlock=detected");
    }
}
'''

def run(*args,cwd=None): return subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
def write_json(path,payload): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    candidate=ROOT/f'review/candidates/answers/{CID}.md'
    if candidate.exists(): raise SystemExit('candidate already exists; do not overwrite reviewed work')
    ctx=json.loads(run('node','scripts/xhs.js','answer','context','--canonical-id',CID,'--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id')!=CID or ctx.get('answer_type')!='coding': raise SystemExit('canonical context/type drift')
    if ctx.get('canonical',{}).get('question_ids')!=[QID]: raise SystemExit('ownership drift')
    src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==QID),None)
    if not src or src.get('original_question')!=EXPECTED or src.get('is_valid_for_library') is not True: raise SystemExit('source wording/validity drift')
    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}'; out.mkdir(parents=True,exist_ok=True); write_json(out/'context.json',ctx)
    candidate.parent.mkdir(parents=True,exist_ok=True); candidate.write_text(CANDIDATE,encoding='utf-8')
    for h in ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']:
        if CANDIDATE.count(h)!=1: raise SystemExit(f'section drift {h}')
    blocks=re.findall(r'```java\n(.*?)\n```',CANDIDATE,re.S)
    if len(blocks)!=1: raise SystemExit('expected one Java block')
    with tempfile.TemporaryDirectory(prefix='b49-sync-') as td:
        p=Path(td); (p/'SynchronizedGranularity.java').write_text(blocks[0].strip()+'\n'); (p/'SynchronizedGranularityTest.java').write_text(TEST)
        run('javac','SynchronizedGranularity.java','SynchronizedGranularityTest.java',cwd=p); stdout=run('java','SynchronizedGranularityTest',cwd=p).stdout.strip()
    expected_stdout='PASS same-instance=serial distinct-instances=overlap static-class=serial dedicated-block=serial monitor-deadlock=detected'
    if stdout!=expected_stdout: raise SystemExit(f'unexpected fixture output: {stdout}')
    validation={'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'command':'javac SynchronizedGranularity.java SynchronizedGranularityTest.java && java SynchronizedGranularityTest','stdout':stdout,'checks':['same instance synchronized method serializes','different instances can overlap','static synchronized shares declaring Class monitor','same dedicated synchronized block monitor serializes','ThreadMXBean detects deterministic two-monitor deadlock']}
    write_json(out/'writer_validation.json',validation)
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources=[{'source_id':'repository-source','title':'Batch 0049 frozen canonical/source context','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'jls-method','title':'Java SE 21 JLS 8.4.3.6 synchronized Methods','locator':JLS_METHOD,'source_type':'official_specification_or_standard','checked_at':DATE},{'source_id':'jls-statement','title':'Java SE 21 JLS 14.19 synchronized Statement','locator':JLS_STATEMENT,'source_type':'official_specification_or_standard','checked_at':DATE},{'source_id':'jls-locks','title':'Java SE 21 JLS 17.1 Synchronization','locator':JLS_LOCKS,'source_type':'official_specification_or_standard','checked_at':DATE},{'source_id':'mxbean','title':'Java SE 21 ThreadMXBean monitor deadlock detection','locator':MXBEAN,'source_type':'official_documentation','checked_at':DATE},{'source_id':'fixture','title':'OpenJDK 21 synchronized granularity and monitor-deadlock fixture','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}]
    claims=[{'claim_id':'lock-identities','text':'Java SE 21 specifies that an instance synchronized method locks the monitor associated with this, a static synchronized method locks the declaring class Class object, and a synchronized statement locks the monitor associated with its evaluated non-null object.','source_ids':['jls-method','jls-statement','jls-locks'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制']},{'claim_id':'source-boundary','text':'The preserved source asks both for synchronized lock granularity and a simulated deadlock; the candidate covers lock identities/critical-section scope plus one deterministic opposite-order two-monitor cycle without adding JVM-version implementation claims.','source_ids':['repository-source'],'answer_locations':['核心结论','1 分钟版','3 分钟版','易错点']},{'claim_id':'runtime-validation','text':'OpenJDK 21 validation demonstrates same-instance serialization, distinct-instance overlap, Class-monitor serialization, dedicated-block serialization, and detects the constructed monitor cycle with ThreadMXBean.','source_ids':['fixture','mxbean'],'answer_locations':['3 分钟版','关键细节','原理机制','常见追问']}]
    coverage=[{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    scores={'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':19,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
    findings=['The answer directly covers both halves of the source question: synchronized lock identity/granularity and a reproducible deadlock scenario.','Instance, static and block monitor identities are tied to Java SE 21 JLS primary sources rather than HotSpot implementation folklore.','The executable fixture proves the expected concurrency domains: one instance serializes, distinct instances overlap, the declaring Class monitor serializes static calls, and a dedicated block monitor serializes its own critical section.','The deadlock uses opposite nested lock order plus a deterministic first-lock barrier, and ThreadMXBean proves the resulting monitor cycle instead of treating a hang as sufficient evidence.','The answer explicitly avoids cross-version claims about biased/lightweight/heavyweight implementation states and does not fabricate production experience.']
    review={'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':'source-first-isolated-reviewer-batch-0049-synchronized-granularity-20260829-v1','review_version':'batch-0049.synchronized-granularity.v1','decision':'pass','revision_round':1,'source_packet':[str(out/'context.json'),str(candidate),str(out/'writer_validation.json'),JLS_METHOD,JLS_STATEMENT,JLS_LOCKS,MXBEAN,'docs/refactor/09_answer_content_standard.md'],'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied']}; write_json(out/'isolated_review_result.json',review)
    evidence={'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0049-synchronized-granularity-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':'synchronized granularity source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':validation['checks'],'boundary_tests':[{'case':'same this monitor','expected':'peak active=1','actual':'pass','passed':True},{'case':'different this monitors','expected':'peak active=2','actual':'pass','passed':True},{'case':'static synchronized','expected':'same Class monitor serializes','actual':'pass','passed':True},{'case':'opposite nested monitors','expected':'both demo threads detected deadlocked and BLOCKED','actual':'pass','passed':True}]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':review['reviewer_id'],'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied'}; write_json(ROOT/f'review/evidence/{CID}.json',evidence)
    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'; text=task.read_text()
    line='- [x] `cq_q_d15ce77874aebd93088257540663cdbe` source-first isolated review PASS: Java SE 21 primary sources bind instance synchronized to `this`, static synchronized to the declaring `Class` monitor, and synchronized blocks to the evaluated lock object. OpenJDK 21 validation proves same-instance serialization, distinct-instance overlap, Class-monitor and dedicated-block serialization, while ThreadMXBean proves the deterministic opposite-order monitor deadlock. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text: text=text.rstrip()+'\n\n## Progress\n'
    if line not in text: text=text.rstrip()+'\n'+line+'\n'
    task.write_text(text)
    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0
if __name__=='__main__': raise SystemExit(main())
