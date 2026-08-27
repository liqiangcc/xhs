<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_b70fe7ccca588e38ec4c4ad817cb97c8","version":1,"status":"draft","updated_at":"2026-08-27","answer_type":"coding","quality_tier":"candidate"} -->
# 使用两个队列实现一个栈

## 核心结论

队列是 FIFO，栈是 LIFO，所以关键是让“最后 push 的元素”在需要 pop/top 时位于队首。这里采用一个明确的参考实现：`q1` 始终保存按“栈顶 → 栈底”顺序排列的全部元素，`q2` 只在 `push` 时做辅助。每次 push 新元素时，先把它放进空的 `q2`，再把 `q1` 的旧元素全部搬到 `q2`，最后交换两个队列。这样 push 是 O(n)，而 pop/top 都是 O(1)。

来源只问“两个队列实现栈”，没有指定必须让 push 还是 pop 更快，因此也可以选择 push O(1)、pop O(n) 的方案；面试时先说清复杂度取舍即可。

## 1 分钟版

- 维护两个队列 `q1`、`q2`，约定操作结束后 `q2` 为空，`q1` 的队首就是栈顶。
- `push(x)`：先 `q2.offer(x)`，再把 `q1` 中元素依次全部搬到 `q2`，然后交换 `q1/q2`。
- `pop()`：直接从 `q1` 队首出队；因为最新元素已在最前面，所以满足 LIFO。
- `top()`：直接读取 `q1` 队首。
- `empty()`：判断 `q1` 是否为空。
- 复杂度：push O(n)，pop/top/empty O(1)，总空间 O(n)。

## 3 分钟版

设栈里从顶到底是 `[c,b,a]`，那么维护不变量：`q1` 从队首到队尾也正好是 `[c,b,a]`。此时 pop 只需要 `q1.remove()`。

当继续 push `d` 时，不能直接追加到 `q1` 尾部，因为那会得到 `[c,b,a,d]`，队首仍然不是最新元素。于是先把 `d` 放到空 `q2`，得到 `[d]`；再把 `q1` 依次搬过去，得到 `[d,c,b,a]`；交换引用后，新 `q1` 再次满足“队首 = 栈顶”的不变量。

```java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.NoSuchElementException;

public final class Solution {
    public static final class MyStack {
        private Deque<Integer> q1 = new ArrayDeque<>();
        private Deque<Integer> q2 = new ArrayDeque<>();

        public void push(int x) {
            q2.addLast(x);
            while (!q1.isEmpty()) {
                q2.addLast(q1.removeFirst());
            }
            Deque<Integer> tmp = q1;
            q1 = q2;
            q2 = tmp;
        }

        public int pop() {
            if (q1.isEmpty()) throw new NoSuchElementException("empty stack");
            return q1.removeFirst();
        }

        public int top() {
            if (q1.isEmpty()) throw new NoSuchElementException("empty stack");
            return q1.getFirst();
        }

        public boolean empty() {
            return q1.isEmpty();
        }
    }
}
```

空栈的 pop/top 在这个参考契约里显式抛 `NoSuchElementException`。如果题目平台定义了别的行为，应按平台 API 调整，不要把这个异常策略冒充成原题要求。

## 关键细节

- **循环不变量**：每次公开操作结束后，`q2` 为空；`q1` 队首到队尾对应栈顶到栈底。
- **为什么要先放新元素**：队列只能尾进头出，新元素必须先进入辅助队列，旧元素随后接在它后面，才能把最新元素旋到队首。
- **交换的是引用**：搬运完成后交换 `q1/q2`，不需要再把所有元素搬回来。
- **复杂度选择不是唯一**：也可让 push O(1)，在 pop 时把前 n-1 个元素搬到辅助队列，最后弹出第 n 个；两种方案都只使用两个队列。
- **这里的 `Deque` 只按队列接口使用**：只调用 `addLast/removeFirst/getFirst`，没有使用尾部弹出模拟栈，否则会绕过题目约束。
- **空栈语义**：来源未规定，本答案选择显式异常；真实平台题要以接口契约为准。

## 原理机制

两种数据结构的差异是输出顺序：队列保持到达顺序，栈要求逆序。这个方案把“逆序成本”全部支付在 push 上：每来一个新元素，就把它旋转到所有旧元素之前。因此 q1 始终已经处于可直接弹栈的顺序。若栈当前有 n 个元素，push 需要搬 n 个旧元素，所以是 O(n)；随后 pop/top 不再需要重排。

## 项目经验版

来源没有提供真实项目经历，不能虚构“线上用两个队列实现栈”的案例。工程上通常不会这样实现栈，因为语言标准库已有栈/双端队列；这道题的价值是验证你能否用受限操作维护不变量，并清楚解释把复杂度放在 push 还是 pop 上的取舍。

## 常见追问

- 问：为什么两个队列可以实现 LIFO？答：每次 push 都把新元素先放进辅助队列，再把旧元素接到后面，使主队列从队首到队尾始终等于栈顶到栈底。
- 问：能不能让 push O(1)？答：可以。push 直接入主队列；pop 时把前 n-1 个元素搬到辅助队列，最后剩下的元素就是栈顶，再交换两队列。
- 问：为什么不直接用 `Deque.removeLast()`？答：那等于直接使用双端队列的栈能力，绕过了“只能按普通队列 FIFO 操作”的题目约束。
- 问：这个方案的空间复杂度是多少？答：两队列合计最多保存 n 个有效元素，辅助搬运不会复制元素总数，所以是 O(n)。
- 问：连续 push 后顺序怎么证明？答：归纳即可：假设操作前 q1 顺序等于栈顶到栈底；新元素先进入 q2，旧 q1 顺序原样接在其后，交换后不变量继续成立。

## 易错点

- 直接把新元素追加到主队列尾部，却又期待队首是栈顶。
- 搬运后忘记交换两个队列，或者没有保证辅助队列在下一次 push 前为空。
- 为了方便偷偷调用双端队列的 `removeLast`，实际没有遵守“队列实现栈”的限制。
- 只给代码，不说明选择了 push O(n) 还是 pop O(n)，导致复杂度取舍不清楚。
- 对空栈返回魔法值而不声明契约，可能与合法数据冲突。
