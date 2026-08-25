<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_6a03e4ded0b05d96bb54b43ae3e980be","version":1,"status":"draft","updated_at":"2026-08-25","answer_type":"coding","quality_tier":"candidate"} -->
# 避免洪水泛滥（LeetCode 1488）

## 核心结论

这题的关键不是“看到晴天就随便抽干一个湖”，而是当某个湖再次下雨时，必须把它上一次下雨之后、这一次下雨之前的某个晴天分配给它。用 `lastRain` 记录每个湖上一次下雨日，用有序集合 `dryDays` 保存尚未分配的晴天；再次遇到同一个湖时，取 `dryDays.higher(lastRain[lake])`，也就是上次下雨之后最早可用的晴天。如果不存在这样的晴天，当前湖必然在再次下雨前仍是满的，直接返回空数组。

## 1 分钟版

- 官方题意里，`rains[i] > 0` 表示第 i 天给对应湖下雨，`rains[i] == 0` 表示当天必须选择一个湖抽干；雨天答案固定为 `-1`，无法避免洪水时返回空数组。
- `lastRain[lake]` 表示这个湖上次被灌满的日期；如果湖第一次下雨，只记录日期即可。
- 每个晴天先加入 `TreeSet<Integer> dryDays`，表示“过去已经发生、但还没分配给任何湖”的抽干机会。
- 湖再次下雨时，必须从 `dryDays` 里找严格晚于上次下雨日的最早晴天；用 `higher(prev)` 得到它，给该晴天安排抽干这个湖并从集合移除。
- 扫描完后仍未使用的晴天可以任意抽干一个湖，例如填 `1`。整体时间 O(n log n)，空间 O(n)。

## 3 分钟版

```java
import java.util.HashMap;
import java.util.Map;
import java.util.TreeSet;

final class AvoidFlood {
    static int[] avoidFlood(int[] rains) {
        if (rains == null) throw new IllegalArgumentException("rains must not be null");
        int n = rains.length;
        int[] ans = new int[n];
        Map<Integer, Integer> lastRain = new HashMap<>();
        TreeSet<Integer> dryDays = new TreeSet<>();

        for (int i = 0; i < n; i++) {
            int lake = rains[i];
            if (lake < 0) throw new IllegalArgumentException("rains[i] must be >= 0");
            if (lake == 0) {
                ans[i] = 1;
                dryDays.add(i);
                continue;
            }

            ans[i] = -1;
            Integer prev = lastRain.put(lake, i);
            if (prev == null) continue;

            Integer dry = dryDays.higher(prev);
            if (dry == null) return new int[0];
            ans[dry] = lake;
            dryDays.remove(dry);
        }
        return ans;
    }
}
```

为什么贪心地选“上次下雨之后最早的可用晴天”是安全的？对当前再次下雨的湖，这个晴天只要落在 `(prev, i)` 内就能消除当前洪水风险；选择最早的可用日，会把更晚的晴天留给那些上一次下雨更晚、可选窗口更窄的未来需求。反过来，如果连最早满足 `> prev` 的可用晴天都不存在，那么过去没有任何尚未使用的晴天能落在合法窗口内，当前洪水已经不可避免。

## 关键细节

- **晴天为什么用日期而不是湖号存集合**：待决定的是“哪一天拿来抽干哪个湖”；湖号只有在第二次下雨暴露出具体需求时才确定。
- **为什么要严格 `higher(prev)`**：上一次下雨当天不能同时抽干；合法抽干日必须在两次下雨之间。
- **为什么不用未来晴天**：在线扫描到第 i 天时，只有 `< i` 的晴天已经发生；`dryDays` 天然只包含过去日期，所以找到的日子自动小于当前再次下雨日。
- **为什么未使用晴天填 1**：官方允许晴天抽干空湖，什么也不会发生；因此不承担关键任务的晴天可以填任意正湖号。
- **输入边界**：官方约束给出非负 `rains[i]`；实现额外对 `null` 和负值 fail closed，属于防御性契约，不是题目新增要求。
- **复杂度**：每个晴天至多加入和删除 `TreeSet` 一次，每次 O(log n)；哈希表平均 O(1)，总时间 O(n log n)，额外空间 O(n)。

## 原理机制

每个湖的两次相邻降雨 `(prev, current)` 形成一个必须满足的“抽干窗口”：至少选择一个尚未被其他湖占用的晴天 `d`，满足 `prev < d < current`。晴天是一种一次性资源，一个日期只能服务一个湖。

扫描到 `current` 时，这个窗口的右端点已经到期。如果此时还没有分配抽干日，就必须立刻从过去的空闲晴天中补一个。选择 `higher(prev)` 给当前湖使用相当于 earliest feasible day：既满足当前截止条件，又尽量保留更晚的资源。`lastRain` 负责生成窗口左端点，`TreeSet` 负责对可用日期做后继查询和删除。

## 项目经验版

题源是算法题，没有真实项目、生产流量或个人经历，不能虚构。工程上可以把它理解为“带时间窗口的一次性资源分配”：先明确资源能否复用、窗口是否开闭区间、失败时是否允许回滚，再选择有序集合或其他调度结构；这些是迁移思路，不是本题来源事实。

## 常见追问

- 问：为什么不能每个晴天就抽干当前任意一个已满湖？答：你不知道哪个湖会最先再次下雨；过早随意消耗晴天可能把唯一可行窗口浪费掉。等到某湖再次下雨时再反向分配过去的空闲晴天，可以精确满足已到期需求。
- 问：为什么 `higher(prev)` 取最早可用晴天？答：当前湖只要求日期晚于 prev；取最早可用值能把更晚、更灵活的日期留给窗口起点更晚的需求。
- 问：如果 `higher(prev)` 返回 `null` 为什么一定无解？答：集合里已经包含当前日前所有尚未使用的晴天；没有任何一个晚于 prev，就不存在能夹在两次降雨之间的可用晴天。
- 问：晴天抽干一个本来就是空的湖可以吗？答：官方题意允许，效果是什么也不发生，所以未被关键约束使用的晴天可填任意正湖号。
- 问：能不能用排序数组代替 `TreeSet`？答：需要同时支持动态插入、找后继、删除已使用日期；普通数组删除代价高。可以用其他有序集合、Fenwick/并查集式“下一个未使用位置”等结构，但实现与复杂度权衡不同。

## 易错点

- 再次下雨时只检查“有没有晴天”，却没检查晴天是否晚于这个湖上一次下雨。
- 找到晴天后不从集合删除，导致同一天被多个湖重复使用。
- 把当前或未来的晴天当作已经可用，破坏时间因果顺序。
- 用 `ceiling(prev)` 而不是严格 `higher(prev)`，错误允许上次下雨当天同时抽干。
- 无解时仍返回一个部分填好的数组，而不是按题意返回空数组。
