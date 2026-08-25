<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_0b2b60b3fcf31abae6c4bff516b07ade","version":1,"status":"draft","updated_at":"2026-08-21","quality_tier":"candidate","answer_type":"coding"} -->
# 二叉树路径总和：先锁定 Path Sum 112 的根到叶语义

## 核心结论

仓库现在保留两条归一到同一 Path Sum 主题的来源：一条腾讯记录只写“算法：二叉树路径总和”，没有保留具体变体；另一条字节记录写“算法手撕：二叉树路径总和（Path Sum）”，且它的 tagged record 明确映射为 **LeetCode 112**。因此不能把 112 语义冒充成腾讯泛化来源的原题事实；下面把“泛化来源的变体缺口”和“字节来源的 112 显式映射”分开。按 112 映射，目标是判断是否存在一条**从根节点到叶子节点**的路径，使沿途节点值之和等于 `targetSum`。LeetCode 官方题面也明确规定 leaf 是“没有子节点的节点”，因此“某个中间前缀刚好等于目标值”不能提前返回成功。

最直接的面试解法是 DFS：把“还差多少”作为递归状态向下传。到达叶子时只检查 `remaining - node.val == 0`。每个节点最多访问一次，时间复杂度 `O(n)`；递归辅助空间是树高 `O(h)`。如果调用栈深度是工程约束，可以把相同状态显式放入栈，避免依赖 JVM 递归深度。

## 1 分钟版

先说明题意边界：腾讯泛化来源本身不足以唯一确定 Path Sum 变体；这里的可执行实现按另一条仓库来源显式映射的 LeetCode 112，求“是否存在根到叶路径”，不是返回所有路径，也不是统计任意向下路径。

递归函数定义为：`hasPathSum(node, remaining)` 表示从当前节点出发，是否能走到某个叶子，使这段路径节点和恰好等于 `remaining`。

- 空节点：`false`。
- 当前是叶子：只判断 `remaining - node.val == 0`。
- 非叶子：把 `remaining - node.val` 传给左右子树，任一成功即可。

关键易错点是**必须在叶子处判定**。例如根到某个内部节点的前缀已经等于目标值，但该节点还有孩子，这条路径还没有结束，不能算 LeetCode 112 的答案。

## 3 分钟版

这个 DFS 的不变量是：进入节点 `node` 时，`remaining` 始终等于“从当前节点开始直到某个叶子，仍需凑出的总和”。消费当前节点值后得到 `next = remaining - node.val`；如果当前节点已经是叶子，那么不存在后续选择，`next == 0` 正好等价于一条合法根到叶路径满足目标和。

如果当前节点不是叶子，就不能仅因为 `next == 0` 返回 `true`。继续向孩子递归，才保持“路径必须结束于叶子”的题目约束。左右子树之间是存在性关系，所以用逻辑 OR；Java 的短路语义还能在左侧已经找到答案时避免无意义搜索右侧。

官方约束允许空树，因此空树返回 `false`。节点值可以为负数，所以不能使用“当前累计和已经超过 target 就剪枝”这类只对全非负输入成立的优化。官方 112 的节点规模上限为 5000；递归写法最简洁，但 JVM 栈容量不是题目语义的一部分，因此工程实现若要对退化深树更稳健，可以使用显式 `Deque`。下面同一份代码同时给出递归版和迭代版，二者共享完全相同的根到叶契约。

## 关键细节

- 两条 source variant 都只在题名层面指向“二叉树路径总和 / Path Sum”；其中只有字节 tagged record 显式写了 `LeetCode 112`。因此 112 是该来源的仓库映射，不是从腾讯泛化题名自行猜出的约束。
- LeetCode 112 返回布尔值：只判断是否存在至少一条匹配路径。
- 合法路径必须从根开始并在叶子结束；内部节点前缀不能作为成功条件。
- `root == null` 时不存在根到叶路径，因此返回 `false`。
- 负数节点合法，不能用基于“和只会增大”的剪枝。
- 递归版时间 `O(n)`、辅助空间 `O(h)`；最坏退化树 `h = n`。
- 迭代版同样是 `O(n)` 时间和最坏 `O(h)` 显式栈空间，但不占用 Java 调用栈。
- 状态中的剩余和使用 `long`，避免把实现正确性无谓绑定到更窄的中间算术范围；公开参数仍保持题目常见的 `int targetSum`。

## 原理机制

```java
import java.util.ArrayDeque;
import java.util.Deque;

public final class PathSum {
    public static final class TreeNode {
        final int val;
        TreeNode left;
        TreeNode right;

        TreeNode(int val) {
            this.val = val;
        }
    }

    public static boolean hasPathSumRecursive(TreeNode root, int targetSum) {
        return hasPathSumRecursive(root, (long) targetSum);
    }

    private static boolean hasPathSumRecursive(TreeNode node, long remaining) {
        if (node == null) {
            return false;
        }

        long next = remaining - node.val;
        if (node.left == null && node.right == null) {
            return next == 0L;
        }
        return hasPathSumRecursive(node.left, next)
                || hasPathSumRecursive(node.right, next);
    }

    public static boolean hasPathSumIterative(TreeNode root, int targetSum) {
        if (root == null) {
            return false;
        }

        Deque<State> stack = new ArrayDeque<>();
        stack.push(new State(root, (long) targetSum));
        while (!stack.isEmpty()) {
            State current = stack.pop();
            TreeNode node = current.node;
            long next = current.remaining - node.val;

            if (node.left == null && node.right == null && next == 0L) {
                return true;
            }
            if (node.right != null) {
                stack.push(new State(node.right, next));
            }
            if (node.left != null) {
                stack.push(new State(node.left, next));
            }
        }
        return false;
    }

    private static final class State {
        final TreeNode node;
        final long remaining;

        State(TreeNode node, long remaining) {
            this.node = node;
            this.remaining = remaining;
        }
    }
}
```

仓库中的确定性测试没有复制“剩余和递归”作为 oracle。独立 oracle 用 BFS 枚举所有**根到叶**路径的累计和集合，再判断目标值是否在集合中；固定用例覆盖空树、单节点、经典命中、内部前缀伪命中、负数节点等边界，并用固定随机种子生成 3000 棵树，把递归版和迭代版都与独立 oracle 对照。另有 5000 节点单链只验证迭代版，以证明显式栈路径不依赖 JVM 递归深度。

## 项目经验版

这是算法手撕题，原始材料没有生产项目指标，不应虚构“线上优化收益”。工程上真正值得迁移的是契约意识：同一个“Path Sum”名字可以指存在性、返回全部路径或任意向下路径计数；实现前先锁定“起点、终点、返回值”三个维度，否则代码即使自洽，也可能答错题。

## 常见追问

- 问：为什么不能在累计和等于 target 时立即返回？答：112 要求路径结束于叶子；当前节点还有孩子时只是前缀匹配，不是合法根到叶路径。
- 问：为什么不能在累计和超过 target 时剪枝？答：节点值允许为负，后续节点可能把总和拉回目标值。
- 问：Path Sum II 有什么不同？答：II 要返回所有满足条件的根到叶路径，因此需要维护路径内容并回溯，而不是只返回布尔存在性。
- 问：Path Sum III 有什么不同？答：III 统计任意向下路径，路径不要求从根开始或在叶子结束，通常会转成前缀和计数问题；不能复用 112 的“只在叶子判定”契约。
- 问：递归会不会栈溢出？答：算法空间复杂度本来就是 `O(h)`；递归把这部分状态放在调用栈。若运行环境对深度敏感，用显式栈保持同一 DFS 状态机即可。
- 问：如何证明代码不是只过样例？答：把实现与结构不同的“BFS 枚举全部根到叶路径和”oracle 在大量固定种子随机树上逐项比较，并单独覆盖内部前缀、负数和深链边界。

## 易错点

- 把“路径和等于目标”误写成任意前缀匹配，遗漏叶子约束。
- 把 Path Sum 112、113、437 三种不同问题混为一谈。
- 看到目标值后做“超过就剪枝”，忽略负数输入。
- 空树时把 `targetSum == 0` 错当成存在一条空路径。
- 只给递归代码却声称额外空间 `O(1)`；递归调用栈实际是 `O(h)`。
- 在没有真实项目材料时编造生产规模、延迟或收益。
