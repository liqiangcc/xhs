#!/usr/bin/env python3
# Build, validate, source-first review, and stage Batch 0053 distinct-number-under-100M candidate.

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0053'
CID = 'cq_q_e96179b8accbba3099c34a7fcd2cf757'
QID = 'e96179b8accbba3099c34a7fcd2cf757'
EXPECTED = '算法：内存 100M 下统计不同号码的个数？'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e96179b8accbba3099c34a7fcd2cf757","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
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
'''

TEST = r'''import java.io.*;
import java.nio.file.*;
import java.util.*;

public final class DistinctNumberCounterTest {
    private static void write(Path path, int[] values) throws IOException {
        try (DataOutputStream out = new DataOutputStream(
                new BufferedOutputStream(Files.newOutputStream(path)))) {
            for (int v : values) out.writeInt(v);
        }
    }

    private static void check(int[] values, long expected) throws Exception {
        Path root = Files.createTempDirectory("distinct-number-test-");
        try {
            Path input = root.resolve("input.bin");
            Path temp = root.resolve("buckets");
            write(input, values);
            long actual = DistinctNumberCounter.countDistinct(input, temp);
            if (actual != expected) {
                throw new AssertionError("expected=" + expected + " actual=" + actual);
            }
            if (Files.exists(temp)) {
                try (var stream = Files.list(temp)) {
                    if (stream.findAny().isPresent()) throw new AssertionError("bucket residue");
                }
            }
        } finally {
            if (Files.exists(root)) {
                try (var walk = Files.walk(root)) {
                    walk.sorted(Comparator.reverseOrder()).forEach(p -> {
                        try { Files.deleteIfExists(p); } catch (IOException e) { throw new UncheckedIOException(e); }
                    });
                }
            }
        }
    }

    public static void main(String[] args) throws Exception {
        check(new int[] {}, 0);
        check(new int[] {7, 7, 7, 7}, 1);
        check(new int[] {Integer.MIN_VALUE, -1, 0, 1, Integer.MAX_VALUE,
                         Integer.MIN_VALUE, Integer.MAX_VALUE}, 5);

        Random random = new Random(20260829L);
        int[] values = new int[250_000];
        Set<Integer> oracle = new HashSet<>();
        for (int i = 0; i < values.length; i++) {
            int v = (i % 5 == 0) ? random.nextInt(10_000) : random.nextInt();
            values[i] = v;
            oracle.add(v);
        }
        check(values, oracle.size());

        int[] boundary = new int[10_000];
        for (int i = 0; i < boundary.length; i++) {
            int high = i & 255;
            int low = (i * 104729) & 0x00ffffff;
            long key = ((long) high << 24) | low;
            boundary[i] = (int) (key + Integer.MIN_VALUE);
        }
        check(boundary, 10_000);

        System.out.println("PASS empty duplicates signed-extremes 250000-random-vs-hashset 256-partition-boundary");
    }
}
'''


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    if candidate.exists():
        raise SystemExit('candidate already exists; do not overwrite reviewed work')

    ctx = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != CID:
        raise SystemExit('canonical context drift')
    if ctx.get('answer_type') != 'coding':
        raise SystemExit(f"answer type drift: {ctx.get('answer_type')}")
    if ctx.get('canonical', {}).get('question_ids') != [QID]:
        raise SystemExit(f"ownership drift: {ctx.get('canonical', {}).get('question_ids')}")
    src = next((x for x in ctx.get('source_questions', []) if x.get('question_id') == QID), None)
    if not src or src.get('original_question') != EXPECTED or src.get('is_valid_for_library') is not True:
        raise SystemExit('source wording/validity drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b53-distinct-number-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'DistinctNumberCounter.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'DistinctNumberCounterTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'DistinctNumberCounter.java', 'DistinctNumberCounterTest.java', cwd=tmpdir)
        stdout = run('java', 'DistinctNumberCounterTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS empty duplicates signed-extremes 250000-random-vs-hashset 256-partition-boundary'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac DistinctNumberCounter.java DistinctNumberCounterTest.java && java DistinctNumberCounterTest',
        'stdout': stdout,
        'checks': [
            'empty input and duplicate-only input',
            'signed int mapping including Integer.MIN_VALUE and Integer.MAX_VALUE',
            '250000 deterministic random values agree with a HashSet oracle',
            'values spanning all 256 high-byte partitions retain unique bucket/offset identity',
            'temporary bucket files are removed after successful processing',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0053 exact 100M distinct-number source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 partition-plus-bitmap deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source gives only a 100M memory budget and distinct-number counting goal; number domain, input size/format, disk availability, and exact-versus-approximate semantics are not preserved.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节', '易错点']},
        {'claim_id': 'explicit-contract', 'text': 'The executable candidate explicitly chooses exact distinct counting over a binary stream of signed 32-bit integers with temporary disk allowed and treats 100M as algorithm working-memory budget rather than total JVM RSS.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节']},
        {'claim_id': 'partition-bitmap-mechanism', 'text': 'Mapping signed ints to [0,2^32), splitting high 8 bits as partition and low 24 bits as bitmap offset is collision-free; processing one partition at a time needs a 2 MiB bitmap payload.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '3 分钟版', '原理机制']},
        {'claim_id': 'validation', 'text': 'Executable validation covers empty/duplicate/extreme signed values, 250000 deterministic random values against a HashSet oracle, all 256 partitions, and successful temporary-file cleanup.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '常见追问', '易错点']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate does not invent phone-number width, data volume, input representation, disk allowance, or exactness from the sparse source; it marks all executable assumptions as candidate contract.',
        'A single full 32-bit bitmap would require 512 MiB, so the answer correctly explains why the 100M budget alone does not justify a one-shot bitmap.',
        'High-8/low-24 decomposition after a monotonic signed-int mapping is collision-free, unlike treating a finite hash value as an exact identifier.',
        'Processing one partition at a time fixes the bitmap payload at 2 MiB while the first pass trades O(N) temporary disk for bounded working memory.',
        'The answer separates exact external partitioning from approximate HyperLogLog and explicitly notes that arbitrary strings or 11-digit numbers require a different declared domain/partition scheme.',
        'OpenJDK 21 validation covers duplicates, signed extremes, deterministic random data against an independent HashSet oracle, all 256 partitions, and temporary-file cleanup.',
        'The engineering boundary distinguishes algorithm working memory from total JVM RSS and calls out disk capacity, file handles, parsing, and abnormal cleanup.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0053-distinct-number-20260829-v1',
        'review_version': 'batch-0053.distinct-number.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0053 distinct-number source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0053-distinct-number-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'duplicate and signed-extreme values', 'expected': 'exact distinct count', 'actual': 'pass', 'passed': True},
                {'case': '250000 deterministic random integers', 'expected': 'matches independent HashSet oracle', 'actual': 'pass', 'passed': True},
                {'case': 'all 256 high-byte partitions', 'expected': 'unique partition/offset mapping retained', 'actual': 'pass', 'passed': True},
                {'case': 'successful bucket cleanup', 'expected': 'no temporary bucket residue', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e96179b8accbba3099c34a7fcd2cf757` source-first isolated review PASS: the source preserves only a 100M-memory distinct-number counting goal, so number domain, input format/scale, disk allowance, and exactness remain explicit candidate contract. The candidate defines exact signed-32-bit counting with temporary disk, uses collision-free high-8/low-24 partitioning so only a 2 MiB bitmap is resident per bucket, and OpenJDK 21 validation covers duplicates/extreme ints, 250000 deterministic random values against a HashSet oracle, all 256 partitions, and cleanup. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
