<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_cb9856867b3fb40eec91f9d6408beaaf","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# 递归判断字符串是否为回文串

## 核心结论

递归判断回文的核心不变量是：只要当前区间两端字符相等，问题就缩小为判断内部区间是否回文；当左右指针相遇或交错时，说明所有成对字符都匹配，返回 `true`。仓库原始笔记只保留“递归判断回文串”，没有保留忽略大小写、跳过标点或空白等规则；虽然结构化标签里出现了 `LeetCode 125`，但原始笔记没有这个编号，因此不能把 LeetCode 125 的归一化规则冒充成原题要求。下面给一个明确的 Java 参考契约：按 `String.charAt` 的 UTF-16 code unit 精确、区分大小写比较；空串和单字符为回文；`null` 作为非法输入抛异常。

## 1 分钟版

- 定义递归函数 `check(s, left, right)`，表示闭区间 `[left, right]` 是否回文。
- 终止条件是 `left >= right`，此时剩余 0 或 1 个字符，必然回文。
- 若 `s.charAt(left) != s.charAt(right)`，立即返回 `false`。
- 两端相等时递归判断 `check(s, left + 1, right - 1)`。
- 每对字符最多比较一次，时间复杂度 O(n)；递归深度最多约 n/2，所以额外栈空间 O(n)。
- 如果面试官补充“忽略大小写/标点/空格”或要求完整 Unicode code point 语义，应先修改输入归一化与字符遍历契约，再复用同一个递归不变量。

## 3 分钟版

```java
public final class RecursivePalindrome {
    public static boolean isPalindrome(String s) {
        if (s == null) {
            throw new IllegalArgumentException("input must not be null");
        }
        return check(s, 0, s.length() - 1);
    }

    private static boolean check(String s, int left, int right) {
        if (left >= right) {
            return true;
        }
        if (s.charAt(left) != s.charAt(right)) {
            return false;
        }
        return check(s, left + 1, right - 1);
    }
}
```

例如 `abcba`：先比较 `a/a`，递归到 `bcb`；再比较 `b/b`，递归到单字符 `c`；此时 `left >= right` 返回 `true`，逐层返回。若是 `abca`，第一层 `a/a` 相等，但下一层比较 `b/c` 立即返回 `false`。

## 关键细节

- **先定义比较规则**：原始来源没有说忽略大小写、空格或标点，所以参考实现采用精确比较，不偷偷引入额外规则。
- **终止条件**：奇数长度最终落到一个字符，偶数长度最终左右交错；两种情况都由 `left >= right` 统一覆盖。
- **递归收缩必须单调**：每层 `left + 1`、`right - 1`，保证有限步内到达终止条件。
- **短路失败**：任意一对不相等即可直接判 `false`，后续内部字符无需继续检查。
- **空串**：按数学上“反转后仍相同”的常见定义，本参考契约把空串视为回文；这是实现选择，不是来源明确要求。
- **`null`**：不是字符串值，本参考实现选择 fail-fast 抛 `IllegalArgumentException`，避免把 `null` 默认为空串。
- **Unicode 边界**：Java `charAt` 比较的是 UTF-16 code unit。若题目要求按 Unicode code point 或用户感知字符判断，应改用相应遍历策略，不能宣称这个最小实现覆盖所有 Unicode 语义。
- **栈深度**：时间仍是 O(n)，但很长字符串可能因递归深度触发栈溢出；工程代码可改为双指针迭代版本。题目明确要求递归时，应说明这一代价。

## 原理机制

设命题 `P(l, r)` 表示 `s[l..r]` 是回文。递归关系是：当 `l >= r` 时 `P(l, r)=true`；否则 `P(l, r) = (s[l] == s[r]) && P(l+1, r-1)`。这直接对应回文定义：一个长度至少为 2 的字符串是回文，当且仅当首尾相同且去掉首尾后的子串仍是回文。

因为每次递归都把区间长度减少 2，所以最多进行约 `n/2` 层递归；每层只做常数次比较，时间 O(n)。递归调用栈保存每层的 `left/right` 与返回位置，空间 O(n)。若改成迭代双指针，时间不变但额外空间可降为 O(1)。

## 项目经验版

来源没有真实项目背景，不能虚构线上使用经历。实际业务中如果“回文”用于用户名、文本、国际化内容或清洗后的字段，我会先明确 normalization、大小写、标点、Unicode grapheme/code point 等规则，再决定是先归一化后比较，还是在双端扫描时跳过不参与比较的字符。规则必须有样例和测试证明，不能从一个算法题标题反推业务语义。

## 常见追问

- 问：为什么终止条件是 `left >= right`？答：剩余 0 或 1 个字符时不存在不匹配的字符对，因此当前区间是回文。
- 问：递归和双指针迭代有什么区别？答：判断逻辑相同，递归更直接表达定义，但需要 O(n) 调用栈；迭代可把额外空间降到 O(1)。
- 问：`"A man, a plan, a canal: Panama"` 怎么办？答：那需要先确认是否采用类似“忽略非字母数字并忽略大小写”的契约。原始笔记没有保留该要求，本候选不会默认套入这套规则。
- 问：为什么不直接 `new StringBuilder(s).reverse()`？答：那可以判断某个明确字符串契约，但题目明确要求递归，面试考点是递归状态、终止条件和区间收缩；同时 reverse 方案会额外构造字符串。
- 问：复杂度是多少？答：最多比较约 n/2 对字符，时间 O(n)；递归深度 O(n)，因此栈空间 O(n)。

## 易错点

- 忘记 `left >= right` 的终止条件，导致越界或无限递归。
- 两端相等后没有同时收缩左右边界。
- 看到结构化标签中的 `LeetCode 125` 就擅自加入忽略标点/大小写规则，而没有回到原始笔记核对。
- 把 `null` 与空串混为一谈，却没有说明异常契约。
- 在 Java 中把 `charAt` 的 UTF-16 code unit 比较误称为完整 Unicode 字符语义。
- 只说时间 O(n)，忽略递归调用栈的 O(n) 空间和极长输入的栈深限制。
