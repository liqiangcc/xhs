<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_cc39dcdb","version":1,"status":"draft","updated_at":"2026-07-11","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：字符串大数加法

## 核心结论

字符串大数加法从两个字符串末尾同时向前扫描，把当前两位和 carry 相加，追加 sum%10，并把 sum/10 带到更高位；最后反转结果并去掉多余前导零。每个字符在校验和加法阶段至多访问常数次，时间 O(m+n)、额外空间 O(m+n)，不依赖数值类型容量。

## 1 分钟版

- 输入是非空、仅含 ASCII 十进制数字的两个非负整数字符串；输出是它们的规范十进制和，零固定输出为 "0"。
- 状态是两个下标 i、j 和进位 carry；每轮已写出的逆序后缀恰是两个已处理低位及其进位的正确和。
- 任一字符串先耗尽时按 0 参与；循环条件还要包含 carry，避免例如 "9"+"1" 漏掉最高位。
- 实现逐字符校验输入而不是悄悄接受负号、小数点或空串；原字符串不修改。

## 3 分钟版

从最低位开始是因为进位只流向更高位。每轮取 digitA、digitB 和 carry，sum=digitA+digitB+carry，当前位为 sum%10，新 carry 为 sum/10；这与竖式加法同构。循环结束时所有位和最后进位都已写入逆序 StringBuilder，反转后得到结果。若输入带前导零，运算仍正确，但输出用 trimLeadingZeros 统一为规范表示。

```java
public final class StringAddition {
    private StringAddition() {}

    public static String add(String first, String second) {
        validate(first);
        validate(second);
        int i = first.length() - 1, j = second.length() - 1, carry = 0;
        StringBuilder reversed = new StringBuilder(Math.max(first.length(), second.length()) + 1);
        while (i >= 0 || j >= 0 || carry != 0) {
            int left = i >= 0 ? first.charAt(i--) - '0' : 0;
            int right = j >= 0 ? second.charAt(j--) - '0' : 0;
            int sum = left + right + carry;
            reversed.append((char) ('0' + sum % 10));
            carry = sum / 10;
        }
        return trimLeadingZeros(reversed.reverse().toString());
    }

    private static void validate(String value) {
        if (value == null || value.isEmpty()) throw new IllegalArgumentException("non-empty decimal string required");
        for (int i = 0; i < value.length(); i++) {
            if (value.charAt(i) < '0' || value.charAt(i) > '9') {
                throw new IllegalArgumentException("decimal digits only");
            }
        }
    }

    private static String trimLeadingZeros(String value) {
        int firstNonZero = 0;
        while (firstNonZero < value.length() - 1 && value.charAt(firstNonZero) == '0') firstNonZero++;
        return value.substring(firstNonZero);
    }
}
```

## 关键细节

- 输入是非空、仅含 ASCII 十进制数字的两个非负整数字符串；输出是它们的规范十进制和，零固定输出为 "0"。
- 状态是两个下标 i、j 和进位 carry；每轮已写出的逆序后缀恰是两个已处理低位及其进位的正确和。
- 任一字符串先耗尽时按 0 参与；循环条件还要包含 carry，避免例如 "9"+"1" 漏掉最高位。
- 实现逐字符校验输入而不是悄悄接受负号、小数点或空串；原字符串不修改。
- null、空串或非数字字符抛 IllegalArgumentException；题目若允许符号或小数，应先把符号/小数位拆成独立问题，不能复用本实现。
- 覆盖 0、不同长度、连续进位、最终进位、输入前导零、超出 long 的长串和非法输入。
- 与 BigInteger 独立 oracle 对照所有长度 1 到 3、数字范围 0 到 3 的 7,056 对输入。
- 时间 O(m+n)，结果 StringBuilder 与最终字符串占 O(m+n) 额外空间。
- 复杂度：时间 O(m+n)，额外空间 O(m+n)。

## 原理机制

不变量是：经过 k 轮后，builder 中从左到右保存结果最低 k 位的逆序，carry 等于尚未处理前缀应加到下一位的唯一进位。每轮把该进位完全吸收进一个十进制位并产生下一位进位，因此循环终止时 builder 正是完整和的逆序。
- 复杂度：时间 O(m+n)，额外空间 O(m+n)。

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：为什么从尾部加？答：十进制进位从低位流向高位；从尾部扫描只需保留一个 carry，不必回填前面的结果。
- 问：为什么循环条件要包含 carry？答：例如 "9"+"1" 处理完两个字符后 carry 仍为 1；漏掉它会返回 "0" 而非 "10"。
- 问：输入有前导零怎么办？答：逐位计算仍正确，最后统一裁剪为规范输出；"000"+"000" 返回 "0"。
- 问：如何支持负数？答：先比较绝对值并转换为加法或借位减法，再按较大绝对值确定符号；不能把 '-' 当普通数字相加。

## 易错点

- 不要把整串解析成 int 或 long，会在长输入溢出。
- 不要忘记最后 carry，也不要在任一字符串耗尽后停止。
- 字符转数字应减 '0'，并先校验字符范围。
- 返回前要处理全零结果，否则 "000"+"000" 会得到多余零。
