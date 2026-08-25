<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_6ae96feaa0e3c49daad3242f62e1cc8e","version":1,"status":"draft","updated_at":"2026-08-25","answer_type":"coding","quality_tier":"candidate"} -->
# 买卖股票的最佳时机系列：统一状态机 DP

## 核心结论

当前来源只保留“买卖股票的最佳时机系列，用动态规划解决：基础买卖、无限次交易、N 次交易限制”，没有保存具体函数签名、价格范围、手续费/冷冻期、是否允许同时持有多股，也没有说明“N 次”是恰好还是至多。为了给出可运行实现，我采用一个明确的候选契约：`prices[i]` 是非负整数；任意时刻最多持有 1 股；一次交易是先买后卖；没有手续费和冷冻期；“基础买卖”解释为**至多 1 次完整交易**，“无限次”解释为可重复买卖但同一时刻最多持有 1 股，“N 次限制”解释为**至多 k 次完整交易**。这些是本答案为恢复可执行语义而声明的假设，不冒充来源原文。

三类题本质上是同一个状态机：每天结束时只需要知道“是否持股”，有限交易版本再增加“最多已经使用多少次卖出/完成交易”的维度。单次交易是 `k=1`；无限次交易是去掉交易次数维度；有限 `k` 是完整二维状态的空间压缩版。

## 1 分钟版

- **至多 1 次**：维护 `hold`（买入后持有 1 股的最大收益）和 `cash`（已卖出/不持股的最大收益）。因为不能二次买入，`hold = max(hold, -price)`；`cash = max(cash, oldHold + price)`。
- **无限次**：仍是 `hold/cash` 两状态，但允许在前一天 `cash` 基础上再次买入：`hold = max(oldHold, oldCash - price)`，`cash = max(oldCash, oldHold + price)`。
- **至多 k 次**：令 `buy[t]` 表示“最多完成 `t-1` 次交易后又买入、当前持股”的最好收益，`sell[t]` 表示“最多完成 `t` 次交易、当前空仓”的最好收益。每天从前一天快照转移：`buy[t] = max(oldBuy[t], oldSell[t-1] - price)`，`sell[t] = max(oldSell[t], oldBuy[t] + price)`。
- 当 `k >= n/2` 时，最多可能完成的交易数已经不受 k 约束，可退化成无限次版本。
- 核心不是背三套代码，而是先定义“状态代表什么”，再确认每个转移来自**前一天的合法状态**。

## 3 分钟版

```java
import java.util.Arrays;

public final class StockProfitDp {
    private static final long NEG = Long.MIN_VALUE / 4;

    public static long maxProfitOne(int[] prices) {
        requirePrices(prices);
        long hold = NEG;
        long cash = 0;
        for (int price : prices) {
            long oldHold = hold;
            hold = Math.max(oldHold, -(long) price);
            cash = Math.max(cash, oldHold + price);
        }
        return cash;
    }

    public static long maxProfitUnlimited(int[] prices) {
        requirePrices(prices);
        long hold = NEG;
        long cash = 0;
        for (int price : prices) {
            long oldHold = hold;
            long oldCash = cash;
            hold = Math.max(oldHold, oldCash - price);
            cash = Math.max(oldCash, oldHold + price);
        }
        return cash;
    }

    public static long maxProfitAtMostK(int[] prices, int k) {
        requirePrices(prices);
        if (k < 0) throw new IllegalArgumentException("k must be >= 0");
        if (k == 0 || prices.length < 2) return 0;
        if (k >= prices.length / 2) return maxProfitUnlimited(prices);

        long[] buy = new long[k + 1];
        long[] sell = new long[k + 1];
        Arrays.fill(buy, NEG);

        for (int price : prices) {
            long[] oldBuy = buy.clone();
            long[] oldSell = sell.clone();
            for (int t = 1; t <= k; t++) {
                buy[t] = Math.max(oldBuy[t], oldSell[t - 1] - price);
                sell[t] = Math.max(oldSell[t], oldBuy[t] + price);
            }
        }
        return sell[k];
    }

    private static void requirePrices(int[] prices) {
        if (prices == null) throw new IllegalArgumentException("prices must not be null");
        for (int price : prices) {
            if (price < 0) throw new IllegalArgumentException("price must be non-negative");
        }
    }
}
```

这里故意用“前一天快照”写有限 k 版本，避免在解释时混淆“本轮刚更新的状态”与“前一天状态”。如果只追求常数优化，可以证明更新顺序后原地滚动；面试中先写对、先把状态语义说清楚通常更重要。

## 关键细节

- **交易次数怎么计**：本候选把一次完整交易定义为一次 `buy -> sell`，并在 `sell[t]` 里把第 t 次卖出视为完成第 t 次交易。来源没有保存这个细节，所以必须显式声明。
- **为什么 `k >= n/2` 等价无限次**：在 n 天里每次完整交易至少需要一个买入日和一个不早于买入的卖出日；在不允许同一时刻持多股且同日零收益买卖没有必要的前提下，最多有意义的正收益交易数不超过 `floor(n/2)`。
- **为什么用 long**：来源没给价格上限。本实现用 `long` 保存累计收益，避免把示例实现绑定到未保存的 int 利润上界；输入仍以 `int[]` 表示候选 API。
- **空数组和单元素**：在本候选契约下都没有可完成的正收益交易，返回 0。
- **下降序列**：所有版本都允许“不交易”，所以不会被迫产生负收益。
- **不能同时更新后再误用**：无限次版本先保存 `oldHold/oldCash`；有限 k 版本直接快照数组，转移含义因此清晰对应“从前一天到今天”。
- **复杂度**：单次/无限次都是 O(n) 时间、O(1) 额外空间；至多 k 次是 O(nk) 时间、O(k) 状态空间，当前教学实现每日 clone 也仍是 O(k) 峰值额外空间，但会增加常数分配开销。

## 原理机制

把每天结束时的合法状态看成一个有限状态机。对于无限次版本，只有两类状态：

- `cash`：今天结束后不持股；要么昨天也不持股，要么昨天持股今天卖出。
- `hold`：今天结束后持 1 股；要么昨天已经持股，要么昨天空仓今天买入。

所以每一天都只是在两个合法前态之间做 `max`。有限交易次数只是在状态上再加一个交易预算维度：第 t 次买入只能来自“最多完成 t-1 次交易的空仓状态”，第 t 次卖出只能来自“第 t 层持股状态”。这就是 `oldSell[t-1] -> buy[t] -> sell[t]` 的因果链。

单次交易为什么不同？因为买入后不能在第一次卖出后再次买入，所以 `hold` 的“买入来源”固定是初始现金 0，即 `-price`，而不是任意历史 `cash - price`。这也是为什么把三类题统一成状态语义后，比背模板更不容易写错。

## 项目经验版

来源没有真实项目、交易系统或生产数据，因此不能虚构“线上股票策略经验”。如果这是业务里的状态机计算，我会先冻结完整交易规则（手续费、冷冻期、持仓上限、是否允许做空、成交时点），再为每条规则增加状态维度或转移约束，并用小规模穷举 oracle 与随机/边界输入交叉验证 DP；规则一变，状态定义也必须跟着变。

## 常见追问

- 问：为什么单次交易的 `hold` 不是 `cash - price`？答：因为本候选“基础买卖”只允许至多一次完整交易；如果从已经卖出后的 cash 再买，就隐含允许第二次交易了。
- 问：无限次为什么不是把所有上涨区间直接相加？答：在本候选无手续费、无冷冻期、最多持一股的规则下，两者可得到同一最优值；DP 的价值是状态定义更容易扩展到手续费、冷冻期或交易次数限制。
- 问：k 很大为什么优化成无限次？答：当 k 不小于天数能容纳的最大有效完整交易数时，次数约束不会再排除任何更优策略，继续做 O(nk) 没有必要。
- 问：如果题目说“恰好 k 次”怎么办？答：状态初始化和最终答案都要改变，不能把“至多 k 次”的 0 初值直接照搬；当前来源只说“N 次交易限制”，本候选明确选择“至多 k 次”。
- 问：手续费或冷冻期怎么加？答：手续费可以进入买/卖转移；冷冻期需要增加“刚卖出/冷冻”或读取更早天状态。先改状态机，再改公式，不能只在现有代码上随意加常数。
- 问：如何证明代码不是只过几个例子？答：对小数组枚举所有价格组合和所有合法买/卖/跳过路径，用穷举最优值逐一对比单次、无限次和有限 k DP；当前候选的可执行 fixture 就采用这种交叉验证。

## 易错点

- 没说明“N 次”到底是“至多”还是“恰好”，却直接给初始化为 0 的 DP。
- 在单次交易题里从已卖出的 `cash` 再买，悄悄放宽成多次交易。
- 有限 k 的 `buy[t]` 错从 `sell[t]` 买入，导致交易次数层级定义含糊。
- 滚动数组时没有保存前一日状态，也没有证明原地更新顺序安全。
- 忘记允许“不交易”，使下降序列得到负利润。
- 来源没有手续费、冷冻期或持仓上限细节，却把某一个 LeetCode 变体的规则冒充成原题。
