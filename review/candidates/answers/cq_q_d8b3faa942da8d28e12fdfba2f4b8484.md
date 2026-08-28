<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d8b3faa942da8d28e12fdfba2f4b8484","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 两个数组的交集：先明确“去重”还是“保留重复次数”

## 核心结论

来源只写了“两个数组的交集”，没有给题号，也没有说明重复元素是否只保留一次、结果是否要求有序、是否允许修改输入。因此不能把某一道 LeetCode 的完整契约冒充成原题。

面试时我会先确认重复语义。若按数学集合交集理解：每个公共值只返回一次，可以把较短数组放进 `HashSet`，扫描另一个数组；命中时把值加入结果并从 Set 删除，这样天然去重。期望时间 O(n+m)，额外空间 O(min(n,m))（不计返回结果）。若题意是“重复多少次就交多少次”的多重集交集，则要改成频次表，不能直接用 Set。

## 1 分钟版

- 第一问先确认：`[1,2,2,1]` 和 `[2,2]` 到底返回 `[2]` 还是 `[2,2]`？源题没有说明，这是必须显式补齐的契约。
- **集合交集**：把较短数组元素放入 `HashSet`，扫描较长数组；`set.remove(x)` 成功就记录 x。删除后同一个值不会再次进入结果。
- **多重集交集**：用 `HashMap<值, 次数>` 统计一侧；扫描另一侧时，计数大于 0 才输出并减 1。
- 两种哈希方案平均都只线性扫描输入；如果不能接受哈希额外空间，可以复制后排序，再用双指针做交集，代价变成 O(n log n + m log m)。
- 原题没规定结果顺序，所以答案不把“按升序”或“按输入出现顺序”说成题目要求；若需要稳定顺序，要单独定义。

## 3 分钟版

```java
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public final class ArrayIntersection {
    // 数学集合交集：每个公共值只出现一次；结果顺序不作为契约。
    public static int[] intersectionUnique(int[] a, int[] b) {
        requireArrays(a, b);
        int[] small = a.length <= b.length ? a : b;
        int[] large = a.length <= b.length ? b : a;

        Set<Integer> candidates = new HashSet<>();
        for (int x : small) {
            candidates.add(x);
        }

        int[] tmp = new int[Math.min(a.length, b.length)];
        int size = 0;
        for (int x : large) {
            if (candidates.remove(x)) {
                tmp[size++] = x;
            }
        }
        return Arrays.copyOf(tmp, size);
    }

    // 多重集交集：公共值出现 min(countA, countB) 次。
    public static int[] intersectionWithMultiplicity(int[] a, int[] b) {
        requireArrays(a, b);
        if (a.length > b.length) {
            return intersectionWithMultiplicity(b, a);
        }

        Map<Integer, Integer> counts = new HashMap<>();
        for (int x : a) {
            counts.merge(x, 1, Integer::sum);
        }

        int[] tmp = new int[a.length];
        int size = 0;
        for (int x : b) {
            int left = counts.getOrDefault(x, 0);
            if (left > 0) {
                tmp[size++] = x;
                if (left == 1) {
                    counts.remove(x);
                } else {
                    counts.put(x, left - 1);
                }
            }
        }
        return Arrays.copyOf(tmp, size);
    }

    private static void requireArrays(int[] a, int[] b) {
        if (a == null || b == null) {
            throw new IllegalArgumentException("input arrays must not be null");
        }
    }
}
```

例如 `a=[1,2,2,1]`、`b=[2,2]`：集合语义返回一个 `2`；多重集语义返回两个 `2`。这正是为什么不能看到“数组交集”四个字就直接默认为某一种重复规则。

集合版本使用 `remove` 而不是 `contains`：第一次命中时删除候选，后面再遇到同样的 x 就不会重复输出。多重集版本则不能删除整个键，因为还要保留剩余次数；只能每次减 1，直到计数归零。

## 关键细节

- **重复语义**：这是最重要的契约边界。Set 只能表达“是否存在”，Map 频次才能表达“存在多少次”。
- **结果顺序**：当前来源没有排序要求。上面的哈希实现按被扫描数组的首次命中顺序产生结果，但调用方不应依赖这个顺序；若要求升序，可在结果上排序或直接使用排序双指针方案。
- **空间优化**：集合版本把较短数组放入 Set；多重集版本递归交换参数，确保频次表建立在较短数组上。
- **空数组**：自然得到空结果。`null` 不在原题说明中，本实现把它定义为非法输入并抛异常，这是工程接口扩展，不是来源事实。
- **负数和重复大值**：哈希键按整数值处理，不依赖元素范围，所以不需要额外值域数组。
- **排序方案**：若先对副本排序，两个指针相等时输出并前进；集合语义要跳过相同值，多重集语义则每次相等都输出。若直接排序原数组会修改输入，必须先确认是否允许。
- **复杂度**：哈希表操作按通常平均 O(1) 计，整体期望 O(n+m)；最坏复杂度取决于具体哈希实现与碰撞行为。排序双指针是确定的 O(n log n + m log m)。

## 原理机制

数组交集的本质是“成员关系”与“计数关系”的选择。

集合语义只关心某个值是否同时存在于两边，所以状态只需要一位“有/无”。`HashSet` 正好对应这个模型；命中后删除相当于把该值状态从“待匹配”改成“已消费”，因此同一值最多输出一次。

多重集语义则要求某个值最多输出 `min(countA, countB)` 次，因此状态必须是整数计数。扫描第二个数组时，每消费一次就把剩余次数减 1；计数归零后再遇到同值也不能输出。两种算法代码很像，但状态模型不同，不能混用。

排序双指针是另一种实现：排序把相同值聚在一起，两个指针通过大小比较单调前进。它用排序时间换取少量额外查找空间，也更容易直接得到有序结果，但若排序原数组会改变输入。

## 项目经验版

来源没有真实项目背景，不能虚构。实际业务里“交集”经常出现在权限集合、标签集合、用户分群或 ID 列表筛选中。落地前仍要先确认三件事：重复是否有意义、结果顺序是否稳定、数据量是否大到不适合一次性放入内存。若输入来自超大文件或数据流，通常会进一步考虑排序归并、分桶或外部存储，而不是直接把全部元素塞进 JVM HashMap。

## 常见追问

- 问：为什么 `HashSet` 版本用 `remove` 而不是 `contains`？答：`remove` 同时完成“是否命中”和“只消费一次”两个动作，保证集合交集不会重复输出同一个值。
- 问：如果题目要求 `[1,2,2,1]` 和 `[2,2]` 返回 `[2,2]` 呢？答：那是多重集语义，要用频次 Map；每次匹配后把计数减 1，最多输出两边次数的最小值。
- 问：如果不能用额外哈希空间怎么办？答：可以复制数组后排序，再用双指针；若允许修改输入，可原地排序，时间复杂度提高到排序级别。
- 问：结果必须升序怎么办？答：来源没这个要求；若新增该契约，可以在交集结果上排序，或者直接选择排序双指针方案并自然按升序产生结果。
- 问：为什么优先把较短数组放到哈希表？答：查找次数仍是线性，但辅助结构最多保存较短一侧的 distinct 值或频次，降低峰值空间。
- 问：如果元素是对象而不是 int 呢？答：要先明确相等语义和哈希契约，例如 Java 对象需要一致的 `equals` / `hashCode`；当前实现只针对整数数组。

## 易错点

- 没确认重复语义就把 Set 或计数 Map 当成唯一正确答案。
- 集合交集只用 `contains`，导致第二个数组里重复值被重复加入结果。
- 多重集交集匹配后不减计数，导致输出次数超过第一侧实际拥有的次数。
- 题目没要求顺序，却把 HashSet 的遍历或某个输入顺序写成稳定契约。
- 为省空间直接排序输入数组，却没有确认“允许修改输入”。
- 把哈希方案笼统写成严格 O(n+m) 最坏时间，忽略哈希操作复杂度依赖实现与碰撞行为。
