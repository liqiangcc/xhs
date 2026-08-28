<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d9617ce6ae5f4ede30ddabf9bd41f2c1","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# LeetCode 76 Minimum Window Substring：可变滑动窗口

## 核心结论

来源明确指向 LeetCode 76。当前官方题面是：给字符串 `s` 和 `t`，返回 `s` 中最短的连续子串，使它包含 `t` 中每个字符及其重复次数；不存在则返回空字符串，测试保证答案唯一。官方 follow-up 要求 O(m+n)。标准做法是可变滑动窗口：右指针扩张直到窗口覆盖 `t` 的全部需求，然后左指针尽量收缩；每次窗口仍合法时更新最短答案。

一个很稳的实现是维护 `need[c]` 和一个 `missing` 计数。`need[c] > 0` 表示当前窗口还缺多少个字符 c；加入右字符时，如果加入前 `need[c] > 0`，说明确实补上了一个缺口，`missing--`，随后 `need[c]--`。当 `missing==0` 时窗口合法；移走左字符时先 `need[left]++`，如果变成正数，说明刚删掉的是必需字符，窗口重新非法并 `missing++`。

## 1 分钟版

- 先统计 `t` 的字符需求，`missing = t.length()`，重复字符按重复次数计，不是只看 distinct 字符种类。
- `right` 每右移一步，把字符加入窗口：若它之前仍欠缺，就让 `missing--`；无论是否欠缺都把 `need[c]--`。
- 当 `missing==0`，当前窗口已经覆盖 `t`，开始移动 `left` 压缩；每个合法窗口都可以尝试更新最短答案。
- 左边字符移出时 `need[c]++`；若加回后 `need[c] > 0`，说明窗口刚失去一个必需字符，此时停止收缩，继续扩右。
- 左右指针都只单调前进，每个字符最多被右指针加入一次、左指针移出一次，所以 O(m+n)。
- 当前官方约束字符是大小写英文字母；实现用 `int[128]` 足够。若业务输入扩到任意 Unicode，应改为按 code point 计数的 Map，而不是把 ASCII 数组冒充通用字符串方案。

## 3 分钟版

```java
public final class MinimumWindowSubstring {
    public static String minWindow(String s, String t) {
        if (s == null || t == null) {
            throw new IllegalArgumentException("s and t must not be null");
        }
        if (t.isEmpty() || s.length() < t.length()) {
            return "";
        }

        int[] need = new int[128];
        for (int i = 0; i < t.length(); i++) {
            char c = t.charAt(i);
            if (c >= need.length) {
                throw new IllegalArgumentException("this implementation expects ASCII input");
            }
            need[c]++;
        }

        int missing = t.length();
        int bestStart = 0;
        int bestLen = Integer.MAX_VALUE;
        int left = 0;

        for (int right = 0; right < s.length(); right++) {
            char rc = s.charAt(right);
            if (rc >= need.length) {
                throw new IllegalArgumentException("this implementation expects ASCII input");
            }
            if (need[rc] > 0) {
                missing--;
            }
            need[rc]--;

            while (missing == 0) {
                int len = right - left + 1;
                if (len < bestLen) {
                    bestLen = len;
                    bestStart = left;
                }

                char lc = s.charAt(left++);
                need[lc]++;
                if (need[lc] > 0) {
                    missing++;
                }
            }
        }

        return bestLen == Integer.MAX_VALUE
                ? ""
                : s.substring(bestStart, bestStart + bestLen);
    }
}
```

例如 `s="ADOBECODEBANC", t="ABC"`。窗口先扩到 `ADOBEC` 才第一次覆盖 A/B/C，随后左缩直到再缩会丢 A；右边继续扩，最终在末尾形成 `BANC`，长度 4，是最短答案。

重复字符是这题最重要的边界之一：`s="a", t="aa"` 必须返回 `""`。如果只记录 `t` 中有哪几种字符，而不记录频次，就会错误地认为一个 a 已经满足两个 a 的需求。

## 关键细节

- **窗口合法性**：不是“窗口含有 t 的所有 distinct 字符”，而是每个字符计数都至少达到 t 中要求的频次。
- **`need` 的正负含义**：正数=还欠几个，0=刚好，负数=窗口中有多余的这个字符。
- **`missing`**：按字符总需求计数，初始是 `t.length()`；加入真正缺少的字符才减，移出导致重新欠缺时才加。
- **收缩顺序**：合法时先记录当前窗口，再移出 `left`；否则可能漏掉刚好最短的合法窗口。
- **唯一答案**：当前官方测试保证最短答案唯一，所以不需要设计同长窗口 tie-break；真实业务若不保证唯一，要明确选择最左、最右或全部结果。
- **字符集**：当前官方输入只包含大小写英文字母，ASCII 数组是有依据的优化；若扩大输入域要更换计数结构。
- **空字符串/null**：官方约束 `m,n >= 1`，因此空/null 不是题面测试域；本实现把空 t 返回空、null 抛异常，是工程接口扩展。
- **复杂度**：右指针最多 m 步，左指针最多 m 步，构建 t 频次 n 步，总计 O(m+n)，空间对固定 ASCII 字符集为 O(1)。

## 原理机制

滑动窗口能线性工作的关键是单调性。对固定右端点，窗口一旦覆盖全部需求，可以不断右移左边界寻找最短合法窗口；当删掉一个必需字符后，继续右移左边界只会更缺，不可能重新合法，所以应停止收缩，转而继续扩张右边界。这让左右指针都不回退。

`need` 数组同时承担“还欠多少”和“多余多少”的差分计数。加入字符时从需求中减 1，移出字符时加 1；`missing` 只追踪所有正需求的总缺口，因此合法性检查是 O(1)，不需要每一步扫描整个频次数组。若每次都遍历 52 个字符检查是否覆盖，在当前固定字符集仍是常数，但这个差分模型更容易泛化到大字符集的 Map。

## 项目经验版

来源没有真实项目经历，不能虚构。工程里类似问题常见于日志片段、事件流或字符序列的最小覆盖查询。落地时首先要确认“包含”是计数覆盖、集合覆盖还是有序子序列；这三种合同对应的算法不同。还要确认字符编码：Java `char` 是 UTF-16 code unit，若真实业务要求 Unicode code point 语义，不能直接把 `char` 当完整字符。

## 常见追问

- 问：为什么 `missing` 用 `t.length()` 而不是 distinct 字符数？答：因为题面明确要求包含重复字符。例如 t="AABC" 需要两个 A；总缺口能直接表达每一个必需字符实例。
- 问：`need[c]` 为什么可以变负？答：负数表示当前窗口里这个字符比 t 需要的更多；多余字符不影响窗口合法，只在左缩时提供缓冲。
- 问：为什么总体不是 O(m²)，while 也在 for 里面？答：left 只从 0 单调移动到 m，每个位置最多被移出一次；把所有 while 次数累加仍不超过 m。
- 问：如果答案不唯一怎么办？答：当前 LeetCode 测试保证唯一；若业务不保证，要额外定义 tie-break，例如同长取最左，并据此决定 `len < bestLen` 还是其他比较。
- 问：为什么不能固定窗口长度？答：答案长度未知，且覆盖 t 的最短长度会随 s 中字符分布变化；必须先扩到合法再收缩，是可变窗口。
- 问：和 Minimum Window Subsequence 有什么区别？答：本题只要求窗口包含字符多重集合，不要求 t 的字符在窗口中按 t 顺序出现；subsequence 版本有顺序约束，是另一道问题。

## 易错点

- 只统计 distinct 字符，不统计 t 中重复次数。
- 每次窗口合法后只更新一次却不继续收缩，错过更短答案。
- 移出左字符时先判断再恢复 `need`，把“刚刚重新欠缺”的时机写反。
- 把 `char[128]` 方案描述成任意 Unicode 通用实现。
- 看到“力扣76”却误答成 Minimum Window Subsequence，而不是 Minimum Window Substring。
- 用嵌套循环表象错误地宣称 O(m²)，忽略 left/right 都只单调前进。
