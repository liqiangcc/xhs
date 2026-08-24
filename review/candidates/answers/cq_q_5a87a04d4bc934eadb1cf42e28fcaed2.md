<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_5a87a04d4bc934eadb1cf42e28fcaed2","version":1,"status":"draft","updated_at":"2026-08-25","answer_type":"coding","quality_tier":"candidate"} -->
# IPv4 转 int

## 核心结论

把 IPv4 的四个十进制段依次校验到 `0..255`，每处理一段执行 `result = (result << 8) | octet`，四段后得到完整 32 位位模式。Java `int` 是有符号 32 位，因此最高位为 1 时结果会显示为负数；若需要 `0..4294967295` 的无符号数值，用 `Integer.toUnsignedLong(result)` 查看同一位模式。

## 1 分钟版

- 来源只要求 **IPv4 字符串 -> int**，不把反向转换扩成题目要求。
- 输入契约是四段十进制数字，每段 `0..255`；下面实现明确允许前导零并按十进制解释。
- 从左到右追加字节：旧结果左移 8 位，再把当前段写入低 8 位。
- `255.255.255.255` 的位模式是 `0xffffffff`，Java `int` 显示为 `-1`，无符号解释为 `4294967295`。
- 单次扫描，时间 `O(n)`，额外空间 `O(1)`。

## 3 分钟版

关键不变量是：处理完前 `k` 段后，`result` 的低 `8k` 位按顺序保存这 `k` 个 octet。处理下一段时左移 8 位腾出低字节，再按位或写入当前段；四段后得到完整 32 位地址位模式。每段必须先验证非空、只含十进制数字、最多三位且数值不超过 255，否则非法输入可能被错误映射成另一个地址。

Java 的 `int` 能保存全部 32 个比特，只是按有符号补码解释。需要无符号打印或更宽数值表示时，用 `Integer.toUnsignedLong`；这不会改变低 32 位内容。来源没有规定前导零语义，所以实现必须把它当作自身契约而不是协议事实；这里选择允许，并始终按十进制解析。

```java
public final class Ipv4ToInt {
    public static int parse(String ip) {
        if (ip == null || ip.isEmpty()) throw new IllegalArgumentException("IPv4 text is required");
        int result = 0;
        int octets = 0;
        int value = 0;
        int digits = 0;
        for (int i = 0; i <= ip.length(); i++) {
            char ch = i == ip.length() ? '.' : ip.charAt(i);
            if (ch == '.') {
                if (digits == 0 || octets >= 4) throw new IllegalArgumentException("IPv4 must contain exactly four non-empty octets");
                result = (result << 8) | value;
                octets++;
                value = 0;
                digits = 0;
                continue;
            }
            if (ch < '0' || ch > '9' || digits == 3) throw new IllegalArgumentException("octet must contain one to three decimal digits");
            value = value * 10 + (ch - '0');
            digits++;
            if (value > 255) throw new IllegalArgumentException("IPv4 octet out of range: " + value);
        }
        if (octets != 4) throw new IllegalArgumentException("IPv4 must contain exactly four octets");
        return result;
    }

    public static long asUnsignedLong(int bits) {
        return Integer.toUnsignedLong(bits);
    }

    private Ipv4ToInt() {}
}
```

## 关键细节

- 输入是恰好四段的十进制 IPv4 文本；输出是保存同一 32 位模式的 Java `int`。
- 本实现拒绝 `null`、空串、缺段、多段、空段、非数字、超过三位或数值大于 255 的段。
- 本实现明确允许 `001.002.003.004` 并按十进制解释为 `1.2.3.4`；这只是实现契约。
- Java `int` 为负不代表位模式错误，需要无符号数值时使用 `Integer.toUnsignedLong`。
- 先校验段值再写入 8 位位置，避免非法值越界污染相邻字节。
- 每个字符处理一次，时间 `O(n)`，只使用固定整数变量，额外空间 `O(1)`。

## 原理机制

四段 `a,b,c,d` 对应的 32 位模式等价于 `(a << 24) | (b << 16) | (c << 8) | d`。流式写法只是把它改写成四次相同的状态转移：已有结果左移一个字节，再写入当前低字节。每个段已限制在 `0..255`，因此不会占用超过 8 位。`Integer.toUnsignedLong` 把 `int` 的低 32 位原样扩展到 `long` 并在高位补零，因此可得到相同位模式的无符号数值解释。

## 项目经验版

来源没有提供真实项目经历，不能编造线上使用结果。真实项目映射时，如果只需要内存中的紧凑键，可比较 32 位位模式；如果要写数据库或跨语言接口，应先确认字段的有符号/无符号契约，必要时用 `long` 表达 `0..4294967295`，并用固定地址样例验证跨系统一致性。

## 常见追问

- 问：为什么 `255.255.255.255` 得到 `-1`？答：32 位全为 1，Java 有符号 `int` 按补码解释为 `-1`；低 32 位本身仍正确。
- 问：为什么必须检查每段 `<=255`？答：一个 octet 只有 8 位，超范围值会占用额外高位，破坏地址位布局。
- 问：左移加按位或和乘 256 有什么区别？答：在已校验范围内数值递推等价；位移更直接表达“追加一个字节”的状态变化。
- 问：前导零是否允许？答：题目没规定，本实现明确选择允许且按十进制解释；若模拟具体 JDK、代理或网关，应遵循那个组件的正式解析契约。
- 问：一百万个 IPv4 转 int 后就一定更省内存吗？答：转换只提供 32 位键；实际内存还取决于集合实现、装箱和数据布局，来源没有规定唯一存储方案。

## 易错点

- 把“IPv4 转 int”扩写成双向转换。
- 把负的 Java `int` 误判成转换错误。
- 不校验段数、空段、字符和 `0..255` 范围。
- 拼接方向写反导致字节顺序颠倒。
- 把某个库的前导零解析习惯说成通用协议规则。
