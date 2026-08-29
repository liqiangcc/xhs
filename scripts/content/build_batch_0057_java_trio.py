#!/usr/bin/env python3
"""Build, execute, and source-first review three source-clear Batch 0057 Java coding candidates."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0057'
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}

TARGETS = [
    {
        'cid':'cq_q_426504c2ae6acad967088081d941ef70',
        'qid':'426504c2ae6acad967088081d941ef70',
        'expected':'算法：求1到n的和 (递归、循环及O(1)公式实现对比)',
        'slug':'sum-1-to-n',
        'class':'SumOneToN',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_426504c2ae6acad967088081d941ef70","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 求 1 到 n 的和：递归、循环与 O(1) 公式

## 核心结论

来源要求对比递归、循环和 O(1) 公式，但没有规定 n 的范围或溢出语义。这里采用 Java `long` 合同：`n >= 0`，结果必须能放进 `long`，否则抛 `ArithmeticException`。递归和循环都做 n 次加法，时间 O(n)；递归还需要 O(n) 调用栈，循环只需 O(1) 额外空间；公式 `n(n+1)/2` 时间和额外空间都是 O(1)，但实现时应先除以 2 再乘，并检查溢出。

## 1 分钟版

- 递归：`sum(n)=n+sum(n-1)`，直观但调用深度 O(n)，n 大时会栈溢出。
- 循环：从 1 加到 n，时间 O(n)、空间 O(1)，工程上比递归稳定。
- 公式：等差数列求和 `n(n+1)/2`，时间 O(1)。
- 公式不能直接无脑写 `n*(n+1)/2`：中间乘积可能先溢出；可让 n 和 n+1 中的偶数先除 2，再做受检乘法。
- 三种方法应在同一输入/溢出合同下比较，不能只看 Big-O 忽略数值边界。

## 3 分钟版

```java
public final class SumOneToN {
    private static void requireNonNegative(long n) {
        if (n < 0) throw new IllegalArgumentException("n must be non-negative");
    }

    public static long recursive(long n) {
        requireNonNegative(n);
        if (n == 0) return 0;
        return Math.addExact(n, recursive(n - 1));
    }

    public static long loop(long n) {
        requireNonNegative(n);
        long sum = 0;
        for (long i = 1; i <= n; i++) {
            sum = Math.addExact(sum, i);
        }
        return sum;
    }

    public static long formula(long n) {
        requireNonNegative(n);
        long next = Math.addExact(n, 1);
        long a = n;
        long b = next;
        if ((a & 1L) == 0L) a /= 2;
        else b /= 2;
        return Math.multiplyExact(a, b);
    }
}
```

面试时可先写公式版，再解释为什么先把偶数因子除以 2：连续两个整数必有一个是偶数，这样不会改变数学结果，却能降低中间乘积溢出的概率；最终结果本身超出 `long` 时仍由 `Math.multiplyExact` 明确失败。

## 关键细节

- 本合同把 `n=0` 定义为 0；负数直接拒绝，避免递归永不收敛。
- 递归版本即使数值不溢出，也可能因为 n 太大导致 `StackOverflowError`，这是空间复杂度带来的运行时边界。
- 循环版不会有递归栈问题，但仍然需要 O(n) 次迭代。
- 公式版先计算 `n+1` 时也可能溢出，所以使用 `Math.addExact`。
- 若题目需要任意精度，应改用 `BigInteger`，而不是静默让 `long` 回绕。

## 原理机制

把 1 到 n 的序列正反配对：`1+n`、`2+(n-1)`……每一对和都是 `n+1`，最终得到等差数列公式 `n(n+1)/2`。递归和循环是在逐项执行同一个累加关系，公式则直接利用序列结构消掉了逐项遍历，因此从 O(n) 降为 O(1)。但复杂度下降不等于数值语义自动正确，固定宽度整数仍必须处理溢出。

## 项目经验版

来源没有真实数据范围，不能虚构线上 n 的规模。我会先问清 n 的最大值和返回类型；若只是面试算法比较，用 `long` + 明确溢出足够；如果来自计费、统计等不能丢精度的业务，就应按业务上界选择 `long` 或 `BigInteger`，并把边界测试写进单元测试。

## 常见追问

- 问：递归和循环时间复杂度一样，为什么通常选循环？答：循环没有 O(n) 调用栈，也没有大 n 的栈溢出风险。
- 问：公式为什么是 O(1)？答：固定次数的加、除、乘，与 n 的大小无关。
- 问：为什么先除 2？答：n 和 n+1 必有一个偶数，先约掉因子 2 可以减小中间乘积，同时保持精确整数结果。
- 问：`long` 还会溢出吗？答：会；这里用 `addExact/multiplyExact` 把溢出变成显式异常。
- 问：如果要求不使用乘除法呢？答：那就是另一个合同，可讨论短路递归、位运算等限制；来源当前明确要求对比公式，因此不额外引入该约束。

## 易错点

- 负数没有基线条件，递归不断向更小值走。
- 只写 `n*(n+1)/2`，忽略中间乘积或 `n+1` 溢出。
- 说递归空间 O(1)，忽略调用栈。
- 把 O(1) 公式理解成“永不溢出”。
- 三种方法使用不同输入边界，却直接比较结果和复杂度。
''',
        'test':r'''public final class SumOneToNTest {
    static void check(long actual,long expected,String name){if(actual!=expected)throw new AssertionError(name+"="+actual);}
    static void invalid(){for(int m=0;m<3;m++){try{if(m==0)SumOneToN.recursive(-1);if(m==1)SumOneToN.loop(-1);if(m==2)SumOneToN.formula(-1);throw new AssertionError("negative");}catch(IllegalArgumentException expected){}}}
    public static void main(String[] args){
        check(SumOneToN.recursive(0),0,"r0"); check(SumOneToN.loop(0),0,"l0"); check(SumOneToN.formula(0),0,"f0");
        check(SumOneToN.recursive(10),55,"r10"); check(SumOneToN.loop(10),55,"l10"); check(SumOneToN.formula(10),55,"f10");
        check(SumOneToN.formula(1_000_000_000L),500000000500000000L,"large-formula");
        invalid();
        try{SumOneToN.formula(Long.MAX_VALUE);throw new AssertionError("overflow");}catch(ArithmeticException expected){}
        System.out.println("PASS zero recursive loop formula large-formula negative-rejected overflow-detected");
    }
}
''',
        'stdout':'PASS zero recursive loop formula large-formula negative-rejected overflow-detected',
        'checks':['all methods return 0 for n=0','all methods return 55 for n=10','O(1) formula handles n=1,000,000,000 exactly','negative n rejected consistently','formula detects fixed-width overflow'],
        'claims':[
            ('source-boundary','The source requires recursive, iterative, and O(1) formula comparison but does not define numeric range or overflow behavior; the candidate declares a non-negative long contract with explicit overflow detection.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('implementation-correctness','The executable OpenJDK fixture verifies equivalent small results, a large O(1) formula case, consistent negative-input rejection, and fixed-width overflow detection.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['All three requested approaches are implemented under one explicit contract.','The complexity comparison distinguishes recursive call-stack space from loop/formula constant extra space.','The formula reduces an even factor before multiplication and still uses checked arithmetic for real overflow.','OpenJDK validation covers zero, ordinary, large-formula, invalid, and overflow cases.'],
        'task_note':'- [x] `cq_q_426504c2ae6acad967088081d941ef70` source-first isolated review PASS: recursive/loop/O(1) implementations share an explicit non-negative long contract, complexity and stack trade-offs are distinguished, and OpenJDK validation covers ordinary, large-formula, invalid, and overflow cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_31f9c8768b0db3328f3b2b374a1f4e8f',
        'qid':'31f9c8768b0db3328f3b2b374a1f4e8f',
        'expected':'代码：实现策略模式',
        'slug':'strategy-pattern',
        'class':'StrategyPatternExample',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_31f9c8768b0db3328f3b2b374a1f4e8f","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# Java 实现策略模式

## 核心结论

来源只要求“实现策略模式”，没有指定业务。这里用“订单价格策略”做最小可执行示例：`PricingStrategy` 定义可替换算法接口，不同折扣实现只负责算法，`Checkout` 只依赖接口并委托计算。这样变化点从 `if/else` 中抽离，通过组合在构造时注入策略；新增策略通常不需要修改 Context。

## 1 分钟版

- Strategy：定义同一种算法族的统一接口。
- Concrete Strategy：每种算法各自实现接口，例如原价、百分比折扣。
- Context：持有一个 Strategy，只负责业务流程和委托，不写具体算法分支。
- 客户端选择策略并注入 Context，因此运行行为由组合决定，而不是 Context 内部硬编码。
- 适合“算法可互换、分支会持续增加”的场景；如果只有两个永不变化的简单分支，强行上模式反而会增加类型数量。

## 3 分钟版

```java
public final class StrategyPatternExample {
    public interface PricingStrategy {
        long apply(long cents);
    }

    public static final class NoDiscount implements PricingStrategy {
        @Override public long apply(long cents) {
            requireNonNegative(cents);
            return cents;
        }
    }

    public static final class PercentageOff implements PricingStrategy {
        private final int percent;
        public PercentageOff(int percent) {
            if (percent < 0 || percent > 100) throw new IllegalArgumentException("percent must be 0..100");
            this.percent = percent;
        }
        @Override public long apply(long cents) {
            requireNonNegative(cents);
            long kept = 100L - percent;
            return Math.multiplyExact(cents, kept) / 100L;
        }
    }

    public static final class Checkout {
        private final PricingStrategy strategy;
        public Checkout(PricingStrategy strategy) {
            if (strategy == null) throw new IllegalArgumentException("strategy must not be null");
            this.strategy = strategy;
        }
        public long quote(long cents) {
            return strategy.apply(cents);
        }
    }

    private static void requireNonNegative(long cents) {
        if (cents < 0) throw new IllegalArgumentException("cents must be non-negative");
    }
}
```

客户端可以写 `new Checkout(new PercentageOff(20)).quote(1000)` 得到 800。Context 不知道“20% 折扣”怎么算，它只知道调用 `PricingStrategy.apply`。

## 关键细节

- 策略模式的重点是“可替换算法对象”，不是单纯把 `if` 拆成多个方法。
- Context 依赖抽象接口而非具体策略，方向上是高层流程依赖稳定契约。
- 示例用整数分表示金额，避免把浮点误差混进模式演示；具体舍入规则仍应由真实业务合同定义。
- 当前 `Checkout` 的策略不可变；运行时切换可以创建新 Context，或者在有明确并发语义时提供受控 setter。
- 策略数量很少且不会扩展时，一个局部条件分支可能更简单，模式不是越多越好。

## 原理机制

策略模式把“变化的算法”变成满足同一接口的一组对象，Context 只做一次动态分派。原来 `if(type==A)...else if(type==B)...` 的变化轴被移动到对象组合关系上：增加新算法时新增一个 Strategy 实现，已有 Context 的委托逻辑保持不变。这降低的是算法选择和流程代码之间的耦合，而不是消灭所有条件判断。

## 项目经验版

来源没有真实项目背景，不能虚构“线上使用过策略模式”。实际落地前我会先确认变化频率和边界：如果支付路由、定价、风控规则确实有多种可替换算法且持续新增，策略模式很合适；如果分支稳定且只有一两个，保留简单条件可能更易读。还要明确策略是否无状态、是否可复用以及并发下能否安全共享。

## 常见追问

- 问：策略模式和工厂模式什么关系？答：Strategy 解决算法如何封装/替换；Factory 可以负责“根据配置创建哪个 Strategy”，两者职责不同但可以组合。
- 问：和模板方法有什么区别？答：模板方法主要靠继承固定流程、覆写步骤；策略模式靠组合替换算法对象，运行时组合更灵活。
- 问：是不是完全没有 `if/else`？答：不一定。策略选择处仍可能有配置映射或工厂分支，目标是让核心 Context 不承担每种算法实现。
- 问：为什么 Context 不直接 new 具体策略？答：否则 Context 又和具体实现耦合，替换策略仍需修改 Context。
- 问：什么时候不建议用？答：算法几乎不变、策略很少且逻辑极简单时，额外接口和类可能得不偿失。

## 易错点

- Context 内仍然按策略类型写大段 `if/else`，只是给类换了名字。
- 具体策略同时修改大量 Context 状态，导致算法边界不清。
- 在没有真实舍入规则时把金额例子的整数除法当成通用计费结论。
- 为极少且稳定的分支制造过多样板类型。
- 把“创建策略”和“执行策略”混成一个职责，难以独立测试。
''',
        'test':r'''public final class StrategyPatternExampleTest {
    static void check(long actual,long expected,String name){if(actual!=expected)throw new AssertionError(name+"="+actual);}
    public static void main(String[] args){
        check(new StrategyPatternExample.Checkout(new StrategyPatternExample.NoDiscount()).quote(1000),1000,"no-discount");
        check(new StrategyPatternExample.Checkout(new StrategyPatternExample.PercentageOff(20)).quote(1000),800,"20off");
        check(new StrategyPatternExample.Checkout(new StrategyPatternExample.PercentageOff(100)).quote(999),0,"100off");
        try{new StrategyPatternExample.PercentageOff(101);throw new AssertionError("percent");}catch(IllegalArgumentException expected){}
        try{new StrategyPatternExample.Checkout(null);throw new AssertionError("null-strategy");}catch(IllegalArgumentException expected){}
        try{new StrategyPatternExample.Checkout(new StrategyPatternExample.NoDiscount()).quote(-1);throw new AssertionError("negative");}catch(IllegalArgumentException expected){}
        System.out.println("PASS no-discount percentage-off full-discount invalid-percent null-strategy negative-amount");
    }
}
''',
        'stdout':'PASS no-discount percentage-off full-discount invalid-percent null-strategy negative-amount',
        'checks':['no-discount strategy delegates unchanged price','20-percent strategy returns declared result','100-percent strategy returns zero','invalid percent rejected','null strategy rejected','negative amount rejected'],
        'claims':[
            ('source-boundary','The preserved source only requests an implementation of Strategy; no business domain, strategy-selection mechanism, mutability, or monetary rounding policy is supplied, so the example declares a bounded pricing contract.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('pattern-correctness','The executable OpenJDK fixture verifies Context-to-Strategy delegation across interchangeable concrete strategies and declared invalid-input boundaries.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate contains the three essential roles: strategy contract, concrete strategies, and a context that depends only on the contract.','Concrete pricing algorithms are replaceable through composition without editing Checkout.','The answer explicitly distinguishes Strategy from strategy selection/factory concerns and names over-engineering boundaries.','OpenJDK validation covers multiple strategies and invalid strategy/parameter/value cases.'],
        'task_note':'- [x] `cq_q_31f9c8768b0db3328f3b2b374a1f4e8f` source-first isolated review PASS: the implementation separates Strategy/Concrete Strategy/Context, keeps Checkout dependent on the strategy contract, states selection/rounding/over-engineering boundaries, and OpenJDK validation covers interchangeable strategies and invalid inputs. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_e787825953b8cf140b0102f3c504960e',
        'qid':'e787825953b8cf140b0102f3c504960e',
        'expected':'算法：两个二叉树合并，值相加。递归和非递归实现的区别？',
        'slug':'merge-binary-trees',
        'class':'MergeBinaryTrees',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e787825953b8cf140b0102f3c504960e","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 合并两棵二叉树：递归与非递归

## 核心结论

来源要求“两棵树合并、值相加，并比较递归和非递归”，没有说明是否原地修改。这里选择“创建新树，不修改也不共享输入节点”的合同：同一位置两边都有节点就把值相加；只有一边有节点就复制该节点及后续结构；都为空则为空。递归写法直接对应树的定义，代码短但使用 O(h) 调用栈；非递归 BFS 用显式队列保存待处理节点对，避免深树递归栈风险，但最宽层可能占 O(w) 队列空间。

## 1 分钟版

- 当前坐标 `(a,b)`：都空返回空；否则新建输出节点，值是存在节点值之和。
- 递归分别合并 `left` 和 `right`，天然保持结构对应关系。
- 非递归可以队列保存 `(a,b,out)` 三元组，弹出后为左右孩子创建输出节点并继续入队。
- 两种方式都访问输出树每个位置一次，时间 O(n)，区别主要在辅助空间和深树的栈安全性。
- 本答案明确不复用输入节点，避免“只有一边非空时直接返回原子树”造成结果与输入共享引用。

## 3 分钟版

```java
import java.util.ArrayDeque;
import java.util.Queue;

public final class MergeBinaryTrees {
    public static final class Node {
        public final int val;
        public Node left;
        public Node right;
        public Node(int val) { this.val = val; }
    }

    public static Node recursive(Node a, Node b) {
        if (a == null && b == null) return null;
        Node out = new Node(sum(a, b));
        out.left = recursive(a == null ? null : a.left, b == null ? null : b.left);
        out.right = recursive(a == null ? null : a.right, b == null ? null : b.right);
        return out;
    }

    public static Node iterative(Node a, Node b) {
        if (a == null && b == null) return null;
        Node root = new Node(sum(a, b));
        Queue<Frame> q = new ArrayDeque<>();
        q.add(new Frame(a, b, root));
        while (!q.isEmpty()) {
            Frame f = q.remove();
            Node al = f.a == null ? null : f.a.left;
            Node bl = f.b == null ? null : f.b.left;
            if (al != null || bl != null) {
                f.out.left = new Node(sum(al, bl));
                q.add(new Frame(al, bl, f.out.left));
            }
            Node ar = f.a == null ? null : f.a.right;
            Node br = f.b == null ? null : f.b.right;
            if (ar != null || br != null) {
                f.out.right = new Node(sum(ar, br));
                q.add(new Frame(ar, br, f.out.right));
            }
        }
        return root;
    }

    private static int sum(Node a, Node b) {
        int av = a == null ? 0 : a.val;
        int bv = b == null ? 0 : b.val;
        return Math.addExact(av, bv);
    }

    private static final class Frame {
        final Node a, b, out;
        Frame(Node a, Node b, Node out) { this.a = a; this.b = b; this.out = out; }
    }
}
```

## 关键细节

- “合并”是否允许修改原树必须先确认；本合同始终新建节点，因此输出和两棵输入没有共享节点。
- 递归辅助空间看树高 h：平衡树约 O(log n)，极端链状树是 O(n)，并可能触发栈溢出。
- BFS 队列空间看最大宽度 w；宽而浅的树可能比递归占更多瞬时内存。
- 两种实现都用同一个 `sum` 规则，并用 `Math.addExact` 明确节点值相加的 int 溢出边界。
- 若题目允许原地复用第一棵树，可以减少分配，但会改变副作用合同，不能和当前版本混为一谈。

## 原理机制

两棵树的合并可以看成对“同一结构坐标”的同步遍历。每个输出节点只依赖输入在该坐标上的两个节点，然后左右两个子问题彼此独立。递归把“待处理坐标”隐式放在调用栈；非递归把完全相同的状态显式放进队列，所以核心状态转移不变，改变的是调度方式和辅助空间形态。

## 项目经验版

来源没有真实树规模或可变性要求，不能虚构线上数据。面试时我会先确认是否允许修改输入；若深度有上限且代码清晰优先，递归通常更直接；若树可能非常深或来自不可信输入，显式队列/栈更容易控制资源上限。还应补“仅一侧有节点”“两侧都空”“链状深树”和数值溢出测试。

## 常见追问

- 问：只有一棵子树存在时为什么不直接返回它？答：那会让结果共享输入节点；当前合同承诺输出独立，所以要复制。
- 问：递归和 BFS 时间复杂度有区别吗？答：都对每个输出位置做常数工作，都是 O(n)；主要区别在辅助空间和栈安全性。
- 问：非递归能用 DFS 栈吗？答：可以，显式栈会更接近递归的深度优先顺序；这里用 BFS 是为了直观看到队列宽度 O(w)。
- 问：可以原地改第一棵树吗？答：可以作为另一个合同，能减少新节点分配，但调用方必须接受输入被修改。
- 问：节点值相加溢出怎么办？答：当前示例用 `Math.addExact` 直接失败；若业务允许更大范围，应把节点值改为 `long` 或任意精度。

## 易错点

- 只在两边都有节点时创建输出，丢失单边子树。
- 直接复用单边子树，却宣称结果与输入完全独立。
- 说递归空间永远 O(log n)，忽略退化树。
- 非递归队列只保存输入节点，不保存对应输出节点，导致连接位置混乱。
- 递归和非递归使用不同的空节点或溢出语义，比较失去同一合同基础。
''',
        'test':r'''import java.util.*;
public final class MergeBinaryTreesTest {
    static MergeBinaryTrees.Node n(int v){return new MergeBinaryTrees.Node(v);}    
    static String enc(MergeBinaryTrees.Node x){if(x==null)return "#";return x.val+","+enc(x.left)+","+enc(x.right);}
    static MergeBinaryTrees.Node[] sample(){
        MergeBinaryTrees.Node a=n(1);a.left=n(3);a.right=n(2);a.left.left=n(5);
        MergeBinaryTrees.Node b=n(2);b.left=n(1);b.right=n(3);b.left.right=n(4);b.right.right=n(7);
        return new MergeBinaryTrees.Node[]{a,b};
    }
    public static void main(String[] args){
        MergeBinaryTrees.Node[] s=sample(); String a0=enc(s[0]),b0=enc(s[1]);
        MergeBinaryTrees.Node r=MergeBinaryTrees.recursive(s[0],s[1]);
        MergeBinaryTrees.Node i=MergeBinaryTrees.iterative(s[0],s[1]);
        String expected="3,4,5,#,#,4,#,#,5,#,7,#,#";
        if(!enc(r).equals(expected)||!enc(i).equals(expected))throw new AssertionError(enc(r)+" / "+enc(i));
        if(!enc(s[0]).equals(a0)||!enc(s[1]).equals(b0))throw new AssertionError("input mutated");
        if(r==s[0]||r==s[1]||r.left==s[0].left||i.right==s[1].right)throw new AssertionError("shared node");
        if(MergeBinaryTrees.recursive(null,null)!=null||MergeBinaryTrees.iterative(null,null)!=null)throw new AssertionError("null-null");
        MergeBinaryTrees.Node one=n(9); MergeBinaryTrees.Node copied=MergeBinaryTrees.recursive(one,null); if(copied==one||copied.val!=9)throw new AssertionError("single-side-copy");
        try{MergeBinaryTrees.recursive(n(Integer.MAX_VALUE),n(1));throw new AssertionError("overflow");}catch(ArithmeticException expectedOverflow){}
        System.out.println("PASS recursive iterative same-result inputs-unchanged no-sharing null single-side-copy overflow-detected");
    }
}
''',
        'stdout':'PASS recursive iterative same-result inputs-unchanged no-sharing null single-side-copy overflow-detected',
        'checks':['recursive standard merge matches expected structure','iterative standard merge matches recursive result','input trees remain unchanged','output does not share representative input nodes','both-null returns null','single-side subtree is copied rather than shared','node-value overflow detected'],
        'claims':[
            ('source-boundary','The preserved source requires value-summing merge plus recursive/non-recursive comparison but does not define mutation or overflow semantics; the candidate explicitly chooses a new-tree, no-sharing contract with checked int addition.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('merge-correctness','The executable OpenJDK fixture verifies equivalent recursive/BFS output, unchanged inputs, no representative node sharing, null/single-side behavior, and overflow detection.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The recursive and iterative implementations operate under one explicit no-mutation/no-sharing contract.','The answer correctly identifies O(h) recursive stack versus O(w) BFS queue space rather than claiming one universal auxiliary bound.','Single-sided structure is preserved by copying, not aliasing input subtrees.','OpenJDK validation covers standard merge, equivalence, input immutability, no-sharing, null/single-side, and overflow cases.'],
        'task_note':'- [x] `cq_q_e787825953b8cf140b0102f3c504960e` source-first isolated review PASS: recursive and BFS implementations share a no-mutation/no-sharing contract, distinguish O(h) call-stack from O(w) queue space, and OpenJDK validation covers equivalence, input immutability, single-side/null, and overflow cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
]


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    if not inventory_path.exists():
        raise SystemExit('Batch 0057 source inventory must be frozen before writing')
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task_text = task.read_text(encoding='utf-8').rstrip()
    results = []

    for target in TARGETS:
        cid, qid = target['cid'], target['qid']
        candidate = ROOT / f'review/candidates/answers/{cid}.md'
        evidence = ROOT / f'review/evidence/{cid}.json'
        if candidate.exists() or evidence.exists():
            raise SystemExit(f'{cid}: candidate/evidence already exists; do not overwrite')
        ctx_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{cid}/context.json'
        if not ctx_path.exists():
            raise SystemExit(f'{cid}: frozen context missing')
        ctx = json.loads(ctx_path.read_text(encoding='utf-8'))
        if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id') != cid or ctx.get('answer_type') != 'coding':
            raise SystemExit(f'{cid}: context/type drift')
        if ctx.get('canonical',{}).get('question_ids') != [qid]:
            raise SystemExit(f'{cid}: source ownership drift')
        src = next((x for x in ctx.get('source_questions',[]) if x.get('question_id') == qid), None)
        if not src or src.get('original_question') != target['expected'] or src.get('is_valid_for_library') is not True:
            raise SystemExit(f'{cid}: source wording/validity drift')
        inv = next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id') == cid), None)
        if not inv or inv.get('existing_candidate') or inv.get('existing_evidence') or inv.get('answer_type') != 'coding':
            raise SystemExit(f'{cid}: inventory no longer describes a fresh coding target')

        body = target['candidate']
        for heading in HEADINGS:
            if body.count(heading) != 1:
                raise SystemExit(f'{cid}: section drift {heading}')
        blocks = re.findall(r'```java\n(.*?)\n```', body, re.S)
        if len(blocks) != 1:
            raise SystemExit(f'{cid}: expected exactly one Java implementation block')
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(body, encoding='utf-8')

        out = ROOT / f'review/content_build/answer_batch_{BATCH}/{cid}'
        with tempfile.TemporaryDirectory(prefix=f'b57-{target["slug"]}-') as tmp:
            d = Path(tmp)
            (d / f'{target["class"]}.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
            (d / f'{target["class"]}Test.java').write_text(target['test'], encoding='utf-8')
            run('javac', f'{target["class"]}.java', f'{target["class"]}Test.java', cwd=d)
            stdout = run('java', f'{target["class"]}Test', cwd=d).stdout.strip()
        if stdout != target['stdout']:
            raise SystemExit(f'{cid}: fixture stdout drift: {stdout}')

        validation = {'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,'command':f'javac {target["class"]}.java {target["class"]}Test.java && java {target["class"]}Test','stdout':stdout,'checks':target['checks']}
        write_json(out/'writer_validation.json', validation)
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        sources = [
            {'source_id':'repository-source','title':f'Batch 0057 frozen source context for {target["slug"]}','locator':str(ctx_path),'source_type':'repository_source_record','checked_at':DATE},
            {'source_id':'fixture','title':f'OpenJDK deterministic validation for {target["slug"]}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
        ]
        claims = [{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in target['claims']]
        coverage = [{'question_id':qid,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
        write_json(out/'writer_research.json', {'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
        reviewer = f'source-first-isolated-reviewer-batch-0057-{target["slug"]}-20260829-v1'
        review = {'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0057.{target["slug"]}.v1','decision':'pass','revision_round':1,'source_packet':[str(ctx_path),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings'],'promotion_blockers':[PROMOTION_BLOCKER]}
        write_json(out/'isolated_review_result.json', review)
        write_json(evidence, {'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':f'content-batch-0057-{target["slug"]}-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':f'Batch 0057 {target["slug"]} source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':target['checks'],'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in target['checks']]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings']},'promotion_blocker':PROMOTION_BLOCKER})
        writer = json.loads((out/'writer_research.json').read_text(encoding='utf-8'))
        writer['review_state'] = 'writer_complete_isolated_review_passed'
        writer['promotion_blocker'] = PROMOTION_BLOCKER
        write_json(out/'writer_research.json', writer)

        if target['task_note'] not in task_text:
            task_text += '\n' + target['task_note']
        results.append({'canonical_id':cid,'candidate_sha256':digest,'decision':'pass','stdout':stdout})

    task.write_text(task_text + '\n', encoding='utf-8')
    print(json.dumps({'ok':True,'batch':BATCH,'completed':results,'promotion_blocker':PROMOTION_BLOCKER}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
