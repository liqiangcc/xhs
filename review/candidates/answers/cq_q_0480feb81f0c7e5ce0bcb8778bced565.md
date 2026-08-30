<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_0480feb81f0c7e5ce0bcb8778bced565","version":1,"status":"draft","updated_at":"2026-08-30","answer_type":"concept","quality_tier":"candidate"} -->
# Thread.sleep() 和 Object.wait() 的区别

## 核心结论

最核心的区别不是“一个让线程睡眠、一个让线程等待”这么简单，而是它们属于两种完全不同的协调模型：

- `Thread.sleep(...)` 是**当前线程主动暂停一段时间**；它不要求你持有某个对象的 monitor，而且**不会释放当前线程已经持有的 monitor**。
- `Object.wait(...)` 是**基于对象 monitor 的条件等待**；调用线程必须先持有这个对象的 monitor，调用后进入该对象的 wait set，并**释放这个对象的 monitor**，以后被 `notify/notifyAll`、中断、超时或伪唤醒等唤醒，再重新竞争并拿回 monitor 后继续。

所以选择规则是：**只是延时/退避用 sleep；线程之间围绕一个受 synchronized 保护的条件协作用 wait/notify。** 而且 `wait` 要放在检查条件的 `while` 循环里。

## 1 分钟版

- **所属和调用方式不同**：`sleep` 是 `Thread` 的静态方法，作用于当前执行线程；`wait` 是 `Object` 的实例方法，围绕“这个对象的 monitor + wait set”工作。
- **锁行为不同**：`sleep` 不会释放任何已持有 monitor；`wait` 必须在持有目标对象 monitor 时调用，并释放**这个对象的 monitor**，不是把线程持有的所有锁都释放。
- **唤醒条件不同**：`sleep` 主要按时间结束，实际重新运行还受 timer/scheduler 影响；`wait` 可以被 `notify/notifyAll`、中断、timed wait 超时或伪唤醒唤醒。
- **用途不同**：`sleep` 是 delay/backoff；`wait` 是 monitor-based condition coordination。
- **两者都能被中断**：文档规定相应情况下都会抛 `InterruptedException`，并清除 interrupted status。

一句话：**sleep 是“我先停一会儿但不交锁”，wait 是“条件不满足，我把这个 monitor 交出去并进入它的等待集合”。**

## 3 分钟版

### 1. sleep：时间等待，不参与 monitor 协议

```java
synchronized (lock) {
    Thread.sleep(1000);
    // 睡眠期间仍然持有 lock 的 monitor
}
```

`Thread.sleep` 是静态方法，它让**当前执行线程**暂时停止执行。它不要求调用线程拥有任何特定对象 monitor。

关键点是：**sleep 不释放 monitor**。如果你在 `synchronized(lock)` 中调用 `sleep`，别的线程仍然不能因为你 sleep 了就进入同一个 `synchronized(lock)` 临界区。

指定的 1 秒也不是“1 秒后这一行一定立刻执行”。API 明确把睡眠精度绑定到系统 timer 和 scheduler；睡眠条件结束以后，线程还要等调度。

典型用途：

```text
retry backoff
rate pacing
测试里制造延迟
某些轮询场景的节流
```

但如果你本质上是在等“队列不为空”“资源可用了”这类条件，用固定 sleep 轮询往往不如条件通知机制自然。

### 2. wait：对象 monitor 上的条件等待

`wait` 是 `Object` 的方法：

```java
synchronized (lock) {
    while (!condition()) {
        lock.wait();
    }
    useSharedState();
}
```

调用 `lock.wait()` 前，当前线程必须已经拥有 `lock` 的 monitor，否则会抛 `IllegalMonitorStateException`。

调用之后，大致状态变化是：

```text
own lock monitor
 -> check condition false
 -> wait()
 -> enter lock's wait set
 -> release lock monitor
 -> dormant
 -> notify / notifyAll / interrupt / timeout / spurious wakeup
 -> leave wait set
 -> compete to reacquire lock monitor
 -> reacquire
 -> recheck condition
 -> continue
```

因此“`notify()` 之后等待线程马上运行”也是错的。被唤醒的线程还要等当前持锁线程退出 synchronized/释放 monitor，再和其他竞争者一起抢锁。

### 3. wait 只释放目标对象的 monitor

这是面试里最容易说错的边界。

假设：

```java
synchronized (a) {
    synchronized (b) {
        a.wait();
    }
}
```

如果语义允许执行到这里，`a.wait()` 释放的是 `a` 的 monitor；Java API 明确指出，线程在其他对象上持有的 monitor 不会因为这次 wait 一起释放。也就是说不能背成：

```text
wait 会释放线程持有的所有锁
```

准确说法是：

```text
wait releases synchronization claims on the object whose wait method is called
```

### 4. 为什么 wait 一定推荐 while 检查条件

不能写：

```java
synchronized (lock) {
    if (!condition()) {
        lock.wait();
    }
    useSharedState();
}
```

更稳妥的是：

```java
synchronized (lock) {
    while (!condition()) {
        lock.wait();
    }
    useSharedState();
}
```

原因有两个：

1. Java `wait` 允许**spurious wakeup**；
2. 即便确实被 `notify/notifyAll` 唤醒，等你重新拿到 monitor 时，共享条件也可能已经被别的线程改变。

所以通知的语义不是“你的业务条件现在一定成立”，而是“你可以醒来重新检查条件了”。

### 5. 中断行为

两者都是可中断等待。

```java
try {
    Thread.sleep(1000);
} catch (InterruptedException e) {
    Thread.currentThread().interrupt();
}
```

以及：

```java
synchronized (lock) {
    try {
        lock.wait();
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    }
}
```

在 API 定义的中断场景下，`sleep` / `wait` 都会抛 `InterruptedException`，抛出时当前线程的 interrupted status 被清除。工程代码是否重新设置 interrupt，要看上层取消协议；常见做法是不能处理时恢复中断状态并向上退出。

对于 `wait`，规范还保证异常真正抛出前会恢复该对象 monitor 的锁状态，因此 catch 块执行时仍处在 synchronized 的 monitor 语义里。

### 6. 怎么选

```text
只是“隔一段时间再做”
    -> sleep

“条件没满足就等待，别人改变共享状态后通知我”
    -> wait/notify/notifyAll + synchronized + while(predicate)

更复杂的并发协调
    -> 优先评估 BlockingQueue / CountDownLatch / Semaphore /
       Lock + Condition 等更高层抽象
```

最后一条不是说 `wait` 过时，而是复杂业务如果直接手写 monitor 协议，容易漏掉条件循环、中断、超时、通知丢失和锁边界。

## 关键细节

- **sleep 是 `Thread` 静态方法**；调用 `someThread.sleep(...)` 这种写法即使能编译，真正睡的仍然是当前执行线程，因此不要用实例语法误导语义。
- **wait 是 `Object` 方法**，因为每个对象都关联 monitor 和 wait set。
- **sleep 不释放 monitor**。在 synchronized 中 sleep，临界区依旧被当前线程占着。
- **wait 必须拥有目标 monitor**，否则 `IllegalMonitorStateException`。
- **wait 只释放这个对象的 monitor**，其他对象上的 monitor 仍可能保持锁定。
- **notify 不是锁的直接移交**。它只是把 waiter 从等待条件推进到重新竞争 monitor 的阶段。
- **wait 应在 while 中重查 predicate**，既处理伪唤醒，也处理重新获得锁前条件再次变化。
- **timed wait 和 sleep 都涉及时间，但语义不同**：timed wait 仍然属于 monitor condition wait；sleep 只是线程时延。
- **两者都可中断**，不要背“wait 能中断、sleep 不能”。
- **sleep 时间不是精确调度 SLA**；计时结束不代表马上获得 CPU。

## 原理机制

可以把两者画成两个不同状态机。

`sleep`：

```text
RUNNABLE
 -> sleep(duration)
 -> temporarily not executing
 -> duration elapsed or interrupt
 -> eligible for scheduling
 -> RUNNABLE/executing later
```

这个过程中 monitor ownership 没有因为 sleep 自动改变。

`wait`：

```text
own object monitor
 -> wait()
 -> join object's wait set
 -> release that object's monitor
 -> notified/interrupted/timed out/spurious wakeup
 -> contend for same object monitor
 -> reacquire monitor
 -> return/throw
 -> recheck predicate
```

因此二者最大的因果差异是：

```text
sleep:
time controls when current thread becomes eligible again
monitor ownership stays unchanged

wait:
condition-notification protocol controls waiting
target monitor is temporarily relinquished so another thread can enter
and change the protected condition
```

如果 `wait` 不释放 monitor，那么生产者就可能永远进不来修改条件；这正是它必须释放目标 monitor 的机制原因。

## 项目经验版

来源没有提供真实事故、性能数据或个人经历，所以不能编造“线上因为 sleep 导致死锁”之类故事。

真实项目里判断这两个 API，我会先问：代码是在**做节奏控制**还是在**等共享条件**。

比如重试第三方接口希望指数退避，`sleep` 可以是简单实现，但要处理 interruption；生产者—消费者如果用：

```java
while (queue.isEmpty()) {
    Thread.sleep(100);
}
```

这会带来无意义轮询延迟和 CPU/锁设计问题，更自然的方案是条件通知或直接使用 `BlockingQueue`。如果已经写 `wait/notify`，则重点检查 predicate 是否在同一 monitor 下保护、是否 while 重查、是否正确处理中断和超时。

## 常见追问

- 问：sleep 会释放 synchronized 锁吗？
  答：不会。Java `Thread.sleep` 明确不丢失任何 monitor ownership，所以在 synchronized 块里 sleep 会继续占着该 monitor。

- 问：wait 会释放所有锁吗？
  答：不会。`obj.wait()` 释放的是 `obj` 这个对象的 monitor；线程在其他对象上的 monitor 不会因此自动释放。

- 问：为什么 wait 必须写在 synchronized 里？
  答：准确说是调用线程必须拥有目标对象的 monitor。`synchronized(obj)` 是最常见的获得方式；wait 的“检查条件—进入 wait set—释放 monitor”需要和受同一 monitor 保护的共享条件形成协议。

- 问：notify 后线程为什么不能马上继续？
  答：通知只把 waiter 唤醒，它仍需重新获取同一个 monitor。通知方还持锁时，waiter 只能继续等待/竞争。

- 问：为什么用 while 而不是 if？
  答：因为可能伪唤醒，而且重新拿到 monitor 前其他线程可能改变条件。wait 返回只意味着“该重新检查了”，不意味着 predicate 一定为真。

- 问：sleep(1000) 是否保证正好 1 秒后执行？
  答：不保证。休眠时间受 timer/scheduler 精度影响，时间到后也只是重新具备被调度的条件，什么时候真正执行还取决于调度。

- 问：sleep 和 wait 被 interrupt 后有什么共同点？
  答：相应等待期间被中断都会抛 `InterruptedException`，异常抛出时 interrupted status 会被清除；调用方要按取消协议决定是否恢复 interrupt。

## 易错点

- 说 `sleep` 会“释放 CPU 所以也释放锁”；线程不执行和 monitor ownership 是两件事。
- 说 `wait` 会释放当前线程持有的所有锁。
- 忘记 `wait` 属于 `Object`，或者不持有目标 monitor 就直接调用。
- 认为 `notify()` 等于把锁立即交给某个 waiter。
- `if (condition false) wait()` 后不重新检查条件。
- 忽略 spurious wakeup。
- 说 `sleep(1000)` 能精确保证 1000ms 后立即运行。
- 用固定 sleep 轮询代替本应由条件通知完成的线程协作。
- 认为只有 wait 能响应 interrupt。
- 捕获 `InterruptedException` 后无条件吞掉，破坏上层取消语义。
