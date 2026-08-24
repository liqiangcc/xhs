<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_topic_cc39dcdb","version":2,"status":"draft","updated_at":"2026-08-25","quality_tier":"candidate","answer_type":"coding"} -->
# 算法：字符串大数加法

## 核心结论

字符串大数加法就是模拟十进制竖式：从两个字符串末尾同时向前，逐位计算 `digitA + digitB + carry`，写当前位并把进位带到更高位。结合当前已归一化到该 Canonical 的来源变体，本候选明确把空字符串视为 0，因此 `"321" + "" = "321"`，两边都空返回规范零 `"0"`；`null` 和非数字字符仍视为非法输入。

## 1 分钟版

- 输入是两个“空串或仅含 ASCII 十进制数字”的非负整数字符串；空串语义为 0，输出去掉多余前导零，零统一为 `"0"`。
- 两个下标从末位向前，当前缺失位按 0 参与；状态只需要 `i/j/carry`。
- 每轮 `sum = a + b + carry`，结果位是 `sum % 10`，新进位是 `sum / 10`。
- 循环条件要包含 `carry`，否则 `"9" + "1"` 会漏掉最高位。
- 不把整串转成 `long`；字符串长度只影响线性扫描和结果空间。

## 3 分钟版

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
        if (reversed.length() == 0) return "0";
        reversed.reverse();
        int p = 0;
        while (p < reversed.length() - 1 && reversed.charAt(p) == '0') p++;
        return reversed.substring(p);
    }

    private static void validate(String value) {
        if (value == null) throw new IllegalArgumentException("non-null decimal string required");
        for (int i = 0; i < value.length(); i++) {
            char ch = value.charAt(i);
            if (ch < '0' || ch > '9') throw new IllegalArgumentException("decimal digits only");
        }
    }
}
```

`"321" + ""` 时第二个下标一开始就是 -1，因此每一轮右侧数字自然按 0 处理，结果为 321；两边都空时循环一次都不进入，最后显式返回 `"0"`。

## 关键细节

- 空串视为 0 是当前来源变体要求后形成的 Canonical 契约；它不同于很多题库里“输入必为非空数字串”的版本，不能再用旧候选的空串报错规则。
- `null` 不等于空串，本实现仍拒绝 `null`，避免把缺失对象引用默默解释成业务数值 0。
- 前导零允许输入，输出统一裁剪；`"000" + "00"` 返回 `"0"`。
- 任一侧先耗尽时缺失位按 0；最后 carry 仍要单独进入循环。
- 校验和加法会使字符被访问常数次，总时间仍 O(m+n)，结果缓冲区 O(m+n)。
- 本实现处理非负整数；负号、小数和其他进制需要重新定义符号、对齐和借位/进位规则。

## 原理机制

不变量是：完成 k 轮后，`reversed` 已按逆序保存最终和的最低 k 位，`carry` 是未处理高位唯一需要继承的十进制进位。因为低位进位只影响紧邻高位，从末尾向前时无需回改已经确定的低位。空串只是“没有任何显式数字位”的 0，在这一状态机里等价于下标从 -1 开始。

## 项目经验版

这是算法题，不应包装成虚构项目经历。真实接口若允许空串，还要在 API 文档和测试里把“空串 = 0”写成正式契约，避免调用方把数据缺失和数字零混为一谈；如果业务不希望这种宽松语义，就应在边界层拒绝空串。

## 常见追问

- 问：为什么不能直接 `Long.parseLong`？答：字符串可能超过固定整数类型范围，而逐位法只受可用内存限制。
- 问：为什么这版允许空串？答：当前 Canonical 已吸收一个明确的来源变体 `"321" + "" = "321"`，因此空串必须按 0 处理；这是来源边界，不是随意宽松输入。
- 问：`"" + ""` 为什么返回 `"0"`？答：在“空串表示 0”的契约下两个操作数都是 0，输出又要求规范十进制表示，所以选 `"0"` 而不是空串。
- 问：如何支持负数？答：先拆符号，异号时转成绝对值比较与大数减法；不能把 `'-'` 当普通数字参与本循环。
- 问：为什么最后要裁剪前导零？答：输入允许前导零，但输出希望唯一规范表示；否则同一个数会有多个字符串表示。

## 易错点

- 沿用旧版“空串非法”假设，漏掉新归一化来源的明确示例。
- 两个输入都空时返回空结果而不是规范零。
- 忘记最终 carry，`"9"+"1"` 变成 `"0"`。
- 把整串转成 `int/long` 导致大数溢出。
- 未校验字符却直接 `ch-'0'`，把负号或其他字符算成伪数字。
