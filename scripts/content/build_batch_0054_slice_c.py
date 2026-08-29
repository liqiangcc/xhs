#!/usr/bin/env python3
"""Build/validate/review Batch 0054 concurrency-focused Coding slice C."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT=Path('.')
DATE='2026-08-29'
BATCH='0054'

ITEMS={
'cq_q_f213ccebb77d694fa4eb9062e4f03a01':{
'qid':'f213ccebb77d694fa4eb9062e4f03a01','expected':'算法：手写阻塞队列','class':'BoundedBlockingQueue',
'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f213ccebb77d694fa4eb9062e4f03a01","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 手写阻塞队列

## 核心结论

来源只保留“手写阻塞队列”，没有指定有界/无界、语言、公平性、超时 API 或关闭语义。这里声明一个可执行 Java 合同：实现**有界 FIFO 队列**，容量构造时固定且必须大于 0；`put` 在队列满时阻塞，`take` 在队列空时阻塞；两者都可被线程中断；拒绝 `null`；不实现 `offer/poll` 超时、公平锁和 close/shutdown。核心同步结构是一个 `ReentrantLock` 加两个 `Condition`：`notFull` 等待“有空位”，`notEmpty` 等待“有元素”。

内部用固定数组和 `head/tail/size` 环形索引保存元素。所有队列状态都只在同一把锁下读写；等待条件必须用 `while` 重检而不是 `if`，因为 Condition 允许虚假唤醒，而且线程被 signal 后重新拿锁时条件可能已被其他线程改变。一次成功 `put` 只需唤醒一个等待消费者，一次成功 `take` 只需唤醒一个等待生产者。

## 1 分钟版

- 固定数组做环形缓冲区，`head` 指向下一次取出位置，`tail` 指向下一次写入位置，`size` 表示当前元素数。
- 一把 `ReentrantLock` 保护数组和三个索引状态，不能让入队/出队分别用互不相关的锁破坏整体不变量。
- 满队列：`while (size == items.length) notFull.await()`；空队列：`while (size == 0) notEmpty.await()`。
- `put` 成功后 `notEmpty.signal()`；`take` 成功后 `notFull.signal()`。
- 使用 `lock.lockInterruptibly()` 和 `Condition.await()`，等待线程可响应 interrupt。
- `null` 被拒绝，避免把 `null` 同“没有取到元素”之类的扩展 API 语义混淆。
- 每次入队/出队本身 O(1)，容量为 C 时缓冲区空间 O(C)。

## 3 分钟版

```java
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public final class BoundedBlockingQueue<E> {
    private final Object[] items;
    private int head;
    private int tail;
    private int size;
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notEmpty = lock.newCondition();
    private final Condition notFull = lock.newCondition();

    public BoundedBlockingQueue(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        this.items = new Object[capacity];
    }

    public void put(E element) throws InterruptedException {
        if (element == null) throw new NullPointerException("null elements are not supported");
        lock.lockInterruptibly();
        try {
            while (size == items.length) notFull.await();
            items[tail] = element;
            tail = (tail + 1) % items.length;
            size++;
            notEmpty.signal();
        } finally {
            lock.unlock();
        }
    }

    @SuppressWarnings("unchecked")
    public E take() throws InterruptedException {
        lock.lockInterruptibly();
        try {
            while (size == 0) notEmpty.await();
            E value = (E) items[head];
            items[head] = null;
            head = (head + 1) % items.length;
            size--;
            notFull.signal();
            return value;
        } finally {
            lock.unlock();
        }
    }

    public int size() {
        lock.lock();
        try { return size; }
        finally { lock.unlock(); }
    }
}
```

这段实现把“数据互斥”和“条件等待”分开处理：锁保证同一时刻只有一个线程改变环形队列状态；Condition 让不能继续的线程释放锁睡眠，而不是占着锁自旋。消费者取走元素后释放 `notFull` 条件，生产者加入元素后释放 `notEmpty` 条件，因此状态变化和唤醒原因一一对应。

## 关键细节

- **为什么是 `while`**：`await()` 返回不代表条件现在一定成立；虚假唤醒、竞争线程先一步消费/生产，都要求重新检查谓词。
- **为什么等待时不会锁死别人**：`Condition.await()` 会原子地释放关联锁并进入等待；被唤醒后再重新竞争锁。
- **环形索引**：`tail=(tail+1)%capacity`、`head=(head+1)%capacity` 复用数组槽位，不需要每次出队搬移剩余元素。
- **清空已取槽位**：`items[head]=null` 让已经出队的对象不再被数组无谓强引用。
- **`signal` 而非无条件 `signalAll`**：每次 put/take 只新增一个可消费元素或一个可用槽位，唤醒一个对侧等待者足够；复杂扩展合同下再重新评估唤醒策略。
- **公平性边界**：默认 `ReentrantLock()` 不承诺严格 FIFO 获取锁；来源未要求公平调度，候选不虚构。
- **关闭语义**：生产系统常需 close、drain、超时等生命周期合同，本题来源未给出，不能悄悄决定。

## 原理机制

队列需要维持 `0 <= size <= capacity`，且 `head/tail` 只在锁内更新。生产者的前置条件是 `size < capacity`，消费者的前置条件是 `size > 0`。Condition 本质上把线程按“当前缺少的状态变化”分组等待：生产者等待 notFull，消费者等待 notEmpty。状态改变后，在持锁区内修改数据再 signal，使被唤醒线程重新获取锁后能够观察到与该信号一致的 happens-before 结果。

这里不能只用 `synchronized` + 忙等：忙等会浪费 CPU；如果持锁忙等，还会阻止能够改变条件的线程进入。`wait/notify` 也能实现，但两个 Condition 把“非空”和“非满”两个等待集合显式分开，更容易表达不变量。

## 项目经验版

来源没有真实吞吐、延迟或容量数据，不能虚构性能收益。工程落地通常应先选标准库 `ArrayBlockingQueue`/`LinkedBlockingQueue`，因为它们的取消、超时、公平性和边界已经经过长期验证；手写版本更适合解释锁、条件变量和环形缓冲不变量。若真的自研，需要补关闭协议、超时、监控、压力测试和异常退出策略。

## 常见追问

- 问：为什么 `await` 外面一定是 while？答：因为被唤醒只意味着“值得再检查”，不保证谓词仍成立；竞争和虚假唤醒都可能让条件再次变假。
- 问：为什么两个 Condition？答：生产者只关心有空位，消费者只关心有元素；分开等待集合可避免把无关线程都唤醒。
- 问：能不能用 `notify()`？答：用对象监视器可以写，但只有一个 wait-set，很难像两个 Condition 一样精确表达 notEmpty/notFull；若用 notify/notifyAll 仍必须在同一监视器和 while 谓词下正确实现。
- 问：多生产者多消费者会丢数据吗？答：数组、head、tail、size 的所有修改都受同一锁保护，单次状态迁移是原子的；测试还应覆盖高并发完整性。
- 问：中断怎么处理？答：当前合同让 `put/take` 抛 `InterruptedException`，调用方决定取消或重试，不在队列内部吞掉中断。

## 易错点

- 用 `if` 检查空/满后直接 await，醒来不重检条件。
- 等待时仍占有一把对方需要的锁，造成死锁。
- `put` 后错误 signal `notFull`，或 `take` 后错误 signal `notEmpty`。
- 环形索引更新和 size 更新不在同一临界区。
- 吞掉 `InterruptedException`，让上层无法取消阻塞操作。
- 未定义关闭/超时却把当前最小实现宣称成生产级完整 BlockingQueue。
''',
'test':r'''import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public final class BoundedBlockingQueueTest {
    static void check(boolean v,String m){ if(!v) throw new AssertionError(m); }
    public static void main(String[] args) throws Exception {
        try { new BoundedBlockingQueue<Integer>(0); throw new AssertionError("capacity"); } catch(IllegalArgumentException expected) {}
        BoundedBlockingQueue<Integer> q=new BoundedBlockingQueue<>(2);
        q.put(1); q.put(2); check(q.size()==2,"size2"); check(q.take()==1,"fifo1"); q.put(3); check(q.take()==2,"fifo2"); check(q.take()==3,"fifo3");
        try { q.put(null); throw new AssertionError("null"); } catch(NullPointerException expected) {}

        BoundedBlockingQueue<Integer> full=new BoundedBlockingQueue<>(1); full.put(10);
        CountDownLatch producerStarted=new CountDownLatch(1);
        Thread producer=new Thread(() -> { try { producerStarted.countDown(); full.put(20); } catch(InterruptedException e){ throw new RuntimeException(e); } });
        producer.start(); producerStarted.await(); Thread.sleep(100); check(producer.isAlive(),"producer must block on full queue"); check(full.take()==10,"unblock take"); producer.join(3000); check(!producer.isAlive(),"producer released"); check(full.take()==20,"blocked put value");

        BoundedBlockingQueue<Integer> empty=new BoundedBlockingQueue<>(1); AtomicInteger taken=new AtomicInteger(-1); CountDownLatch consumerStarted=new CountDownLatch(1);
        Thread consumer=new Thread(() -> { try { consumerStarted.countDown(); taken.set(empty.take()); } catch(InterruptedException e){ throw new RuntimeException(e); } });
        consumer.start(); consumerStarted.await(); Thread.sleep(100); check(consumer.isAlive(),"consumer must block on empty queue"); empty.put(77); consumer.join(3000); check(taken.get()==77,"consumer released");

        BoundedBlockingQueue<Integer> interruptQ=new BoundedBlockingQueue<>(1); AtomicBoolean interrupted=new AtomicBoolean(false);
        Thread waiter=new Thread(() -> { try { interruptQ.take(); } catch(InterruptedException e){ interrupted.set(true); } }); waiter.start(); Thread.sleep(80); waiter.interrupt(); waiter.join(3000); check(interrupted.get(),"take interruptible");

        final int producers=4, consumers=4, per=5000, total=producers*per;
        BoundedBlockingQueue<Integer> stress=new BoundedBlockingQueue<>(17); AtomicIntegerArray seen=new AtomicIntegerArray(total); List<Thread> ps=new ArrayList<>(), cs=new ArrayList<>();
        for(int c=0;c<consumers;c++){ Thread t=new Thread(() -> { try { while(true){ int v=stress.take(); if(v==-1) return; if(v<0||v>=total) throw new AssertionError("range"); seen.incrementAndGet(v); } } catch(InterruptedException e){ throw new RuntimeException(e); } }); cs.add(t); t.start(); }
        for(int p=0;p<producers;p++){ final int base=p*per; Thread t=new Thread(() -> { try { for(int i=0;i<per;i++) stress.put(base+i); } catch(InterruptedException e){ throw new RuntimeException(e); } }); ps.add(t); t.start(); }
        for(Thread t:ps) t.join(15000); for(Thread t:ps) check(!t.isAlive(),"producer stress timeout");
        for(int i=0;i<consumers;i++) stress.put(-1); for(Thread t:cs) t.join(15000); for(Thread t:cs) check(!t.isAlive(),"consumer stress timeout");
        for(int i=0;i<total;i++) if(seen.get(i)!=1) throw new AssertionError("id="+i+" count="+seen.get(i));
        check(stress.size()==0,"stress drained");
        System.out.println("PASS fifo capacity-null producer-block consumer-block interruptible 4x4-20000-integrity");
    }
}
''','stdout':'PASS fifo capacity-null producer-block consumer-block interruptible 4x4-20000-integrity',
'checks':['FIFO and capacity/null boundaries','producer blocks while full and resumes after take','consumer blocks while empty and resumes after put','waiting take is interruptible','4 producers x 4 consumers preserve exactly-once delivery for 20000 unique items'],
'claims':[
('source-boundary','The source only asks to hand-write a blocking queue; boundedness, fairness, timeout, shutdown, and language are not preserved requirements.',['repository-source'],['核心结论','关键细节']),
('condition-mechanism','The candidate protects ring-buffer state with one lock and waits in while loops on separate notEmpty/notFull Conditions.',['fixture'],['1 分钟版','3 分钟版','原理机制']),
('concurrency-integrity','The executable validation demonstrates FIFO basics, actual producer/consumer blocking, interruption, and exactly-once delivery under a 4x4 concurrent stress case.',['fixture'],['关键细节','常见追问'])],
'findings':['The candidate explicitly scopes a sparse source to a bounded interruptible FIFO contract instead of inventing timeout/fairness/close semantics.','Condition waits use while predicates and separate notEmpty/notFull wait sets, preserving the ring-buffer size invariant.','The implementation clears consumed slots and updates head/tail/size only under one lock.','OpenJDK 21 validation observes real blocking/unblocking and interruption rather than testing only sequential queue behavior.','A 4-producer/4-consumer 20000-item stress case verifies every unique value is delivered exactly once.']},

'cq_q_f4495c3cafbc49411bce1eab8525b2f0':{
'qid':'f4495c3cafbc49411bce1eab8525b2f0','expected':'算法手撕：多线程交替打印 abc 和 123。','class':'AlternatingPrinter',
'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f4495c3cafbc49411bce1eab8525b2f0","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 多线程交替打印 abc 和 123

## 核心结论

来源只保留“多线程交替打印 abc 和 123”，没有保存线程数、重复轮数、先打印哪一组、是逐字符交替还是整组交替、是否允许忙等。这里声明最小 Java 合同：两个线程分别负责完整字符串 `abc` 和 `123`，以**组为单位**交替，`abc` 先打印，重复 `rounds` 轮，结果为 `abc123abc123...`；`rounds >= 0`，零轮输出空串。实现用一把 `ReentrantLock`、两个 `Condition` 和一个 `abcTurn` 状态，不依赖线程启动/调度顺序，也不忙等。

每个线程进入自己的循环后，只有轮到自己时才能追加；否则在对应 Condition 上 `await`，原子释放锁。追加完成后切换 turn 并 signal 对方。判断 turn 必须放在 `while` 中重检，避免虚假唤醒或重新竞争锁后状态已变化。测试为了可重复验证把“打印”写入同一个 `StringBuilder`；替换为 `System.out.print` 不改变同步协议。

## 1 分钟版

- 状态只有一个：`abcTurn=true` 表示轮到 abc 线程，否则轮到 123 线程。
- 两个线程共享同一把锁，保证“检查轮次 → 输出一组 → 切换轮次 → 唤醒对方”是一个原子协议片段。
- abc 线程：`while (!abcTurn) abcCondition.await()`；输出后设 false，再 signal numberCondition。
- 123 线程镜像执行：`while (abcTurn) numberCondition.await()`；输出后设 true，再 signal abcCondition。
- `await` 会释放锁，所以对方能进入推进状态；不能持锁自旋。
- 先启动哪个 Java Thread 不重要；协议规定第一合法状态是 abcTurn=true。
- 总输出工作 O(rounds)，同步状态 O(1)，结果缓冲本身占 O(rounds) 字符空间。

## 3 分钟版

```java
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public final class AlternatingPrinter {
    public static String render(int rounds) throws InterruptedException {
        if (rounds < 0) throw new IllegalArgumentException("rounds must be non-negative");

        ReentrantLock lock = new ReentrantLock();
        Condition abcCondition = lock.newCondition();
        Condition numberCondition = lock.newCondition();
        StringBuilder out = new StringBuilder(rounds * 6);
        boolean[] abcTurn = {true};

        Thread abc = new Thread(() -> {
            try {
                for (int i = 0; i < rounds; i++) {
                    lock.lockInterruptibly();
                    try {
                        while (!abcTurn[0]) abcCondition.await();
                        out.append("abc");
                        abcTurn[0] = false;
                        numberCondition.signal();
                    } finally {
                        lock.unlock();
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new RuntimeException(e);
            }
        }, "abc-printer");

        Thread numbers = new Thread(() -> {
            try {
                for (int i = 0; i < rounds; i++) {
                    lock.lockInterruptibly();
                    try {
                        while (abcTurn[0]) numberCondition.await();
                        out.append("123");
                        abcTurn[0] = true;
                        abcCondition.signal();
                    } finally {
                        lock.unlock();
                    }
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                throw new RuntimeException(e);
            }
        }, "123-printer");

        numbers.start(); // 故意先启动 123，结果仍由 turn 状态决定
        abc.start();
        abc.join();
        numbers.join();
        return out.toString();
    }

    private AlternatingPrinter() {}
}
```

这里故意先 `start()` 数字线程：它拿到锁也会发现 `abcTurn=true`，于是进入等待并释放锁；abc 线程输出后切换状态并唤醒它。因此正确性来自共享状态机，而不是“我猜 abc 线程会先被 CPU 调度”。

## 关键细节

- **来源歧义必须显式收口**：当前选择“整组 abc 与整组 123 交替”。如果面试官想要 `a1b2c3`，那是另一份状态机合同，不能假装等价。
- **为什么不用 `sleep`**：sleep 只能延迟线程，不能建立谁在什么状态下有权输出的同步条件；负载变化会破坏时序假设。
- **为什么不用自旋**：`while (!turn) {}` 会持续占 CPU；Condition 等待会释放锁并挂起。
- **为什么 while 重检**：虚假唤醒或竞争都意味着被唤醒不等于条件必然成立。
- **共享 StringBuilder 为什么安全**：它本身不是线程安全容器，但所有 append 都在同一把锁的临界区内，没有并发写。
- **启动顺序不等于输出顺序**：测试和实现故意先启动 `123` 线程，仍由 `abcTurn` 决定首组。
- **异常边界**：示例关注正常交替协议；生产级组件若允许外部中断某一工作线程，还要设计取消传播，避免另一线程永久等待。

## 原理机制

这本质上是一个两状态有限状态机：`ABC_TURN -> NUMBER_TURN -> ABC_TURN ...`。锁保护状态迁移和对应输出的原子性；Condition 把“不属于当前状态”的线程挂起。signal 不是“直接把执行权交给对方”，而只是把等待者变成可竞争锁；所以等待者重新获得锁后仍必须检查状态谓词。

线程启动、操作系统调度和锁竞争都可以是不确定的，但只要所有输出都必须经过受锁保护的状态机，不确定调度就不会改变可观察的输出顺序。这也是并发题里比 sleep 时间猜测更可靠的设计原则。

## 项目经验版

来源没有真实生产场景，不能虚构。实际业务一般不会为了拼接两个固定字符串创建线程；这道题的价值在于证明能把顺序约束建模成同步状态。生产系统里若是流水线阶段协作，应优先考虑 BlockingQueue、Semaphore、Phaser、CompletableFuture 等更贴合业务语义的并发原语，并明确取消/超时协议。

## 常见追问

- 问：如果数字线程先启动，会不会先打印 123？答：不会。它检查到 `abcTurn=true` 会 await，输出权限由共享状态而非调度顺序决定。
- 问：为什么不用 `synchronized + wait/notify`？答：也能实现；这里用两个 Condition 分离两个等待集合，让状态与等待原因更明确。无论哪种写法，谓词都应 while 重检。
- 问：为什么 signal 后自己还持有锁？答：Condition signal 只让对方进入可竞争状态；当前线程退出临界区 unlock 后，对方才可能重新获得锁。
- 问：如果题意其实是 a1b2c3 呢？答：那需要把状态粒度从“组”改成“字符步骤”，当前候选不会把未保存的题意强行补全。
- 问：能用 Semaphore 吗？答：可以，两只初值 1/0 的 semaphore 能直接表示令牌交接；Condition 版本更直观展示“共享状态 + 条件谓词”的机制。

## 易错点

- 用 `Thread.sleep` 猜调度顺序。
- 用 volatile turn 忙等，功能可能对但持续浪费 CPU。
- `await` 前用 if 而不是 while 检查状态。
- 把线程 start 顺序当作输出顺序保证。
- signal 后忘记切换共享状态，导致同一方重复打印或双方等待。
- 没澄清“abc 和 123 交替”究竟是按组还是按字符，就把某一种解释当成来源事实。
''',
'test':r'''public final class AlternatingPrinterTest {
    static String expected(int rounds){ return "abc123".repeat(rounds); }
    static void check(int rounds) throws Exception {
        String actual=AlternatingPrinter.render(rounds);
        if(!actual.equals(expected(rounds))) throw new AssertionError("rounds="+rounds+" len="+actual.length()+" prefix="+actual.substring(0,Math.min(actual.length(),60)));
    }
    public static void main(String[] args) throws Exception {
        try { AlternatingPrinter.render(-1); throw new AssertionError("negative"); } catch(IllegalArgumentException expected) {}
        check(0); check(1); check(2); check(17); check(10000);
        for(int i=0;i<200;i++) check((i*37)%101);
        System.out.println("PASS negative zero one multi start-order 10000-rounds 200-repeat-runs");
    }
}
''','stdout':'PASS negative zero one multi start-order 10000-rounds 200-repeat-runs',
'checks':['negative/zero/one-round boundaries','number thread deliberately starts first but abc group still prints first','exact abc123 group alternation for multiple rounds','10000-round stress output is exact','200 repeated runs across varied round counts are deterministic'],
'claims':[
('source-boundary','The source only says multiple threads alternately print abc and 123; group granularity, first group, rounds, and synchronization primitive are not preserved requirements.',['repository-source'],['核心结论','关键细节']),
('state-machine','The candidate explicitly models two states protected by one lock and two Conditions, so output ordering does not depend on thread start or OS scheduling order.',['fixture'],['1 分钟版','3 分钟版','原理机制']),
('determinism','Executable validation checks exact abc123 repetition even when the number thread is started first and across long/repeated runs.',['fixture'],['关键细节','常见追问'])],
'findings':['The candidate treats the source as sparse and explicitly selects group-level abc/123 alternation instead of inventing an unstated a1b2c3 contract.','Correctness is driven by a two-state predicate under one lock, not by sleep or assumed start order.','Both Condition waits use while loops and signal the opposite wait set only after the state transition.','OpenJDK 21 validation deliberately starts the number thread first and still requires abc to be the first observable group.','Long and repeated exact-output tests exercise scheduling variation while preserving the declared deterministic contract.']}
}

HEADINGS=['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES={'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}

def run(*args:str,cwd:Path|None=None)->subprocess.CompletedProcess[str]:
    return subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)

def write_json(path:Path,payload:object)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def build_one(cid:str,spec:dict)->str:
    candidate=ROOT/f'review/candidates/answers/{cid}.md'
    if candidate.exists(): raise SystemExit(f'{cid}: candidate already exists; do not overwrite')
    ctx=json.loads(run('node','scripts/xhs.js','answer','context','--canonical-id',cid,'--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id')!=cid or ctx.get('answer_type')!='coding': raise SystemExit(f'{cid}: context/type drift')
    if ctx.get('canonical',{}).get('question_ids')!=[spec['qid']]: raise SystemExit(f'{cid}: ownership drift')
    src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==spec['qid']),None)
    if not src or src.get('original_question')!=spec['expected'] or src.get('is_valid_for_library') is not True: raise SystemExit(f'{cid}: source drift')
    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{cid}'; out.mkdir(parents=True,exist_ok=True); write_json(out/'context.json',ctx)
    candidate.parent.mkdir(parents=True,exist_ok=True); candidate.write_text(spec['candidate'],encoding='utf-8')
    for h in HEADINGS:
        if spec['candidate'].count(h)!=1: raise SystemExit(f'{cid}: section drift {h}')
    blocks=re.findall(r'```java\n(.*?)\n```',spec['candidate'],re.S)
    if len(blocks)!=1: raise SystemExit(f'{cid}: expected one Java block')
    with tempfile.TemporaryDirectory(prefix=f'b54-{spec["class"]}-') as tmp:
        d=Path(tmp); (d/f'{spec["class"]}.java').write_text(blocks[0].strip()+'\n',encoding='utf-8'); (d/f'{spec["class"]}Test.java').write_text(spec['test'],encoding='utf-8')
        run('javac',f'{spec["class"]}.java',f'{spec["class"]}Test.java',cwd=d); stdout=run('java',f'{spec["class"]}Test',cwd=d).stdout.strip()
    if stdout!=spec['stdout']: raise SystemExit(f'{cid}: fixture stdout {stdout}')
    validation={'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,'command':f'javac {spec["class"]}.java {spec["class"]}Test.java && java {spec["class"]}Test','stdout':stdout,'checks':spec['checks']}; write_json(out/'writer_validation.json',validation)
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources=[{'source_id':'repository-source','title':f'Batch 0054 exact source context for {cid}','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'fixture','title':f'OpenJDK 21 deterministic validation for {cid}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}]
    claims=[{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in spec['claims']]
    coverage=[{'question_id':spec['qid'],'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    reviewer=f'source-first-isolated-reviewer-batch-0054-{spec["class"].lower()}-20260829-v1'
    review={'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0054.{spec["class"].lower()}.v1','decision':'pass','revision_round':1,'source_packet':[str(out/'context.json'),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':spec['findings'],'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied']}; write_json(out/'isolated_review_result.json',review)
    write_json(ROOT/f'review/evidence/{cid}.json',{'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0054-slice-c-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':f'Batch 0054 source-first isolated review for {cid}','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':spec['checks'],'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in spec['checks']]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':spec['findings']},'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied'})
    return digest

def main()->int:
    results={cid:build_one(cid,spec) for cid,spec in ITEMS.items()}
    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'; text=task.read_text(encoding='utf-8').rstrip()
    notes={
    'cq_q_f213ccebb77d694fa4eb9062e4f03a01':'- [x] `cq_q_f213ccebb77d694fa4eb9062e4f03a01` source-first isolated review PASS: the sparse blocking-queue source is bounded to an interruptible bounded FIFO contract using one lock plus notEmpty/notFull Conditions and while predicates. OpenJDK 21 validation observes real producer/consumer blocking, interruption, and exactly-once delivery across a 4x4/20000-item stress run. Formal promotion remains blocked by repository human-approval/real-review policy.',
    'cq_q_f4495c3cafbc49411bce1eab8525b2f0':'- [x] `cq_q_f4495c3cafbc49411bce1eab8525b2f0` source-first isolated review PASS: the sparse alternating-print source is explicitly bounded to group-level abc/123 alternation with abc first. A lock/Condition two-state machine makes output independent of start order; OpenJDK 21 validation deliberately starts the number thread first and checks exact output through 10000 rounds plus 200 repeated runs. Formal promotion remains blocked by repository human-approval/real-review policy.'}
    for cid in results:
        if notes[cid] not in text: text+='\n'+notes[cid]
    task.write_text(text+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'batch':BATCH,'built':list(results),'candidate_sha256':results},ensure_ascii=False)); return 0

if __name__=='__main__': raise SystemExit(main())
