<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_b46e3f4b0ff3224ae7b5462be34acba2","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# 矩阵左上角到右下角的最小路径：DP 还是 Dijkstra？

## 核心结论

这题首先要确认“允许怎么走”和“格子代价是否可能为负”。如果只能从左上角向右或向下走，那么状态转移天然无环，直接用动态规划：`dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])`，时间 O(mn)，空间可压到 O(n)。如果允许上下左右四个方向，路径图可能有环；当每个格子代价都非负时，把每个格子看成图节点、移动看成边，用 Dijkstra 求最短路更合适。来源只写了“DP/Dijkstra”，没有给移动规则和权值范围，所以答案不能把某一种模型冒充成原题唯一约束。

## 1 分钟版

- **只允许右/下**：这是一个 DAG。`dp[i][j]` 表示到 `(i,j)` 的最小累计代价，来源只可能来自上方或左方。
- 初始化 `dp[0][0]=grid[0][0]`，第一行只能从左边来，第一列只能从上面来。
- 可用一维 `dp[j]`：更新前的 `dp[j]` 是“上方”，更新后的 `dp[j-1]` 是“左方”。
- **允许四方向**：存在回边，普通右/下 DP 不再覆盖全部路径；若代价非负，可用 Dijkstra。
- **存在负代价且允许成环**：标准 Dijkstra 的前提被破坏；还要继续确认是否存在负环以及题目真正的图模型。

## 3 分钟版

先说最常见的右/下模型：矩阵非空，进入一个格子就支付该格子的 `long` 代价，路径包含起点和终点。

```java
import java.util.*;

public final class Solution {
    public static long minPathRightDown(long[][] grid) {
        validate(grid);
        int m = grid.length, n = grid[0].length;
        long[] dp = new long[n];
        dp[0] = grid[0][0];
        for (int j = 1; j < n; j++) dp[j] = Math.addExact(dp[j - 1], grid[0][j]);
        for (int i = 1; i < m; i++) {
            dp[0] = Math.addExact(dp[0], grid[i][0]);
            for (int j = 1; j < n; j++) {
                dp[j] = Math.addExact(Math.min(dp[j], dp[j - 1]), grid[i][j]);
            }
        }
        return dp[n - 1];
    }

    public static long minPathFourDirectionsNonNegative(long[][] grid) {
        validate(grid);
        int m = grid.length, n = grid[0].length;
        for (long[] row : grid) for (long v : row) {
            if (v < 0) throw new IllegalArgumentException("Dijkstra requires non-negative cell costs");
        }
        long[][] dist = new long[m][n];
        for (long[] row : dist) Arrays.fill(row, Long.MAX_VALUE);
        PriorityQueue<State> pq = new PriorityQueue<>(Comparator.comparingLong(s -> s.dist));
        dist[0][0] = grid[0][0];
        pq.add(new State(0, 0, grid[0][0]));
        int[][] dirs = {{1,0},{-1,0},{0,1},{0,-1}};
        while (!pq.isEmpty()) {
            State cur = pq.poll();
            if (cur.dist != dist[cur.r][cur.c]) continue;
            if (cur.r == m - 1 && cur.c == n - 1) return cur.dist;
            for (int[] d : dirs) {
                int nr = cur.r + d[0], nc = cur.c + d[1];
                if (nr < 0 || nr >= m || nc < 0 || nc >= n) continue;
                long nd = Math.addExact(cur.dist, grid[nr][nc]);
                if (nd < dist[nr][nc]) {
                    dist[nr][nc] = nd;
                    pq.add(new State(nr, nc, nd));
                }
            }
        }
        throw new IllegalStateException("target unreachable");
    }

    private static void validate(long[][] grid) {
        if (grid == null || grid.length == 0 || grid[0] == null || grid[0].length == 0) {
            throw new IllegalArgumentException("grid must be non-empty");
        }
        int n = grid[0].length;
        for (long[] row : grid) if (row == null || row.length != n) {
            throw new IllegalArgumentException("grid must be rectangular");
        }
    }

    private record State(int r, int c, long dist) {}
}
```

右/下 DP 的正确性来自最优子结构：到 `(i,j)` 的最后一步只能来自 `(i-1,j)` 或 `(i,j-1)`，所以最优路径一定由这两个前驱中的较优者加当前格子构成。四方向时这个“固定前驱层次”不存在，节点可能从任意已扩展邻居得到更短距离，因此要用图最短路算法维护全局最小未确定距离。

## 关键细节

- **先确认移动集合**：右/下是 DAG；四方向通常是有环图。算法选择由图结构决定，不是题名里出现了哪个关键词决定。
- **起点是否计费**：本参考实现把 `grid[0][0]` 计入总和；若题目定义“走边付费”或不计起点，需要对应调整初始化。
- **Dijkstra 的非负前提**：这里把“进入相邻格子的代价”当作边权，因此格子代价必须非负；负权时不能直接沿用 Dijkstra 的贪心定点性质。
- **空间优化**：右/下 DP 只依赖当前行左侧和上一行同列，所以二维数组可压成 O(n)；若列数更大，也可按较短维压缩。
- **溢出**：示例用 `long` 并用 `Math.addExact` 暴露溢出，而不是静默回绕。平台若保证范围较小，可按题目约束简化。
- **复杂度**：右/下 DP 是 O(mn) 时间、O(n) 额外空间；四方向 Dijkstra 在 `V=mn`、`E≈4mn` 下用二叉堆是 O(mn log(mn)) 时间、O(mn) 空间。

## 原理机制

DP 和 Dijkstra 都在复用“已经求出的最优子结果”，但成立条件不同。右/下移动给出了天然拓扑序：按行从左到右扫描时，所有前驱都已经完成，因此一次状态转移就能永久确定答案。四方向图没有这样的扫描顺序；Dijkstra 利用非负权保证：优先队列里当前距离最小的未确定节点一旦弹出，它不可能再被经过更远节点的路径改小，于是逐步确定最短距离。

## 项目经验版

来源没有真实项目背景，不能虚构线上案例。工程中遇到“网格最短代价”时我会先把规则翻译成图：节点是什么、边是什么、边权如何定义、是否允许回头、有没有障碍和负权，再决定是 DAG DP、BFS、0-1 BFS、Dijkstra 还是其他最短路算法。先建模再选算法，比记住“矩阵题用 DP”更可靠。

## 常见追问

- 问：为什么右/下可以 DP，而四方向不直接用同一个递推？答：右/下没有回边，存在固定拓扑顺序；四方向会形成环，一个格子的最优值可能来自尚未处理的方向。
- 问：如果所有格子代价都是 1 呢？答：四方向时所有移动边权相同，可退化为 BFS，不需要 Dijkstra 的优先队列。
- 问：如果边权只有 0 和 1 呢？答：可用 0-1 BFS，用双端队列把 0 权边放前面、1 权边放后面，时间可做到 O(V+E)。
- 问：为什么 Dijkstra 不能直接处理负权？答：它在弹出当前最小距离节点时就把该距离视为最终值；负权边可能从后续路径把已确定节点再次改小，破坏这个贪心不变量。
- 问：能不能把 DP 写成原地修改矩阵？答：可以，但会破坏输入；是否允许取决于接口契约。面试里最好先说明是否接受修改入参。
- 问：如何恢复具体路径？答：DP 记录每个格子的前驱方向；Dijkstra 在 relax 成功时记录 parent，最后从终点反向回溯。

## 易错点

- 没问移动规则，就直接套右/下 DP。
- 四方向存在环，却用只看“上/左”的递推漏掉合法路径。
- 格子代价允许为负仍直接套 Dijkstra。
- 起点/终点是否计入代价没有声明，样例与实现口径不一致。
- 只说复杂度 O(mn)，却没有区分 DP 和堆优化 Dijkstra 的成本。
