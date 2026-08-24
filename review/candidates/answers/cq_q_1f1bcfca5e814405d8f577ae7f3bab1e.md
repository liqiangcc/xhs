<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_1f1bcfca5e814405d8f577ae7f3bab1e","version":1,"status":"draft","updated_at":"2026-08-23","quality_tier":"candidate","answer_type":"coding"} -->
# 大文件 Top 10：流式扫描 + 固定大小小顶堆

## 核心结论

仓库原始面经保留的问题是：**“N 个数的文件中，怎么搜索到前 10 大的数字？”**。原始记录没有说明数字类型、文件编码、重复值是否保留、坏行如何处理，以及 `N < 10` 时的返回行为。

下面把这些缺失点明确收窄为候选实现契约：UTF-8 文本文件，每个非空行一个 `long`；重复出现的数字按出现次数参与 Top 10；遇到非法数字行立即报错；若有效数字少于 10 个，则返回全部数字。它们是候选 API 选择，不冒充原题条件。

在这个契约下，只需顺序读取文件并维护一个**最多 10 个元素的小顶堆**。堆未满时直接加入；堆满后，只有当前数字大于堆顶时才弹出堆顶并加入当前数字。扫描结束后，堆里恰好是全文件最大的 10 个数（或不足 10 个时的全部数）。时间复杂度是 `O(N log 10)`，辅助状态是 `O(10)`，不需要把整个文件载入内存。

## 1 分钟版

关键是让堆顶始终代表“当前 Top 10 里最小的那个”。

读到一个数字 `x` 时：

1. 堆不到 10 个元素，直接放进去；
2. 堆已经有 10 个元素，若 `x <= heap.peek()`，它不可能进入当前 Top 10，丢弃；
3. 若 `x > heap.peek()`，弹出当前第 10 大候选，再放入 `x`。

这样每次处理后，堆都保存“已读前缀的最大 10 个数”。文件只扫描一次，内存不会随 `N` 增长。

## 3 分钟版

设 `K=10`。维护不变量：处理完前 `i` 个输入后，小顶堆包含这 `i` 个数中最大的 `min(K, i)` 个数，并且堆顶是这些候选中的最小值。

- 当堆未满时，所有已读元素都应被保留，所以直接插入。
- 当堆已满且 `x <= heap.peek()` 时，堆中已有 `K` 个数都不小于堆顶，因此 `x` 不可能挤进最大的 `K` 个。
- 当堆已满且 `x > heap.peek()` 时，当前堆顶是旧候选中唯一需要被淘汰的最小者；用 `x` 替换它以后，得到新的 Top K。

这个不变量从空前缀开始成立，并在每次读取后保持，因此扫描完成时得到全文件 Top 10。

如果面试官要的是“最大的 10 个**不同值**”，那是另一个重复语义：需要额外去重策略，不能把它默认为原题条件。

## 关键细节

- **为什么用小顶堆而不是大顶堆**：我们只需要快速找到当前 Top 10 中最弱的候选，也就是最小值。
- **为什么不全量排序**：全量排序需要保存全部 `N` 个数，通常是 `O(N log N)` 时间和 `O(N)` 级内存；固定大小堆只保留 10 个候选。
- **重复值**：当前候选契约按出现次数保留。例如最大的数字出现 10 次，它可以占据全部 Top 10。
- **`N < 10`**：返回全部有效数字。
- **坏行**：候选实现 fail-fast；生产场景也可以改成记录坏行并继续，但应作为显式策略。
- **输出顺序**：堆本身不保证降序，所以扫描完成后只对最多 10 个结果排序，代价是 `O(10 log 10)`。
- **超大文件**：算法不依赖文件大小，只要能顺序读取即可；真正的内存上界由读取缓冲区和固定大小堆决定。

## 原理机制

```java
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.PriorityQueue;

public final class FileTopK {
    private FileTopK() {}

    public static List<Long> topK(Path path, int k) throws IOException {
        if (k <= 0) {
            throw new IllegalArgumentException("k must be positive");
        }

        PriorityQueue<Long> minHeap = new PriorityQueue<>(k);
        try (BufferedReader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            String line;
            while ((line = reader.readLine()) != null) {
                String text = line.trim();
                if (text.isEmpty()) {
                    continue;
                }
                long value = Long.parseLong(text);
                if (minHeap.size() < k) {
                    minHeap.add(value);
                } else if (value > minHeap.peek()) {
                    minHeap.poll();
                    minHeap.add(value);
                }
            }
        }

        List<Long> result = new ArrayList<>(minHeap);
        result.sort(Comparator.reverseOrder());
        return result;
    }
}
```

正确性来自前面的前缀不变量。实现中的 `PriorityQueue` 只保留 `k` 个候选；这里调用时令 `k=10`。仓库的确定性测试用“把完整输入排序后截取前 K”作为结构不同的 oracle，覆盖空文件、少于 K、恰好 K、重复值、负数、极值、空白行和 5000 组固定随机种子输入；另有非法数字行与非法 `k` 的边界检查。

## 项目经验版

这是面试场景题，原始材料没有生产项目背景，不应虚构线上规模或性能数据。工程上可以继续追问：文件是否已分片、是否需要分布式 Top K、数据是否能按行解析、坏记录如何处置、结果是否要求 distinct，以及最终 10 个结果是否需要稳定排序。单机文件版本的核心仍是“流式读取 + 有界候选集”。

## 常见追问

- 问：为什么复杂度写成 `O(N log 10)`？答：每个数字最多触发一次固定大小堆的插入/替换；更一般地是 `O(N log K)`。
- 问：能不能写成 `O(N)`？答：当 `K=10` 被视为常数时渐进上可以写 `O(N)`；写 `O(N log K)` 更能表达算法随 K 变化的成本。
- 问：如果要前 10 个不同数字呢？答：需要显式 distinct 语义，可配合集合维护堆内成员，或者根据数据规模采用外部去重；这不是当前原始题干已经给出的条件。
- 问：文件比内存大怎么办？答：该方案只顺序读取，内存不随文件中数字个数增长。
- 问：如果文件分布在多台机器？答：每个分片先算本地 Top 10，再把所有局部候选汇总后再做一次 Top 10；因为任何不在某分片本地 Top 10 的数，都不可能进入全局 Top 10。
- 问：为什么最后还能排序？答：只排序最多 10 个候选，不会退化成全文件排序。

## 易错点

- 用大顶堆却每次淘汰最大值，方向反了。
- 堆满后无条件插入，导致候选数超过 10。
- 把“Top 10”默认为“10 个不同值”，未经题干支持改变重复语义。
- 为了排序结果把整个文件读入数组，失去流式处理的内存优势。
- 忽略 `N < 10`、负数、重复值、极值或坏行策略。
