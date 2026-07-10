<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_cc39dcdb","version":2,"status":"ready","updated_at":"2026-07-10","quality_tier":"curated"} -->
# 算法：字符串大数加法

## 核心结论

字符串数字相加就是模拟竖式加法：从两个字符串末尾开始逐位相加，维护进位，把每位结果追加到缓冲区，最后反转得到答案。

## 1 分钟版

设两个指针 i、j 分别指向 num1 和 num2 末尾，carry 表示进位。循环条件是 i 或 j 未结束，或者 carry 不为 0。每轮取当前数字字符转成整数，sum = a + b + carry，当前位是 sum % 10，新进位是 sum / 10。结果从低位到高位生成，所以最后需要反转。

## 3 分钟版

这题通常要求不能直接转整数，因为字符串可能很长，超过 long 或 BigInteger 也可能被限制。实现时要处理长度不同的两个字符串，缺失位当作 0。字符转数字可以用 `ch - '0'`，但要确认输入都是非负数字字符串。如果题目扩展到负数、小数或前导零，需要额外处理符号、小数点和输出规范；基础版本只考虑非负整数。

```java
class Solution {
    public String addStrings(String num1, String num2) {
        int i = num1.length() - 1, j = num2.length() - 1, carry = 0;
        StringBuilder reversed = new StringBuilder(Math.max(num1.length(), num2.length()) + 1);
        while (i >= 0 || j >= 0 || carry != 0) {
            int a = i >= 0 ? num1.charAt(i--) - '0' : 0;
            int b = j >= 0 ? num2.charAt(j--) - '0' : 0;
            int sum = a + b + carry;
            reversed.append((char) ('0' + sum % 10));
            carry = sum / 10;
        }
        return reversed.reverse().toString();
    }
}
```

## 关键细节

- 从低位往高位加。
- carry 初始为 0，最后可能还要追加。
- 两个字符串长度可以不同。
- 结果生成后需要反转。
- 基础题输入是非空非负十进制字符串；生产函数还要校验非法字符并统一前导零。
- 设最大长度为 n，时间 O(n)，输出缓冲区空间 O(n)。

## 原理机制

- 十进制竖式加法每一位只依赖当前位和进位。
- 从右到左遍历可以自然拿到最低位。
- 使用字符串缓冲区避免频繁创建中间字符串。

## 项目经验版

算法训练映射：使用统一循环条件，随后以 `999+1`、`0+0`、`123+7890` 和大量前导零验证进位、零值与长度差。不要把算法练习虚构成财务系统大数项目。

## 常见追问

- 问：为什么不能转 int/long？答：输入长度可能超过固定位宽，且题目通常要求手动实现；BigInteger 也可能被禁止。
- 问：最后进位怎么处理？答：把 `carry != 0` 放入循环条件，最高位进位会自然追加。
- 问：负数怎么扩展？答：先解析符号，异号时比较绝对值并执行高精度减法，最后规范化符号和前导零。
- 问：还有什么变体？答：字符串乘法用逐位乘积累加到长度 `m+n` 的数组，再统一处理进位；任意进制只需替换基数和字符映射。

## 易错点

- 不要忘记最后的 carry。
- 不要把字符 ASCII 值直接相加。
- 不要遗漏结果反转。
