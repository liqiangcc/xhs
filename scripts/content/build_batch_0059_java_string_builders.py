#!/usr/bin/env python3
"""Stage Batch 0059 Java String/StringBuilder/StringBuffer concept candidate."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path('.')
BATCH = '0059'
DATE = '2026-08-30'
CID = 'cq_q_ae1651ba6576c28fcd53d4f4888dbd3e'
EXPECTED_QIDS = [
    '13d712dbbbe982e220bc87d74737abcd',
    '1bb63b161281368c9e9095fa9bed3b90',
    'ae1651ba6576c28fcd53d4f4888dbd3e',
]
EXPECTED_VARIANTS = {
    'String, StringBuilder, StringBuffer 的区别',
    'String，StringBuffer，StringBuilder的区别',
    'String, StringBuilder, StringBuffer 的区别？',
    '说一下 String, StringBuffer, StringBuilder 的区别',
}
EXPECTED_SOURCE_IDS = {
    'java26-string',
    'java26-stringbuilder',
    'java26-stringbuffer',
    'jls26-string-concat',
}

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ae1651ba6576c28fcd53d4f4888dbd3e","version":1,"status":"draft","updated_at":"2026-08-30","answer_type":"concept","quality_tier":"candidate"} -->
# String、StringBuilder、StringBuffer 的区别

## 核心结论

三者最核心的区别可以用两条轴来记：**是否可变**和**是否提供同步保证**。`String` 表示不可变字符串；`StringBuilder` 和 `StringBuffer` 都是可变字符序列。二者之间，`StringBuilder` 不提供同步保证，适合线程内或有明确外部约束的增量拼接；`StringBuffer` 为共享实例上的操作提供同步语义，只有设计上确实需要多个线程共同修改同一个 builder 时才有理由选它。

选择上可以先按这个规则回答：稳定文本用 `String`；单线程/线程封闭的反复拼接优先 `StringBuilder`；确实需要共享同一个可变字符缓冲区并依赖其同步语义时才考虑 `StringBuffer`。不要把“多线程程序”简单等同于“必须用 StringBuffer”。

## 1 分钟版

- `String`：**不可变**。创建后字符串值不能被原地修改，因此很适合表示稳定文本和跨组件共享的值。
- `StringBuilder`：**可变、无同步保证**。`append`、`insert`、`delete` 等操作修改同一个 builder，通常用于单线程或线程封闭的字符串构建。
- `StringBuffer`：**可变、带同步语义**。API 与 `StringBuilder` 很接近，但为共享实例上的操作提供线程安全保证，因此会承担相应同步成本。
- 性能不要背“固定快几倍”。真正的机制差异是：可变 builder 可以在容量允许时继续修改内部缓冲区，而 `StringBuffer` 还要承担同步；同时 `String +` 的具体编译实现并不是语言规范固定成某一种 builder。
- 最终需要稳定字符串时，builder/buffer 通过 `toString()` 得到 `String`。

一句话：**值用 String，线程内构建用 StringBuilder，共享可变构建且需要内建同步才用 StringBuffer。**

## 3 分钟版

### 1. 可变性

`String` 是不可变的。看起来像修改字符串的操作，例如拼接或替换，语义上得到的是另一个 `String` 值，而不是把已有 `String` 对象里的字符内容改掉。

`StringBuilder` 和 `StringBuffer` 都是可变字符序列：它们维护当前长度和容量，可以通过 `append`、`insert`、`delete` 等操作持续改变内容。容量不足时内部存储会扩展，因此它们适合“逐步构造一个字符串”的场景。

### 2. 并发语义

`StringBuilder` 不提供同步保证。准确说法是：**不能依赖它来保护多个线程对同一个实例的并发修改**。如果 builder 被一个线程独占，或者调用方已经通过更高层机制保证互斥，那么它完全可以出现在多线程程序里。

`StringBuffer` 是线程安全的可变字符序列，对需要的操作做同步，使共享实例上的方法调用具备受保护的串行化语义。但这不等于“一组多步业务操作自动原子”。例如“先判断长度，再 append”涉及两个独立调用时，如果整体必须不可分割，仍然需要更高层同步设计。

### 3. 性能为什么通常不同

如果逻辑需要很多次增量追加，mutable builder 可以复用并扩展自己的内部缓冲区，而不必把每一步都表达成一个新的稳定 `String` 值。`StringBuffer` 在此基础上还要执行同步，所以在不需要同步的普通构建场景里通常更倾向 `StringBuilder`。

但不能把它总结成“StringBuilder 永远比 String 快 N 倍”或者“`+` 一定编译成 StringBuilder”。Java 语言规范允许编译器/JDK 使用不同的字符串拼接策略，只要保持语言语义；具体版本可能采用 builder、运行时拼接工厂或其他等价实现。性能结论必须结合表达式形态、JDK、JIT 和实际负载验证。

### 4. 怎么选

```java
// 稳定值
String name = "alice";

// 当前线程内逐步构建
StringBuilder sb = new StringBuilder();
sb.append("user=").append(name).append(", ok=true");
String result = sb.toString();
```

如果多个工作线程各自构建自己的字符串，通常让每个线程拥有自己的 `StringBuilder`，最后再汇总，比让所有线程争抢一个共享 `StringBuffer` 更自然。只有问题合同本身要求“多个线程共同修改同一个字符缓冲区”时，才需要讨论 `StringBuffer` 或外部同步方案。

## 关键细节

- **String 的共享属性来自不可变性**：不要说“因为 String 是 final，所以线程安全”。`final` 类阻止继承，不是对象状态不可变的充分原因；这里关键是字符串值创建后不能被修改。
- **StringBuilder 的边界是同一实例并发修改**：它没有同步保证，但线程封闭使用是正常场景。
- **StringBuffer 只解决它自己的同步合同**：单个方法受保护，不代表跨多个方法调用的业务不变量自动原子。
- **容量不等于长度**：builder/buffer 的 `length` 是当前字符数量，`capacity` 是当前内部可容纳空间；追加导致容量不够时会扩容。
- **最终值仍通常是 String**：builder 适合构建阶段，进入只读传递、API 参数、Map key 等稳定值语境时通常转为 `String`。
- **不要机械解释 `+`**：源代码里的 `+` 只规定字符串拼接语义；编译器如何降低为字节码/运行时调用属于实现策略，可随 JDK 变化。
- **短小、一次性拼接不必过度优化**：可读性优先；只有循环内大量构建、热点路径或明确性能目标才值得用基准与分配数据做选择。

## 原理机制

可以把三者理解成两种数据模型：

1. `String` 是**稳定值模型**。一旦形成字符串值，后续代码不能原地改变它，因此同一个值被多处引用时，不需要担心某个持有者把字符内容改掉。
2. `StringBuilder` / `StringBuffer` 是**构建器模型**。它们有可变长度和容量，追加时尽量在现有缓冲区上继续工作，容量不足再增长；构建完成后再导出稳定 `String`。

`StringBuilder` 和 `StringBuffer` 的分离点不是“功能是否一样”，而是**同步合同**。前者把并发控制留给调用方/所有权模型，后者在自身操作上加入同步。同步能提供共享修改的安全边界，也会带来协调成本，所以没有共享修改需求时不应为了“更安全”机械选择它。

## 项目经验版

来源没有给真实项目经历，不能虚构“线上压测快了多少”。真实项目里我会先看字符串的生命周期和所有权：配置项、标识符、协议字段这类稳定值直接使用 `String`；序列化、日志格式化、代码生成等逐步构建过程优先局部 `StringBuilder`；如果发现多个线程正在争抢同一个字符缓冲区，我会先检查是否可以改成线程本地构建后汇总，因为减少共享可变状态通常比直接换成 `StringBuffer` 更清晰。只有共享缓冲区本身就是必要合同，才依赖 `StringBuffer` 或显式锁，并用实际并发测试验证吞吐和延迟。

## 常见追问

- 问：为什么 String 不可变还有 `replace`、`substring` 这些方法？答：这些方法返回新的 `String` 结果，不是在原字符串对象上原地修改字符内容。
- 问：StringBuilder 能不能在多线程代码里用？答：能。关键不是“程序有没有多个线程”，而是**同一个 StringBuilder 实例是否被多个线程无外部同步地并发修改**。线程封闭实例没有这个问题。
- 问：StringBuffer 是不是所有操作都天然原子？答：不能这么说。它为自身方法提供同步/线程安全语义，但由多个方法组合出来的业务事务仍可能被其他线程穿插，需要更高层原子性设计。
- 问：为什么通常推荐 StringBuilder 而不是 StringBuffer？答：当不需要同步时，StringBuilder 提供同类可变字符构建 API，而不要求承担 StringBuffer 的同步语义；官方 API 也把它作为普通单线程构建的优先选择。
- 问：循环里 `s = s + x` 一定每次 new 一个 StringBuilder 吗？答：不能把某种历史 javac 实现当成语言保证。规范允许编译器避免不必要中间对象，具体拼接策略随 JDK/编译器而变化；热点性能要看目标版本生成结果和实际测量。
- 问：什么时候应该预估 capacity？答：当能够较可靠估计最终长度，并且构建量大到扩容/复制成本可见时可以预设容量；普通业务代码不要为了微优化牺牲清晰度。

## 易错点

- 把 `String` 的不可变性错误归因于“类是 final”。
- 说 `StringBuilder` “多线程环境绝对不能用”，忽略线程封闭和外部同步。
- 说 `StringBuffer` 能让任意多步业务操作自动原子。
- 背固定性能倍数，忽略 JDK/JIT、表达式形态和负载。
- 说所有字符串 `+` 都必然编译成 `StringBuilder`。
- 为了避免 `String` 拼接，反而把一个 `StringBuilder` 设计成跨线程共享热点。
'''


def main() -> int:
    cdir = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context_path = cdir / 'context.json'
    research_path = cdir / 'primary_source_research.json'
    if not context_path.exists():
        raise SystemExit('frozen Batch 0059 context missing')
    if not research_path.exists():
        raise SystemExit('frozen Java string-builders primary-source research missing')

    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'concept':
        raise SystemExit(f'answer context drift: ok={context.get("ok")} type={context.get("answer_type")}')
    if sorted(context.get('canonical', {}).get('question_ids') or []) != sorted(EXPECTED_QIDS):
        raise SystemExit('canonical source ownership drift')
    if set(context.get('source_variants') or []) != EXPECTED_VARIANTS:
        raise SystemExit('source wording drift')

    research = json.loads(research_path.read_text(encoding='utf-8'))
    if research.get('schema_version') != 'answer_primary_source_research.v1':
        raise SystemExit('primary-source research schema drift')
    source_ids = {s.get('source_id') for s in research.get('sources', [])}
    if not EXPECTED_SOURCE_IDS.issubset(source_ids):
        raise SystemExit(f'primary-source set incomplete: {sorted(source_ids)}')
    claim_ids = {c.get('claim_id') for c in research.get('claims', [])}
    required_claims = {
        'immutability-vs-mutability',
        'synchronization-difference',
        'selection-rule',
        'performance-boundary',
        'plus-operator-boundary',
        'capacity-and-final-string',
    }
    if not required_claims.issubset(claim_ids):
        raise SystemExit(f'primary-source claim set incomplete: {sorted(claim_ids)}')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE, encoding='utf-8')
    digest = hashlib.sha256(CANDIDATE.encode('utf-8')).hexdigest()

    writer = {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'candidate_sha256': digest,
        'sources': [
            {
                'source_id': 'repository-source',
                'title': 'Batch 0059 frozen Java String/StringBuilder/StringBuffer source packet',
                'locator': str(context_path),
                'source_type': 'repository_source_record',
                'checked_at': DATE,
            },
            {
                'source_id': 'primary-source-research',
                'title': 'Java SE 26 String/StringBuilder/StringBuffer APIs and JLS 26 concatenation research packet',
                'locator': str(research_path),
                'source_type': 'official_documentation',
                'checked_at': DATE,
            },
        ],
        'claims': [
            {
                'claim_id': 'comparison-core',
                'text': 'String is immutable, while StringBuilder and StringBuffer are mutable character sequences; StringBuilder has no synchronization guarantee and StringBuffer supplies synchronized/thread-safe operations on a shared instance.',
                'source_ids': ['repository-source', 'primary-source-research'],
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '原理机制'],
            },
            {
                'claim_id': 'selection-and-boundaries',
                'text': 'Use String for stable values, prefer StringBuilder for incremental thread-confined construction, and use StringBuffer only when the design needs shared mutable construction under its synchronization semantics; method synchronization does not make arbitrary multi-call business logic atomic.',
                'source_ids': ['primary-source-research'],
                'answer_locations': ['核心结论', '3 分钟版', '关键细节', '常见追问'],
            },
            {
                'claim_id': 'performance-and-concat-boundary',
                'text': 'Mutable builders can reuse/grow capacity during incremental construction and StringBuffer adds synchronization, but no universal speed ratio or fixed String-plus lowering strategy is guaranteed because compiler/JDK implementations may choose conforming concatenation strategies.',
                'source_ids': ['primary-source-research'],
                'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '常见追问'],
            },
        ],
        'source_question_coverage': [
            {
                'question_id': qid,
                'covered': True,
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '常见追问'],
            }
            for qid in EXPECTED_QIDS
        ],
        'promotion_blocker': 'isolated_independent_review_and_human_approval_not_yet_performed',
    }
    (cdir / 'writer_research.json').write_text(
        json.dumps(writer, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'
    )

    task_path = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0059.md'
    task = task_path.read_text(encoding='utf-8')
    marker = f'- [x] `{CID}` source-bounded Java String/StringBuilder/StringBuffer concept candidate is staged'
    if marker not in task:
        note = (
            f"\n{marker} and writer-bound at candidate SHA-256 `{digest}` from the frozen Java SE 26/JLS 26 "
            "primary-source packet. The candidate covers mutability, synchronization semantics, selection rules, mutable-capacity/performance mechanism, "
            "the non-atomic multi-call boundary, and the JLS/compiler-freedom boundary for String `+`. Isolated independent review, evidence binding, "
            "human approval and real-review policy remain blockers; no formal promotion is claimed.\n"
        )
        task_path.write_text(task.rstrip() + note, encoding='utf-8')

    print(json.dumps({'canonical_id': CID, 'candidate_sha256': digest, 'status': 'staged'}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
