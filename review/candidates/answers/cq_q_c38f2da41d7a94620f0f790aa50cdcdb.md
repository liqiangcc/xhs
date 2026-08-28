<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_c38f2da41d7a94620f0f790aa50cdcdb","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# 字符串大数求和：逐位相加并处理进位

## 核心结论

来源只要求“字符串大数求和”，没有说明负数、小数、前导零或非法字符。这里明确采用一个最小面试契约：输入两个表示**非负十进制整数**的非空字符串，只允许字符 `0-9`；允许前导零，结果规范化为不含多余前导零的十进制字符串（数值 0 返回 `"0"`）。做法是从两个字符串末尾向前逐位相加，加上上一位进位，当前位写 `sum % 10`，新进位是 `sum / 10`。

## 1 分钟版

- 不把字符串转成 `long`/`BigInteger`，因为题目考点就是绕过机器整数位宽限制。
- 两个指针从末尾开始，缺失的一侧按 0 处理；每轮计算 `aDigit + bDigit + carry`。
- 把当前个位追加到 `StringBuilder`，最终反转；循环条件要包含 `carry != 0`，避免漏掉最高位进位。
- 输入先验证为非空且全是十进制数字；前导零不影响逐位算法，返回前统一去除多余前导零。
- 设两个字符串长度为 `m,n`，时间 O(max(m,n))，结果与工作缓冲区额外空间 O(max(m,n))。

## 3 分钟版

```java
public final class BigNumberAddition {
    public static String addNonNegativeDecimalStrings(String a, String b) {
        validateDecimal(a);
        validateDecimal(b);

        int i = a.length() - 1;
        int j = b.length() - 1;
        int carry = 0;
        StringBuilder reversed =
                new StringBuilder(Math.max(a.length(), b.length()) + 1);

        while (i >= 0 || j >= 0 || carry != 0) {
            int da = i >= 0 ? a.charAt(i--) - '0' : 0;
            int db = j >= 0 ? b.charAt(j--) - '0' : 0;
            int sum = da + db + carry;
            reversed.append((char) ('0' + sum % 10));
            carry = sum / 10;
        }

        reversed.reverse();
        int firstNonZero = 0;
        while (firstNonZero < reversed.length() - 1
                && reversed.charAt(firstNonZero) == '0') {
            firstNonZero++;
        }
        return reversed.substring(firstNonZero);
    }

    private static void validateDecimal(String value) {
        if (value == null || value.isEmpty()) {
            throw new IllegalArgumentException("decimal string must be non-empty");
        }
        for (int i = 0; i < value.length(); i++) {
            char c = value.charAt(i);
            if (c < '0' || c > '9') {
                throw new IllegalArgumentException(
                        "decimal string must contain only digits");
            }
        }
    }
}
```

辅助验证函数只接受 `0-9`。例如 `"999" + "1"` 的状态依次产生 `0,0,0`，并把 carry 一直传到最高位，最后得到 `"1000"`；`"000" + "0000"` 则会先得到若干 `0`，再规范化成 `"0"`。

## 关键细节

- **为什么从低位开始**：十进制加法的进位从低位流向高位；从字符串末尾遍历即可让 carry 按自然方向传播。
- **为什么不能直接 `Long.parseLong`**：输入长度可能超过 `long` 可表示范围；先转固定宽度整数会把“大数”问题退化成溢出问题。
- **最高位进位**：循环必须写成 `i >= 0 || j >= 0 || carry != 0`；否则 `99 + 1` 会漏掉最前面的 `1`。
- **前导零**：来源未规定。这里允许输入前导零，但输出做规范化；如果业务要求保留固定宽度，输出契约就要相应改变。
- **非法输入**：负号、小数点、空串、空白和字母都不属于本候选的非负整数契约，直接抛 `IllegalArgumentException`，而不是偷偷解释成别的格式。
- **复杂度**：每个输入字符最多读取一次，时间 O(max(m,n))；输出本身最多 `max(m,n)+1` 位，所以构造结果需要同阶空间。

## 原理机制

每一位只依赖三个状态：当前 `a` 的数字、当前 `b` 的数字和上一轮的 `carry`。因为单个十进制位最多是 9，`9 + 9 + 1 = 19`，所以 `carry` 始终只可能是 0 或 1；当前输出位是总和模 10，下一位进位是整除 10。

这个局部状态保证使算法可以流式从右向左处理任意长度的十进制字符串，不需要把整个数映射到机器整数。若扩展到其他进制，核心不变量不变，只需把基数 10 替换为目标基数并调整字符到数值的解析规则。

## 项目经验版

来源没有真实项目场景，不能虚构“生产上用字符串大数”。项目映射时如果遇到超出内置整数范围的 ID、计数或任意精度运算，应优先确认语言是否已有成熟任意精度类型、输入格式和性能要求；面试手写逐位算法用于证明进位和边界处理能力，不意味着真实系统一定应该重复造 `BigInteger`。

## 常见追问

- 问：两个数长度不一样怎么办？答：短的一侧指针越界后按 0 处理，循环继续直到长的一侧结束且 carry 为 0。
- 问：为什么 `carry` 不会大于 1？答：十进制单个位最大总和是 `9 + 9 + 1 = 19`，整除 10 只能得到 0 或 1。
- 问：如果要支持负数呢？答：需要先解析符号，再根据符号决定做绝对值加法还是大数减法；还要比较绝对值大小，不能只在当前函数前面加一个 `-`。
- 问：能不能支持小数？答：可以，但要先定义小数点对齐、精度和尾零语义；本候选明确只处理非负整数。
- 问：如果输入有一百万位呢？答：算法仍是线性时间，但完整结果本身就需要 O(N) 空间；若输出允许流式写出，还要注意从低位计算与从高位输出之间的方向差异。

## 易错点

- 先把字符串转成 `int`/`long`，直接失去任意长度输入能力。
- 遗漏最终 carry，导致 `999 + 1` 变成 `"000"` 或 `"0000"`。
- 两个指针长度不同时访问越界，没有把缺失位按 0 处理。
- 输入允许前导零却没有定义输出是否规范化，测试口径不一致。
- 没有定义负号、小数点、空串等输入边界，却在代码里随机接受或拒绝。
