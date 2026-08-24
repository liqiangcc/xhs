<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_2f07ba5f8d6e6ad366d2cd13c6d1d1ab","version":1,"status":"draft","updated_at":"2026-08-24","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：手撕实现无向图的深拷贝

## 核心结论

仓库原始来源只保留了“无向图的深拷贝”，没有规定节点字段、输入入口、语言、空输入、邻接表是否允许重复边或完整图是否保证连通。这里显式采用候选契约：Java 节点包含 `int value` 和有序 `List<Node> neighbors`；输入是一个起始节点，返回它所在可达连通分量的深拷贝；`null` 返回 `null`；保留邻接表顺序、自环和重复邻接项；克隆图与原图不共享任何节点对象。

关键不是“复制每条边”本身，而是必须维护 **原节点 → 克隆节点** 的一一映射。第一次遇到原节点时只创建一个克隆；以后再次遇到同一个原节点——无论来自环、自环、共享邻居还是重复边——都复用同一个克隆对象。这样既避免无限遍历，也保证图中的别名关系和环结构被正确复制。

## 1 分钟版

我会用 BFS 或 DFS 加一个 `Map<Original, Clone>`。

以 BFS 为例：

1. `start == null` 直接返回 `null`。
2. 先创建起点的克隆并放进映射，同时把原起点入队。
3. 每次取一个原节点，遍历它的邻居。
4. 邻居没见过，就创建对应克隆、写入映射并把原邻居入队；已经见过就直接复用映射中的克隆。
5. 把邻居克隆按原邻接表顺序追加到当前克隆的 `neighbors`。

最终返回 `map.get(start)`。若可达分量有 `V` 个节点、邻接表总长度为 `E_adj`，时间 `O(V + E_adj)`，映射和队列辅助空间 `O(V)`。

## 3 分钟版

深拷贝图的难点是图不是树。树里一个节点通常只有一条从根到它的父路径；图里同一个节点可能被多个节点引用，而且可能存在环。如果递归时每看到一次邻居就 `new Node`，共享邻居会被复制成多个对象；遇到环还会无限递归。

所以核心不变量是：**每个可达原节点恰好对应一个克隆节点**。映射建立后，复制边只需要把原边 `u -> v` 转换成 `clone(u) -> clone(v)`。因为本候选用邻接列表达无向图，一条无向边通常会以两个邻接项出现，算法不需要特殊处理“无向”——它只忠实复制每个原节点的邻接表；如果原表示里有自环或重复邻接项，也会按原顺序保留。

BFS 和 DFS 都可以。这里选 BFS，避免代码依赖递归深度，并且队列状态容易验证。`IdentityHashMap` 是一个额外的实现选择：候选节点没有覆写 `equals/hashCode`，普通 `HashMap` 也能工作；显式使用身份映射可以强调映射键是“原节点对象身份”，而不是节点值。节点值可以重复，不能拿 `value` 当唯一键。

深拷贝还要验证“不共享对象”。仅仅比较输出值和边数不够；测试应建立原节点到克隆节点的双向一一映射，逐个比较值、邻接长度和每个邻接位置的映射目标，并确认任何克隆节点都不属于原图节点集合。

## 关键细节

- **题源边界**：来源只支持“无向图的深拷贝”；Java、`int value`、起点式 API、邻接表顺序、`null` 行为都是显式候选选择。
- **映射键必须是节点身份**：节点值可重复，不能用 `value` 做 key；否则不同节点会错误合并。
- **先建克隆再扩展邻居**：发现新节点时立即放进映射，再入队，环回到它时就能复用而不是再次创建。
- **自环**：`u.neighbors` 包含 `u` 时，克隆邻接应指回 `clone(u)`。
- **共享邻居/环**：多个原节点引用同一个邻居时，它们必须引用同一个克隆邻居。
- **重复邻接项**：本候选按列表逐项复制，因此平行/重复邻接项不会被集合去重。
- **复杂度**：每个可达节点出队一次，每个邻接项处理一次，时间 `O(V + E_adj)`；映射和队列为 `O(V)`，输出图本身不计入辅助空间。
- **可验证性**：固定用例覆盖空输入、孤立点、两点无向边、三点环、自环、重复值和重复邻接；再用 3000 个确定性随机无向图验证双向一一映射、零共享节点和原图不变。

## 原理机制

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

public final class GraphClone {
    public static final class Node {
        public final int value;
        public final List<Node> neighbors = new ArrayList<>();

        public Node(int value) {
            this.value = value;
        }
    }

    private GraphClone() {}

    public static Node cloneGraph(Node start) {
        if (start == null) {
            return null;
        }

        Map<Node, Node> clones = new IdentityHashMap<>();
        Deque<Node> queue = new ArrayDeque<>();
        clones.put(start, new Node(start.value));
        queue.addLast(start);

        while (!queue.isEmpty()) {
            Node original = queue.removeFirst();
            Node copy = clones.get(original);
            for (Node neighbor : original.neighbors) {
                Node neighborCopy = clones.get(neighbor);
                if (neighborCopy == null) {
                    neighborCopy = new Node(neighbor.value);
                    clones.put(neighbor, neighborCopy);
                    queue.addLast(neighbor);
                }
                copy.neighbors.add(neighborCopy);
            }
        }
        return clones.get(start);
    }
}
```

固定用例和 3000 个随机图的预检输出为：

```text
PASS fixed=7 randomized=3000 oracle=paired-bijection sharedNodes=0 mutation=none
```

## 项目经验版

这是基础算法题，仓库来源没有生产项目上下文，因此不编造项目经历。工程对象图的“深拷贝”往往还要定义不可变对象是否共享、外部资源句柄怎么处理、对象类型与继承关系如何保留；这些都不是本题来源事实。本候选只处理明确声明的图节点与邻接列表契约。

## 常见追问

- 问：为什么不能递归地直接 `new` 每个邻居？答：因为环会无限递归，共享邻居也会被复制成多个不同对象；必须先用映射固定一一对应关系。
- 问：为什么不能用节点值作为 Map 的 key？答：值可以重复，两个不同原节点可能同值；图克隆要保持节点身份关系而不是按值合并。
- 问：BFS 和 DFS 有本质区别吗？答：对正确克隆没有，本质都是“访问集合/映射 + 逐边重建”；BFS 用队列，DFS 用递归或栈。
- 问：怎么证明是深拷贝而不是浅拷贝？答：除了结构和值一致，还要确认所有克隆节点都是新对象，且同一个原节点始终映射到同一个克隆节点；测试做了双向身份映射检查。
- 问：如果图不连通怎么办？答：当前 API 只有一个起点，因此只克隆该起点可达的连通分量；若要求复制整个离散图，需要把输入契约改成所有顶点集合并对每个未访问分量启动一次遍历。

## 易错点

- 看到邻居后先递归/入队，之后才写映射，导致环中重复创建。
- 用 `value` 当节点唯一标识，遇到重复值时错误合并节点。
- 只复制节点值，没有重建邻接关系。
- 克隆节点的 `neighbors` 仍引用原节点，形成浅拷贝。
- 用 `Set` 重建邻接表，意外丢失原表示中的顺序或重复邻接项。
- 把“连通图、固定 Node 签名、Java、无重复边”等未出现在来源中的条件说成原题事实。
