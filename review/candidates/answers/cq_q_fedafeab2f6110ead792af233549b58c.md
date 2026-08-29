<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_fedafeab2f6110ead792af233549b58c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 最长回文子串

## 核心结论

来源只要求最长回文子串，没有指定语言、空值和并列答案规则。这里采用 Java 合同：返回输入字符串中最长的连续回文子串；空串返回空串，`null` 视为无效输入；若有多个同长度最优解，返回起始位置最靠前的一个。使用中心扩展，对每个位置分别尝试奇数中心和偶数中心，时间 O(n²)、额外空间 O(1)。

## 1 分钟版

- “子串”必须连续，因此不能用最长回文子序列的区间 DP 语义混淆。
- 每个回文串都有一个中心：奇数长度中心是字符，偶数长度中心是两个字符之间的缝。
- 从中心向两侧同时扩展，只要字符相等就继续；第一次不等时，该中心的最大回文已经确定。
- 每个位置算奇偶两个中心，维护全局最优 `[start,end]`。
- 只在发现更长答案时更新，因此并列时自然保留更早出现的答案。

## 3 分钟版

```java
public final class LongestPalindromicSubstring {
    public static String longestPalindrome(String s) {
        if (s == null) throw new IllegalArgumentException("s must not be null");
        if (s.length() < 2) return s;
        int start = 0, end = 0;
        for (int i = 0; i < s.length(); i++) {
            int odd = expand(s, i, i);
            int even = expand(s, i, i + 1);
            int len = Math.max(odd, even);
            if (len > end - start + 1) {
                start = i - (len - 1) / 2;
                end = i + len / 2;
            }
        }
        return s.substring(start, end + 1);
    }

    private static int expand(String s, int left, int right) {
        while (left >= 0 && right < s.length() && s.charAt(left) == s.charAt(right)) {
            left--;
            right++;
        }
        return right - left - 1;
    }
}
```

这段代码对应上面的口头推导；面试时应先说明输入合同和不变量，再边写边用一个最小样例验证边界，而不是只贴实现。

## 关键细节

- 奇数中心 `(i,i)` 与偶数中心 `(i,i+1)` 都必须检查，否则会漏掉 `abba` 这类偶数回文。
- `expand` 退出时左右指针已经越过合法回文一格，所以长度是 `right-left-1`。
- 当前实现只在 `len` 严格更大时更新，因此同长度并列保留更早的已有答案；这是本答案显式声明的合同。
- 中心扩展最坏 O(n²)，例如大量相同字符会从许多中心扩展很远；如果要求线性时间可讨论 Manacher，但来源没有要求。
- Java `char` 按 UTF-16 code unit 比较；若题目要求按 Unicode code point 定义字符，需要先改变输入遍历合同。

## 原理机制

回文的对称性意味着一旦中心确定，某个半径是否成立只取决于中心两侧对应字符是否相等。任意连续回文子串都能唯一归入一个奇数或偶数中心，因此枚举全部 2n-1 个中心不会漏解。每个中心扩展到第一次不匹配时，其最大半径已经确定；取所有中心的最大值就是全局最长回文子串。

## 项目经验版

来源没有真实字符串长度、字符集或延迟目标，不能虚构必须使用 Manacher。面试现场我会先用中心扩展写出低风险正确解，声明 O(n²)/O(1)，再根据约束决定是否值得升级到 O(n) 的 Manacher，并额外确认并列答案和 Unicode 字符定义。

## 常见追问

- 问：和最长回文子序列区别？答：子串要求连续，子序列可以跳过字符，两题不能直接互换算法。
- 问：为什么需要偶数中心？答：偶数长度回文没有单个中心字符，中心位于两个字符之间。
- 问：为什么复杂度 O(n²)？答：有 O(n) 个中心，每个中心最坏可扩展 O(n) 距离。
- 问：能做到 O(n) 吗？答：可以用 Manacher，但实现复杂度更高，只有约束需要时才值得使用。
- 问：多个最长答案返回哪个？答：当前合同返回最早起始位置的那个，因为只在严格更长时更新。

## 易错点

- 只扩展奇数中心，漏掉偶数长度回文。
- 把“子串”写成“子序列”问题。
- 退出扩展后长度公式写成 `right-left+1`，造成越界长度。
- 未声明并列答案策略却让测试依赖某个固定返回值。
