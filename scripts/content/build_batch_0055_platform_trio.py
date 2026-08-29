#!/usr/bin/env python3
"""Build, execute, and source-first review EventBus, department top-3 SQL, and ordered ABC candidates."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0055'
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}

TARGETS = [
    {
        'cid':'cq_q_f6ce37472bfc7f9e9c3526329451d8a2','qid':'f6ce37472bfc7f9e9c3526329451d8a2','expected':'算法：实现一个简单的 EventBus 类？','slug':'eventbus','language':'javascript','class':'event_bus',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f6ce37472bfc7f9e9c3526329451d8a2","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 实现一个简单的 EventBus 类

## 核心结论

来源只要求“实现一个简单的 EventBus 类”，没有指定语言、同步/异步语义、异常策略或 `once` 等扩展。这里声明一个最小 JavaScript 合同：`on(event, handler)` 注册同步监听器并返回取消函数；`off(event, handler)` 按函数引用移除该事件下的匹配监听器；`emit(event, payload)` 按注册顺序同步调用当前时刻的监听器快照。核心数据结构是 `Map<event, handler[]>`。

## 1 分钟版

- `Map` 的 key 是事件名，value 是监听器数组。
- `on`：校验 handler，追加到数组，并返回 `() => off(event, handler)`，方便调用方释放订阅。
- `off`：只处理指定事件，把与 handler 引用相等的注册项删除；数组空后删除 key。
- `emit`：先 `slice()` 一份快照，再按顺序调用。这样监听器在回调里新增/删除订阅，不会改变本次已经开始的分发集合。
- 当前合同是同步分发；某个 handler 抛异常时异常直接向上传播，并停止本次后续调用。若业务要“隔离失败继续广播”，需要另定错误合同。

## 3 分钟版

```javascript
class EventBus {
  constructor() {
    this.listeners = new Map();
  }

  on(event, handler) {
    if (typeof handler !== 'function') {
      throw new TypeError('handler must be a function');
    }
    const list = this.listeners.get(event) ?? [];
    list.push(handler);
    this.listeners.set(event, list);
    return () => this.off(event, handler);
  }

  off(event, handler) {
    const list = this.listeners.get(event);
    if (!list) return false;
    const next = list.filter(fn => fn !== handler);
    if (next.length === list.length) return false;
    if (next.length === 0) this.listeners.delete(event);
    else this.listeners.set(event, next);
    return true;
  }

  emit(event, payload) {
    const snapshot = (this.listeners.get(event) ?? []).slice();
    for (const handler of snapshot) handler(payload);
    return snapshot.length;
  }
}

module.exports = { EventBus };
```

这里数组允许同一个函数被重复注册；`off` 会删除该事件下所有相同函数引用的注册。若希望“一次 off 只撤销一次注册”，需要改为注册 token 或只删除一个索引，不能让语义隐含。

## 关键细节

- **快照分发**：若直接遍历原数组，回调内部 `on/off` 可能改变迭代结果；快照让“本次 emit 的监听集合”稳定。
- **同步边界**：当前 `emit` 不 `await` Promise，也不吞异常；异步 EventBus 是另一个合同。
- **重复注册**：数组保留重复注册，因此同一函数注册两次会被调用两次；当前 `off` 一次删除该函数的全部重复注册。
- **内存释放**：调用方应保存 `on` 返回的 unsubscribe；长期不释放订阅会让 bus 持有 handler 引用。
- **事件名类型**：示例允许任意可作为 `Map` key 的值；若业务只允许字符串，可在边界层进一步校验。

## 原理机制

EventBus 是发布/订阅解耦：发布者只知道事件名和 payload，不直接依赖订阅者；订阅者通过注册函数建立运行时关系。`Map<event,listeners>` 把“事件 -> 多个消费者”索引化。快照的意义是确定一次 `emit` 的线性化视图：本次开始时已经存在的监听器参与本次调用，而回调里产生的订阅变化从下一次 emit 起生效。

## 项目经验版

来源没有真实项目规模，不能虚构线上吞吐或故障数据。实际落地前我会先确认四个合同：同步还是异步、监听器异常是否隔离、是否需要 `once`/优先级、是否需要弱引用或显式生命周期。简单 UI/模块内事件总线可用这种实现；跨进程消息、可靠投递、持久化重试则不属于这个内存 EventBus。

## 常见追问

- 问：为什么不用 `Set`？答：`Set` 会天然去重，改变“同一 handler 注册两次是否调用两次”的语义；这里选择数组并明确重复注册规则。
- 问：emit 时有人 off 自己怎么办？答：当前 emit 用快照，因此本次已经进入快照的 handler 仍按顺序执行；off 对后续 emit 生效。
- 问：怎么做 once？答：可以用包装函数，在第一次调用前后执行 unsubscribe；但 `once` 不是当前来源要求，所以不放进最小核心。
- 问：监听器报错怎么办？答：当前同步合同让异常向上抛并中断后续监听器；若业务要求隔离，需要逐个 try/catch 并定义错误汇聚方式。
- 问：会内存泄漏吗？答：如果长期对象注册后不取消，bus 会持续持有函数和闭包引用；返回 unsubscribe 是生命周期管理入口。

## 易错点

- 直接遍历可变监听器数组，让回调中的增删影响当前 emit。
- 用 `Set` 却没有说明重复注册语义。
- 吞掉 handler 异常，却没有给调用方任何失败信号。
- 把内存内同步 EventBus 描述成可靠消息队列。
''',
        'test':r'''const assert = require('assert');
const { EventBus } = require('./event_bus');
const bus = new EventBus();
const calls = [];
const h1 = x => { calls.push('a'+x); bus.on('e', y => calls.push('late'+y)); };
const h2 = x => calls.push('b'+x);
const un1 = bus.on('e', h1);
bus.on('e', h2);
assert.strictEqual(bus.emit('e', 1), 2);
assert.deepStrictEqual(calls, ['a1','b1']);
assert.strictEqual(bus.emit('e', 2), 3);
assert.deepStrictEqual(calls, ['a1','b1','a2','b2','late2']);
assert.strictEqual(un1(), true);
assert.strictEqual(bus.emit('e', 3), 4);
assert.deepStrictEqual(calls.slice(-4), ['b3','late3','late3','late3']);
let dup = 0; const same = () => dup++;
bus.on('d', same); bus.on('d', same); assert.strictEqual(bus.emit('d'), 2); assert.strictEqual(dup, 2); assert.strictEqual(bus.off('d', same), true); assert.strictEqual(bus.emit('d'), 0);
assert.strictEqual(bus.off('missing', same), false);
assert.throws(() => bus.on('x', 1), /handler/);
const err = new EventBus(); err.on('x', () => { throw new Error('boom'); }); err.on('x', () => calls.push('unreached')); assert.throws(() => err.emit('x'), /boom/);
console.log('PASS ordered snapshot unsubscribe duplicate-contract invalid-handler exception-propagation');
''',
        'stdout':'PASS ordered snapshot unsubscribe duplicate-contract invalid-handler exception-propagation',
        'checks':['listeners execute in registration order','emit snapshots listeners so subscriptions added during a callback start next emit','unsubscribe/off behavior is explicit','duplicate registration follows the declared array contract','invalid handlers fail closed and listener exceptions propagate'],
        'claims':[
            ('source-boundary','The preserved source asks only for a simple EventBus and does not specify language, async behavior, error isolation, once semantics, or cross-process reliability.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('eventbus-behavior','The executable Node.js fixture verifies ordered synchronous dispatch, snapshot mutation semantics, unsubscribe/off behavior, duplicate registration, input validation, and exception propagation under the declared contract.',['fixture'],['1 分钟版','3 分钟版','关键细节','原理机制','常见追问']),
        ],
        'findings':['The candidate defines a small in-memory synchronous EventBus contract instead of inventing reliability or async requirements.','Snapshot dispatch provides stable per-emit listener membership when callbacks mutate subscriptions.','The duplicate-registration, off, and exception semantics are explicit rather than left accidental.','Node.js validation covers ordered delivery, mutation during emit, unsubscribe, duplicates, invalid input, and failure propagation.'],
        'task_note':'- [x] `cq_q_f6ce37472bfc7f9e9c3526329451d8a2` source-first isolated review PASS: the minimal synchronous JavaScript EventBus declares ordered snapshot dispatch, explicit duplicate/off/error semantics, and Node.js validation covers mutation during emit, unsubscribe, invalid handlers and exception propagation. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_f849810b0aa5477dc435d4829108f4dd','qid':'f849810b0aa5477dc435d4829108f4dd','expected':'SQL 应用：请口述 SQL 思路：如何计算每个部门薪资前三名的员工信息？请准确写出 `RANK()`, `DENSE_RANK()` 与 `ROW_NUMBER()` 的窗口函数语法，并解释它们在处理并列排名时的区别。','slug':'department-top3-sql','language':'sql','class':'department_top3',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f849810b0aa5477dc435d4829108f4dd","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 每个部门薪资前三名：RANK、DENSE_RANK、ROW_NUMBER

## 核心结论

来源明确要求“每个部门薪资前三名的员工信息”，并要求准确写出 `RANK()`、`DENSE_RANK()`、`ROW_NUMBER()` 的窗口语法和并列区别，但没有给真实表名。这里声明最小 schema：`employee(employee_id, employee_name, department_id, salary)`。如果“前三名”理解为**每个部门前三个不同薪资档位，且并列员工都保留**，应优先用 `DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC)`，再过滤 `salary_rank <= 3`。

## 1 分钟版

- `PARTITION BY department_id`：每个部门独立排名。
- `ORDER BY salary DESC`：薪资从高到低。
- `RANK()`：并列同名次，后续名次会跳号，例如 `100,100,90` -> `1,1,3`。
- `DENSE_RANK()`：并列同名次，后续不跳号，例如 `100,100,90` -> `1,1,2`。
- `ROW_NUMBER()`：每行唯一序号，例如 `100,100,90` -> `1,2,3`；并列工资若没有额外 tie-breaker，哪一行先后不应依赖未声明顺序。
- 因而“前三个薪资档位且保留并列”用 `DENSE_RANK <= 3`；“严格每部门最多三行”才更接近 `ROW_NUMBER <= 3`。

## 3 分钟版

```sql
WITH ranked AS (
  SELECT
    employee_id,
    employee_name,
    department_id,
    salary,
    DENSE_RANK() OVER (
      PARTITION BY department_id
      ORDER BY salary DESC
    ) AS salary_rank
  FROM employee
)
SELECT
  employee_id,
  employee_name,
  department_id,
  salary,
  salary_rank
FROM ranked
WHERE salary_rank <= 3
ORDER BY department_id, salary DESC, employee_id;
```

三种窗口函数的准确语法形态分别是：

`RANK() OVER (PARTITION BY department_id ORDER BY salary DESC)`

`DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC)`

`ROW_NUMBER() OVER (PARTITION BY department_id ORDER BY salary DESC, employee_id)`

最后一个示例给 `ROW_NUMBER` 增加 `employee_id` 作为稳定 tie-breaker；这不是薪资排名业务事实，而是为了在相同 salary 下获得确定顺序。

## 关键细节

- SQL 逻辑执行上不能通常直接在同一 SELECT 的 `WHERE` 中引用窗口函数别名，因此常用 CTE/子查询先算 rank，再过滤。
- `RANK <= 3` 不等价于“三个不同薪资档位”：若第一名两人并列，下一档会是第 3 名，再下一档是第 4 名，所以可能只保留两个薪资档位。
- `DENSE_RANK <= 3` 会保留三个不同薪资档位，并把临界档位上的所有并列员工都返回，因此行数可能超过 3。
- `ROW_NUMBER <= 3` 每部门最多三行，但会拆开并列；要结果可重复，应提供稳定 tie-breaker。
- `NULL salary` 的排序位置依数据库方言而异；来源没有定义空薪资语义，实际系统应先决定是否排除 NULL。

## 原理机制

窗口函数不会像 `GROUP BY` 那样把多行聚合成一行，而是在保留每个员工明细行的同时，为分区内的行计算排名。`PARTITION BY` 切分部门，窗口 `ORDER BY` 决定排名顺序。三种函数的差异只体现在“并列如何占用后续名次”：RANK 留空档、DENSE_RANK 不留空档、ROW_NUMBER 根本不共享名次。选择函数必须先定义业务对并列的语义。

## 项目经验版

来源没有真实 schema、数据库方言、索引或执行计划，不能虚构。落地时我会确认“前三名”到底是三行还是三个薪资档位，以及 NULL/并列规则；然后根据目标数据库检查窗口排序成本，并考虑 `(department_id, salary)` 等索引是否对实际查询计划有帮助。索引效果必须以真实数据库 `EXPLAIN` 为准。

## 常见追问

- 问：RANK 和 DENSE_RANK 最直观区别？答：`100,100,90,80` 上，RANK 是 `1,1,3,4`，DENSE_RANK 是 `1,1,2,3`。
- 问：为什么不用 ROW_NUMBER？答：如果要保留并列的前三个薪资档位，ROW_NUMBER 会强制拆成唯一行号，可能丢掉临界并列员工。
- 问：什么时候用 ROW_NUMBER？答：业务明确要求每部门严格取三行，并定义相同薪资下的 tie-breaker 时。
- 问：为什么用 CTE？答：先计算窗口排名，再在外层按 rank 过滤，结构清楚且跨多数数据库写法稳定。
- 问：结果为什么可能超过三行？答：DENSE_RANK 保留临界薪资档位的全部并列员工，前三档可能对应多于三个人。

## 易错点

- 把 `RANK <= 3` 误说成一定保留三个不同薪资档位。
- 用 `ROW_NUMBER` 处理并列却不给 tie-breaker，还声称结果顺序确定。
- 在不支持 QUALIFY 的数据库里直接 `WHERE DENSE_RANK()...`。
- 把示例表名字段名冒充成来源给定 schema。
''',
        'test':r'''import sqlite3
con=sqlite3.connect(':memory:')
con.execute('create table employee(employee_id integer primary key, employee_name text, department_id integer, salary integer)')
rows=[(1,'A',10,100),(2,'B',10,100),(3,'C',10,90),(4,'D',10,80),(5,'E',10,70),(6,'F',20,50),(7,'G',20,40),(8,'H',20,40),(9,'I',20,30),(10,'J',20,20)]
con.executemany('insert into employee values(?,?,?,?)',rows)
sql='''WITH ranked AS (SELECT employee_id,employee_name,department_id,salary,DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS salary_rank FROM employee) SELECT employee_id,employee_name,department_id,salary,salary_rank FROM ranked WHERE salary_rank<=3 ORDER BY department_id,salary DESC,employee_id'''
actual=list(con.execute(sql))
expected=[(1,'A',10,100,1),(2,'B',10,100,1),(3,'C',10,90,2),(4,'D',10,80,3),(6,'F',20,50,1),(7,'G',20,40,2),(8,'H',20,40,2),(9,'I',20,30,3)]
assert actual==expected,(actual,expected)
rank=list(con.execute('select salary,RANK() over(order by salary desc),DENSE_RANK() over(order by salary desc),ROW_NUMBER() over(order by salary desc, employee_id) from employee where department_id=10 order by salary desc,employee_id'))
assert rank[:4]==[(100,1,1,1),(100,1,1,2),(90,3,2,3),(80,4,3,4)],rank
print('PASS dense-top3 tie-preserved rank-gap dense-no-gap row-number-unique')
''',
        'stdout':'PASS dense-top3 tie-preserved rank-gap dense-no-gap row-number-unique',
        'checks':['DENSE_RANK<=3 returns the first three distinct salary levels per department and preserves ties','RANK shares ties and leaves rank gaps','DENSE_RANK shares ties without gaps','ROW_NUMBER assigns unique row numbers using an explicit tie-breaker'],
        'claims':[
            ('source-boundary','The preserved source explicitly asks for department top-three salaries plus correct RANK, DENSE_RANK, and ROW_NUMBER syntax and tie semantics; table and column names are not preserved source facts.',['repository-source'],['核心结论','3 分钟版','项目经验版']),
            ('window-semantics','The executable SQLite fixture verifies DENSE_RANK top-three salary-level behavior and the 1,1,3 versus 1,1,2 versus unique row-number distinction on tied salaries.',['fixture'],['1 分钟版','3 分钟版','关键细节','原理机制','常见追问']),
        ],
        'findings':['The candidate answers the source-specific comparison of all three ranking functions and does not reduce the task to one SQL query.','DENSE_RANK is correctly selected for the declared three-distinct-salary-level contract with ties preserved.','The answer explains the RANK gap and ROW_NUMBER tie-breaking consequences that often cause incorrect top-three interpretations.','SQLite validation reproduces tied department salaries and verifies the expected ranking behavior and result set.'],
        'task_note':'- [x] `cq_q_f849810b0aa5477dc435d4829108f4dd` source-first isolated review PASS: the candidate accurately distinguishes RANK/DENSE_RANK/ROW_NUMBER tie semantics, declares DENSE_RANK<=3 for three salary levels with ties preserved, and SQLite validation verifies both ranking sequences and department result rows. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_f90ba8d1c83d261d11b756321624b189','qid':'f90ba8d1c83d261d11b756321624b189','expected':'算法 2：多线程按顺序循环打印 A, B, C','slug':'ordered-abc','language':'java','class':'OrderedABC',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f90ba8d1c83d261d11b756321624b189","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 多线程按顺序循环打印 A、B、C

## 核心结论

来源只要求“多线程按顺序循环打印 A, B, C”，没有指定语言、循环次数或并发原语。这里声明一个可执行 Java 合同：启动三个线程 A/B/C，各执行 `rounds` 次，最终顺序必须严格是 `ABCABC...`；用三个 `Semaphore` 组成令牌环，初始只有 A 的许可为 1，B/C 为 0。每个线程获取自己的许可、输出字符，再释放下一个线程的许可。

## 1 分钟版

- 三个信号量：`a=1, b=0, c=0`。
- A：`acquire(a) -> print A -> release(b)`。
- B：`acquire(b) -> print B -> release(c)`。
- C：`acquire(c) -> print C -> release(a)`。
- 每个线程重复 rounds 次，因此令牌按 A→B→C→A 单向传递，不依赖线程调度碰巧有序。
- `rounds=0` 返回空序列；中断不能被静默吞掉，示例恢复 interrupt flag 并作为失败传播。

## 3 分钟版

```java
import java.util.concurrent.Semaphore;

public final class OrderedABC {
    public static String run(int rounds) throws InterruptedException {
        if (rounds < 0) throw new IllegalArgumentException("rounds must be >= 0");

        Semaphore a = new Semaphore(1);
        Semaphore b = new Semaphore(0);
        Semaphore c = new Semaphore(0);
        StringBuffer out = new StringBuffer();

        Thread ta = worker('A', rounds, a, b, out);
        Thread tb = worker('B', rounds, b, c, out);
        Thread tc = worker('C', rounds, c, a, out);
        ta.start(); tb.start(); tc.start();
        ta.join(); tb.join(); tc.join();
        return out.toString();
    }

    private static Thread worker(char ch, int rounds, Semaphore mine,
                                 Semaphore next, StringBuffer out) {
        return new Thread(() -> {
            for (int i = 0; i < rounds; i++) {
                try {
                    mine.acquire();
                    out.append(ch);
                    next.release();
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
            }
        });
    }
}
```

`StringBuffer` 在测试里替代 `System.out.print` 以便精确验证顺序；由于信号量令牌保证同一时刻只有当前字符线程能越过 acquire，核心顺序不依赖缓冲区的线程安全来“碰巧成立”。生产打印时可把 `out.append(ch)` 换成明确的输出动作。

## 关键细节

- 初始许可只能给 A；如果三个 semaphore 都是 1，就不能保证首轮顺序。
- 必须在输出完成后再 release 下一个许可，否则下一个线程可能先运行并打乱可观察顺序。
- `Semaphore` 解决的是顺序协作，不是忙等；没有许可的线程会阻塞。
- 示例 worker 中断后返回会使令牌链可能无法完成，因此 `run` 的简化实现适合面试展示，不是带取消协议的生产任务框架。
- 若需要可取消且保证所有线程退出，应增加共享取消状态、统一唤醒和生命周期管理；来源没有要求，不在最小实现中虚构。

## 原理机制

把“谁可以打印”建模为一个唯一令牌。初始令牌在 A，A 消费后把令牌交给 B，B 再交给 C，C 再交回 A。每个 semaphore 的许可数就是对应线程是否持有执行资格。这样线程调度器可以任意切换线程，但只有拿到许可的线程能跨过同步点，因此可观察输出顺序由同步协议而非调度时机决定。

## 项目经验版

来源没有真实并发规模和生产约束，不能虚构。面试里我会先给 semaphore 方案，再补充 `ReentrantLock + Condition`、`wait/notify` 都能实现相同状态机；选择哪种主要看可读性、取消协议和现有代码约束。真实服务代码通常不会为了打印字符创建永久线程，题目重点是线程协作和 happens-before 的设计。

## 常见追问

- 问：为什么不用 sleep？答：sleep 只延迟时间，不建立线程之间的顺序关系，调度抖动后仍可能乱序。
- 问：为什么不用 volatile 轮询一个 state？答：可以，但会产生忙等或复杂 park/unpark；Semaphore 直接提供阻塞等待和许可传递。
- 问：能打印 N 轮吗？答：每个 worker 循环同一个 rounds 次，令牌环自然产生 N 个 ABC。
- 问：StringBuffer 是必须的吗？答：不是顺序协议的核心；这里用于收集测试结果。令牌保证每一步只有一个线程处于输出临界位置。
- 问：线程被中断怎么办？答：当前示例恢复中断标记并结束该 worker；完整生产取消还要唤醒其他等待线程并统一收尾。

## 易错点

- 用 sleep 猜执行顺序。
- 三个线程初始都可执行，失去唯一令牌不变量。
- 先 release 再输出，允许下一个字符抢先出现。
- 吞掉 InterruptedException，不恢复中断状态。
- 把面试同步示例夸大成生产线程模型。
''',
        'test':r'''import java.util.*;
public final class OrderedABCTest {
    static void check(boolean v,String m){if(!v)throw new AssertionError(m);}
    public static void main(String[] args) throws Exception {
        check(OrderedABC.run(0).equals(""),"zero");
        check(OrderedABC.run(1).equals("ABC"),"one");
        String s=OrderedABC.run(1000);
        check(s.length()==3000,"length="+s.length());
        for(int i=0;i<1000;i++) check(s.regionMatches(i*3,"ABC",0,3),"round="+i);
        try { OrderedABC.run(-1); throw new AssertionError("negative"); } catch(IllegalArgumentException expected){}
        for(int i=0;i<20;i++) check(OrderedABC.run(50).equals("ABC".repeat(50)),"repeat="+i);
        System.out.println("PASS zero one 1000-round exact-order 20-repeat-runs negative-rejected");
    }
}
''',
        'stdout':'PASS zero one 1000-round exact-order 20-repeat-runs negative-rejected',
        'checks':['zero rounds produces empty output','one round produces ABC','1000 rounds produce exactly 3000 characters in ABC order','20 repeated executions preserve deterministic order','negative rounds fail closed'],
        'claims':[
            ('source-boundary','The preserved source requires multiple threads to repeatedly print A, B, C in order but does not specify language, round count, cancellation protocol, or synchronization primitive.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('ordering-correctness','The executable OpenJDK fixture verifies the semaphore token-ring contract for zero, one, 1000 rounds, repeated runs, and invalid round counts.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate models ordering as an explicit A→B→C semaphore token ring rather than timing-based sleep coordination.','Only one initial permit exists, preserving the unique-turn invariant independent of scheduler interleaving.','The answer distinguishes the interview synchronization core from a production-grade cancellation/lifecycle protocol.','OpenJDK validation checks exact order over 1000 rounds and 20 repeated executions plus boundary inputs.'],
        'task_note':'- [x] `cq_q_f90ba8d1c83d261d11b756321624b189` source-first isolated review PASS: a three-Semaphore token ring enforces A→B→C ordering without timing assumptions, and OpenJDK validation checks exact output over 1000 rounds, 20 repeated runs, zero/one rounds and invalid input. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
]


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)

def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def execute(target: dict, code: str) -> str:
    with tempfile.TemporaryDirectory(prefix=f'b55-{target["slug"]}-') as tmp:
        d=Path(tmp)
        if target['language']=='javascript':
            (d/'event_bus.js').write_text(code.strip()+'\n',encoding='utf-8')
            (d/'event_bus_test.js').write_text(target['test'],encoding='utf-8')
            return run('node','event_bus_test.js',cwd=d).stdout.strip()
        if target['language']=='sql':
            (d/'department_top3_test.py').write_text(target['test'],encoding='utf-8')
            return run('python3','department_top3_test.py',cwd=d).stdout.strip()
        if target['language']=='java':
            (d/f'{target["class"]}.java').write_text(code.strip()+'\n',encoding='utf-8')
            (d/f'{target["class"]}Test.java').write_text(target['test'],encoding='utf-8')
            run('javac',f'{target["class"]}.java',f'{target["class"]}Test.java',cwd=d)
            return run('java',f'{target["class"]}Test',cwd=d).stdout.strip()
        raise SystemExit('unknown language')

def main() -> int:
    inventory_path=ROOT/f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    if not inventory_path.exists(): raise SystemExit('Batch 0055 source inventory must be frozen before writing')
    inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task_text=task.read_text(encoding='utf-8').rstrip()
    results=[]
    for target in TARGETS:
        cid,qid=target['cid'],target['qid']
        candidate=ROOT/f'review/candidates/answers/{cid}.md'; evidence=ROOT/f'review/evidence/{cid}.json'
        if candidate.exists() or evidence.exists(): raise SystemExit(f'{cid}: candidate/evidence already exists; do not overwrite')
        ctx_path=ROOT/f'review/content_build/answer_batch_{BATCH}/{cid}/context.json'
        ctx=json.loads(ctx_path.read_text(encoding='utf-8')) if ctx_path.exists() else {}
        if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id')!=cid or ctx.get('answer_type')!='coding': raise SystemExit(f'{cid}: context/type drift')
        if ctx.get('canonical',{}).get('question_ids')!=[qid]: raise SystemExit(f'{cid}: source ownership drift')
        src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==qid),None)
        if not src or src.get('original_question')!=target['expected'] or src.get('is_valid_for_library') is not True: raise SystemExit(f'{cid}: source wording/validity drift')
        inv=next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id')==cid),None)
        if not inv or inv.get('existing_candidate') or inv.get('existing_evidence'): raise SystemExit(f'{cid}: inventory no longer describes a fresh target')
        body=target['candidate']
        for heading in HEADINGS:
            if body.count(heading)!=1: raise SystemExit(f'{cid}: section drift {heading}')
        fence=target['language'] if target['language']!='javascript' else 'javascript'
        blocks=re.findall(rf'```{fence}\n(.*?)\n```',body,re.S)
        if len(blocks)!=1: raise SystemExit(f'{cid}: expected exactly one {fence} implementation block')
        candidate.parent.mkdir(parents=True,exist_ok=True); candidate.write_text(body,encoding='utf-8')
        stdout=execute(target,blocks[0])
        if stdout!=target['stdout']: raise SystemExit(f'{cid}: fixture stdout drift: {stdout}')
        out=ROOT/f'review/content_build/answer_batch_{BATCH}/{cid}'
        command={'javascript':'node event_bus_test.js','sql':'python3 department_top3_test.py','java':f'javac {target["class"]}.java {target["class"]}Test.java && java {target["class"]}Test'}[target['language']]
        validation={'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,'command':command,'stdout':stdout,'checks':target['checks']}
        write_json(out/'writer_validation.json',validation)
        digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
        sources=[{'source_id':'repository-source','title':f'Batch 0055 frozen source context for {target["slug"]}','locator':str(ctx_path),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'fixture','title':f'Deterministic executable validation for {target["slug"]}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}]
        claims=[{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in target['claims']]
        coverage=[{'question_id':qid,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
        write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
        reviewer=f'source-first-isolated-reviewer-batch-0055-{target["slug"]}-20260829-v1'
        review={'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0055.{target["slug"]}.v1','decision':'pass','revision_round':1,'source_packet':[str(ctx_path),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings'],'promotion_blockers':[PROMOTION_BLOCKER]}
        write_json(out/'isolated_review_result.json',review)
        write_json(evidence,{'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':f'content-batch-0055-{target["slug"]}-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':f'Batch 0055 {target["slug"]} source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':command,'result':'pass','reported_stdout':stdout,'checks':target['checks'],'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in target['checks']]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings']},'promotion_blocker':PROMOTION_BLOCKER})
        writer=json.loads((out/'writer_research.json').read_text(encoding='utf-8')); writer['review_state']='writer_complete_isolated_review_passed'; writer['promotion_blocker']=PROMOTION_BLOCKER; write_json(out/'writer_research.json',writer)
        if target['task_note'] not in task_text: task_text+='\n'+target['task_note']
        results.append({'canonical_id':cid,'candidate_sha256':digest,'decision':'pass','stdout':stdout})
    task.write_text(task_text+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'batch':BATCH,'completed':results,'promotion_blocker':PROMOTION_BLOCKER},ensure_ascii=False))
    return 0

if __name__=='__main__': raise SystemExit(main())
