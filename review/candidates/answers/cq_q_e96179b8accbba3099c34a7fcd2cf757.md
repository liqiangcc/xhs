<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e96179b8accbba3099c34a7fcd2cf757","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 内存 100M 下统计不同号码的个数

## 核心结论

仓库来源只保留“内存 100M 下统计不同号码的个数”，没有保存号码的位数/取值域、输入规模、输入格式、是否允许磁盘临时文件，以及要求精确值还是近似值。因此不能直接断言“一个 bitmap 就一定够”。这里给出一个可执行的**精确计数**契约：号码先按 32 位有符号整数表示，输入是顺序可读的二进制 `int` 文件，允许使用临时磁盘；100M 视为算法工作内存上限，而不是整个 JVM RSS。

在这个合同下，用“分区 + 位图”做两阶段处理：第一遍按映射后的高 8 位把整数写入 256 个桶；第二遍一次只处理一个桶，桶内只需要覆盖剩余 24 位，因此 bitmap 大小固定为 `2^24` bit = **2 MiB**。扫描桶时某个位从 0 变 1 才把 distinct 计数加 1。这样对整个 32 位整数域都能精确去重，核心工作内存远低于 100M，代价是 O(N) 临时磁盘和两遍顺序 I/O。

## 1 分钟版

- 先问清“号码”的取值域和“精确/近似”要求；100M 只给内存预算，还不足以唯一决定算法。
- 如果值域很小且已知，直接 bitmap：需要的位数就是 universe 大小。
- 当前合同支持任意 32 位整数，所以把完整 `2^32` 域按高 8 位切成 256 桶。
- 每个桶只覆盖低 24 位，一次只加载一个 `2^24` bit 的 bitmap，也就是 2 MiB。
- 第一遍只负责分桶；第二遍读桶并置位，只有“第一次置位”才计数，因此重复号码不会重复计数。
- 如果号码是 11 位字符串/更大整数，不能偷换成 32 位；仍可按前缀或稳定分区做外部分治，或改用外排序。若只要近似 distinct，HyperLogLog 才是更合适的方向。

## 3 分钟版

```java
import java.io.*;
import java.nio.file.*;
import java.util.Arrays;

public final class DistinctNumberCounter {
    private static final int PARTITIONS = 256;
    private static final int LOW_BITS = 24;
    private static final int LOW_MASK = (1 << LOW_BITS) - 1;
    private static final int WORDS = 1 << (LOW_BITS - 6); // 2^24 / 64

    public static long countDistinct(Path input, Path tempDir) throws IOException {
        Files.createDirectories(tempDir);
        Path[] buckets = new Path[PARTITIONS];
        DataOutputStream[] outputs = new DataOutputStream[PARTITIONS];

        try {
            for (int i = 0; i < PARTITIONS; i++) {
                buckets[i] = tempDir.resolve(String.format("bucket-%03d.bin", i));
                outputs[i] = new DataOutputStream(
                    new BufferedOutputStream(Files.newOutputStream(buckets[i]), 8192));
            }

            try (DataInputStream in = new DataInputStream(
                    new BufferedInputStream(Files.newInputStream(input), 1 << 16))) {
                while (true) {
                    int value;
                    try {
                        value = in.readInt();
                    } catch (EOFException eof) {
                        break;
                    }

                    // 把 signed int 单调映射到 [0, 2^32)，便于按高/低位分区。
                    long key = (long) value - Integer.MIN_VALUE;
                    int bucket = (int) (key >>> LOW_BITS);
                    int low = (int) (key & LOW_MASK);
                    outputs[bucket].writeInt(low);
                }
            }
        } finally {
            IOException first = null;
            for (DataOutputStream out : outputs) {
                if (out == null) continue;
                try {
                    out.close();
                } catch (IOException e) {
                    if (first == null) first = e;
                }
            }
            if (first != null) throw first;
        }

        long distinct = 0;
        long[] bitmap = new long[WORDS]; // 262144 longs = 2 MiB payload
        for (Path bucket : buckets) {
            Arrays.fill(bitmap, 0L);
            try (DataInputStream in = new DataInputStream(
                    new BufferedInputStream(Files.newInputStream(bucket), 1 << 16))) {
                while (true) {
                    int low;
                    try {
                        low = in.readInt();
                    } catch (EOFException eof) {
                        break;
                    }
                    int word = low >>> 6;
                    long mask = 1L << (low & 63);
                    if ((bitmap[word] & mask) == 0) {
                        bitmap[word] |= mask;
                        distinct++;
                    }
                }
            }
            Files.deleteIfExists(bucket);
        }
        return distinct;
    }

    private DistinctNumberCounter() {}
}
```

为什么能覆盖完整 32 位整数域？先用 `value - Integer.MIN_VALUE` 把 `[-2^31, 2^31-1]` 单调映射到 `[0, 2^32-1]`。高 8 位决定唯一桶，低 24 位决定桶内唯一 bitmap 位置。因此两个不同整数不可能落到同一个“桶号 + 位号”，同一个整数重复出现又只会命中同一个位。

## 关键细节

- **100M 不等于“必然能建全域 bitmap”**：完整 32 位域需要 `2^32` bit = 512 MiB，仅一个全域 bitmap 就超预算；分 256 桶后一次只保留 2 MiB 位图。
- **精确性来自无冲突映射**：这里不是对号码做普通 hash 再把 hash 当唯一值，而是把 32 位整数拆成高 8 位和低 24 位，组合起来仍然是一一映射，所以没有 hash collision 导致的少计。
- **临时磁盘**：第一阶段会产生大约 `4*N` 字节的桶数据（忽略文件系统开销），这是用磁盘换内存。若禁止磁盘，题目必须额外给值域/输入规模，才能判断是否存在精确的 100M 内存方案。
- **文件句柄与缓冲**：示例打开 256 个 8 KiB 输出缓冲，大约 2 MiB 缓冲；再加 2 MiB bitmap 和少量输入缓冲，算法结构本身远低于 100M。真实 JVM RSS 还包含堆、类元数据等，需要工程实测。
- **负数处理**：虽然“号码”通常不会是负数，来源没有保存值域；代码为了让 32 位整数合同完整，显式支持负数和 `Integer.MIN_VALUE/MAX_VALUE`。
- **输入格式**：示例用二进制 int 避免把文本解析细节混进核心算法。若输入是文本号码，先严格解析到已声明的数据域，再走同一分区逻辑。
- **失败与清理**：生产实现应把临时目录放到有容量/配额的磁盘，并在异常路径清理残留桶；示例重点展示计数机制。

## 原理机制

这其实是外存算法里的“先缩小局部 universe，再做精确 bitmap”。完整 universe 太大时，把一个值 `x` 拆成 `(partition(x), offset(x))`。只要这个拆分保持一一对应，每个 partition 可以独立去重，最后把各分区 distinct 数相加，因为分区之间互不重叠。

在当前 32 位整数合同里：

- `partition = key >>> 24`，范围 0..255；
- `offset = key & (2^24-1)`，范围 0..2^24-1；
- 每个分区 bitmap 是 2^24 bit；
- 每个输入值在第一遍只写一个桶，第二遍只读一次，所以时间复杂度 O(N)，临时磁盘 O(N)，核心位图空间 O(2^24) bit。

如果 universe 本来就小，例如明确只有几千万个连续编号，第一阶段可以直接省掉；反过来，如果号码是任意长字符串，就应选能够保持精确性的外排序或分区后精确集合，而不是把有限位 hash 当成号码本身。

## 项目经验版

来源没有真实项目规模、号码格式和存储系统信息，不能虚构“线上就是 10 亿手机号”。真实落地我会先确认：号码是否固定长度、是否只含数字、最大 distinct 量、输入是否可重读、可用临时磁盘、是否必须精确。随后用样本测吞吐和临时空间，并对分区倾斜做监控；如果业务只需要近似 DAU/UV 类 distinct 统计，则会单独评估 HyperLogLog 的误差和内存，而不是为了“精确”付出不必要的外存 I/O。

## 常见追问

- 问：为什么不直接用 `HashSet<Integer>`？答：Java boxed `Integer`、HashMap 节点和桶数组都有明显额外开销，100M 下可容纳的 distinct 数远小于“100M / 4”；而且来源没有给数据规模，不能证明它够。
- 问：为什么不直接建 `2^32` bitmap？答：需要 512 MiB，超过 100M。分 256 桶后一次只需要 2 MiB bitmap。
- 问：如果都是 11 位手机号呢？答：来源没有保存这个事实，不能当成本题前提。若确认是 11 位数字，可按前缀/数值区间进一步分区，使每个子域 bitmap 能放进预算；也可以外排序后相邻去重。
- 问：普通 hash 分桶会不会碰撞？答：hash 只用于决定桶时可以接受，但桶内仍必须保存/比较原始值才能精确去重。当前实现更强：对 32 位整数直接拆高/低位，本身就是无冲突映射。
- 问：如果只要近似值？答：可以考虑 HyperLogLog；它用很小内存估算基数，但有统计误差，因此不能和“精确 distinct”混为一谈。
- 问：为什么是两遍？答：第一遍把全局问题拆成能在内存里处理的独立子问题；第二遍逐桶精确去重。若输入已经按高位分区存储，就可以省去第一遍分桶。

## 易错点

- 看到 “bitmap” 标签就假定号码范围一定能塞进 100M。
- 用 32 位 hash 值代替原号码做精确 distinct，忽略 hash collision。
- 说 `HashSet<Integer>` 每个元素只占 4 字节，忽略装箱和哈希表结构开销。
- 分桶后同时给每个桶都分配 bitmap，重新把内存放大 256 倍。
- 没说是否允许磁盘，却宣称某个外存算法一定符合题目。
- 把近似算法 HyperLogLog 的结果描述成精确计数。
- 忽略临时磁盘容量、异常清理和输入格式这些工程边界。
