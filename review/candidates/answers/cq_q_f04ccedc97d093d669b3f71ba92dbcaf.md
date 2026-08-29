<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f04ccedc97d093d669b3f71ba92dbcaf","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 基于 HashMap 的字符串频率统计并按频次降序输出

## 核心结论

来源保留了三个要求：用 HashMap 做字符串频率统计、按出现次数从高到低输出、处理字符边界并关注排序效率；但没有保存语言、所谓“字符”究竟指 UTF-16 `char`、Unicode code point 还是用户可见 grapheme cluster，也没有给并列频次的顺序。这里声明 Java 合同：按 **Unicode code point** 统计，避免把一个补充平面字符拆成两个 surrogate；按频次降序，频次相同时按 code point 数值升序，得到确定性结果。若业务要求用户可见字素簇，还需要更高层 Unicode 分段库，不能把 code point 冒充 grapheme cluster。

统计阶段遍历 `input.codePoints()`，用 `HashMap<Integer, Long>` 累加；排序阶段只排序不同 code point 的条目。设字符串含 C 个 code point、不同 code point 数为 U，则计数平均 O(C)，排序 O(U log U)，额外空间 O(U)，比先展开 C 个字符再整体排序更符合“频率统计 + 排序”的结构。

## 1 分钟版

- Java 的 `char` 是 UTF-16 code unit，补充平面字符会占两个 `char`；所以当前合同使用 `String.codePoints()`。
- 每个 code point 在 `HashMap<Integer, Long>` 中 `merge(cp, 1L, Long::sum)`。
- 统计完成后把 U 个不同字符转成条目列表，而不是把原字符串 C 个字符拿去排序。
- 排序规则：`count` 降序；并列时按 `codePoint` 升序，避免 HashMap 迭代顺序导致输出不稳定。
- 空字符串返回空列表；`null` 直接拒绝。
- 复杂度：平均计数 O(C)，排序 O(U log U)，空间 O(U)。
- code point 仍不等于用户眼里的一个字符；组合附加符和 emoji ZWJ 序列需要 grapheme cluster 语义时必须另定合同。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class StringFrequency {
    public record Entry(int codePoint, long count) {
        public String symbol() {
            return new String(Character.toChars(codePoint));
        }
    }

    public static List<Entry> countAndSort(String input) {
        if (input == null) throw new IllegalArgumentException("input must not be null");

        Map<Integer, Long> counts = new HashMap<>();
        input.codePoints().forEach(cp -> counts.merge(cp, 1L, Long::sum));

        List<Entry> result = new ArrayList<>(counts.size());
        for (Map.Entry<Integer, Long> e : counts.entrySet()) {
            result.add(new Entry(e.getKey(), e.getValue()));
        }
        result.sort(
            Comparator.comparingLong(Entry::count).reversed()
                      .thenComparingInt(Entry::codePoint)
        );
        return result;
    }

    private StringFrequency() {}
}
```

例如输入 `"😀😀你你你a"` 时，`😀` 是一个 code point 而不是两个 surrogate；结果按当前合同是 `你×3`、`😀×2`、`a×1`。如果 `a/b/c` 都出现两次，则按 code point 升序稳定输出 `a,b,c`。

## 关键细节

- **字符边界**：`String.length()` 和 `charAt()` 面向 UTF-16 code unit；直接按 `char` 计数会把 U+FFFF 之外的字符拆开。`codePoints()` 至少保证 code point 边界正确。
- **不是 grapheme cluster**：`e + combining acute` 可能是两个 code point，但用户视觉上像一个字素；来源没有保存这种更强语义，候选不虚构。
- **并列频次**：来源只要求频次降序，未定义 tie-break。当前实现选择 code point 升序作为确定性合同，而不是依赖 HashMap 的非顺序语义。
- **为什么只排序 U 个条目**：频率已经聚合，相同字符无需重复参与排序；当 U 远小于 C 时可显著减少排序对象数。
- **计数类型**：使用 `long` 避免把计数上限不必要地绑定到 `int`；真实 Java `String` 长度本身仍受实现/内存上限约束。
- **输出形式**：返回结构化 `Entry`，展示层再决定打印格式，避免算法和 I/O 文案耦合。

## 原理机制

频率统计先把原始 code point 流映射成“code point → count”的聚合关系；HashMap 提供平均 O(1) 的查找/更新，因此只需一趟扫描。排序发生在聚合后的 U 个键上，比较器首先比较 `count` 的逆序，再用 `codePoint` 完成全序，因此最终输出与 HashMap 桶布局无关。

这里的关键边界是 Unicode 层级：UTF-16 code unit < Unicode code point < grapheme cluster。当前实现明确选择中间层，解决 surrogate 拆分问题，但不声称解决所有“用户可见字符”分段问题。

## 项目经验版

来源没有真实文本规模、语言分布或性能数据，不能虚构线上收益。工程里若 U 很大但只需要 Top-K，应改用大小为 K 的堆，把排序从 O(U log U) 降到 O(U log K)；若要完整有序输出，则 O(U log U) 比较排序是直接方案。若产品语义是“用户可见字符”，应先选定 Unicode grapheme segmentation 实现，再做同样的聚合和排序。

## 常见追问

- 问：为什么不用 `char`？答：Java `char` 是 UTF-16 code unit，一个 emoji 等补充平面字符通常由 surrogate pair 组成，按 `char` 会拆成两个键。
- 问：`codePoints()` 就等于真正的“字符”了吗？答：不一定。多个 code point 可以组成一个 grapheme cluster；当前合同只保证 code point 边界。
- 问：为什么频次相同还要定义顺序？答：来源没有要求，但 HashMap 本身不承诺业务顺序；加确定性 tie-break 能让测试和调用方行为稳定，同时明确这只是实现合同。
- 问：如果只要前 10 名呢？答：统计仍是 O(C)，随后用大小 10 的最小堆可把完整排序改为 O(U log 10)。
- 问：为什么不是 O(C log C)？答：我们不排序原始 C 个字符，只排序聚合后的 U 个不同键，所以是平均 O(C + U log U)。

## 易错点

- 用 `charAt()` 统计并宣称支持所有 Unicode 字符。
- 直接遍历 HashMap 输出，导致同一输入在不同实现细节下没有稳定的并列顺序。
- 把 C 个原始字符全部排序后再计数，忽略先聚合可把排序规模降到 U。
- 把 code point 和 grapheme cluster 混为一谈。
- 为了 Top-K 仍然完整排序全部 U 个条目，却没有说明性能取舍。
