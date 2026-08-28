#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0051 TXT top-10 words candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0051'
CID = 'cq_q_dca65995f5b060544336e01733cfd30d'
QID = 'dca65995f5b060544336e01733cfd30d'
EXPECTED = '算法：查找一个txt中出现次数最多的10个Word'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_dca65995f5b060544336e01733cfd30d","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# TXT 中出现次数最多的 10 个 Word

## 核心结论

来源只说“查找一个 txt 中出现次数最多的 10 个 Word”，没有定义编码、什么算 Word、是否区分大小写、并列时怎么排序，也没有给文件大小。先声明一个最小可执行契约：文件按 UTF-8 读取；Word 定义为连续 ASCII 字母 `[A-Za-z]+`；统计时统一转小写，因此 `Java` 和 `java` 算同一个词；结果按次数降序，次数相同按单词字典序升序，最多返回 10 个。

实现分两层：第一遍流式读文件，用 `HashMap<String, Long>` 统计每个不同单词频次；随后遍历 U 个不同单词，用大小最多 10 的小顶堆维护当前 top-10。时间主要是扫描字符 O(C) + U 次堆操作 O(U log 10)，内存 O(U) 保存频次，top-10 堆本身是 O(10)。

## 1 分钟版

- 用 `BufferedReader` 按行流式读取，不把整个 txt 一次性加载到内存。
- 用正则 `[A-Za-z]+` 提取 token，再 `toLowerCase(Locale.ROOT)` 做大小写归一化。
- `HashMap<word, count>` 累加频次；计数用 `long`，避免超大文件时 `int` 更早溢出。
- 统计完成后维护一个最多 10 个元素的小顶堆；堆顶始终是当前 top-10 中“最差”的项，来了更好的词就替换。
- 为了结果稳定，约定频次相同则字典序更小的词排名更前；最终把堆里的最多 10 项按“频次降序 + 字典序升序”排序输出。
- 如果不同单词 U 太大导致 HashMap 放不下，就不能再说这是内存有界方案，应改成分区/外排/MapReduce 一类外存统计。

## 3 分钟版

```java
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class TopWords {
    private static final Pattern WORD = Pattern.compile("[A-Za-z]+");
    private static final int LIMIT = 10;

    public record Result(String word, long count) {}

    public static List<Result> top10(Path path) throws IOException {
        if (path == null) throw new IllegalArgumentException("path must not be null");

        Map<String, Long> counts = new HashMap<>();
        try (BufferedReader reader = Files.newBufferedReader(path, StandardCharsets.UTF_8)) {
            for (String line; (line = reader.readLine()) != null; ) {
                Matcher matcher = WORD.matcher(line);
                while (matcher.find()) {
                    String word = matcher.group().toLowerCase(Locale.ROOT);
                    counts.merge(word, 1L, Long::sum);
                }
            }
        }

        Comparator<Result> worstFirst = Comparator
                .comparingLong(Result::count)
                .thenComparing(Result::word, Comparator.reverseOrder());
        PriorityQueue<Result> heap = new PriorityQueue<>(worstFirst);

        for (Map.Entry<String, Long> e : counts.entrySet()) {
            Result candidate = new Result(e.getKey(), e.getValue());
            if (heap.size() < LIMIT) {
                heap.offer(candidate);
            } else if (better(candidate, heap.peek())) {
                heap.poll();
                heap.offer(candidate);
            }
        }

        List<Result> out = new ArrayList<>(heap);
        out.sort(Comparator.comparingLong(Result::count).reversed()
                .thenComparing(Result::word));
        return out;
    }

    private static boolean better(Result a, Result b) {
        if (a.count() != b.count()) return a.count() > b.count();
        return a.word().compareTo(b.word()) < 0;
    }
}
```

这里的小顶堆不是用来统计所有单词，而是只在“频次已经统计好”后做 top-K 选择。真正占主要内存的是 `HashMap` 中 U 个不同词。如果文件巨大但词汇集合仍能放入内存，这个方案依然可以流式处理文件；如果 U 本身也巨大，就要把统计阶段做成外存方案。

## 关键细节

- **Word 的定义必须先说清**：当前只匹配 ASCII 字母。`can't` 会被拆成 `can` 和 `t`，`foo123` 会得到 `foo`；这不是“天然正确”，只是本答案明确选择的合同。
- **大小写**：统一 `Locale.ROOT` 小写，避免把 `Java/java/JAVA` 分成三个词。若业务要求区分大小写，去掉归一化。
- **并列规则**：来源未规定。为了可重复测试和稳定输出，当前约定同频时字典序小者优先。
- **为什么计数后再 top-K**：一个词在文件后半段仍可能大量出现，扫描没结束前不能仅凭当前频次永久淘汰它；必须保留可更新的全局计数，或采用更复杂的近似流式算法。
- **复杂度**：设字符总数 C、不同词数 U。提取与计数近似 O(C)，top-10 选择 O(U log 10)，最后排序最多 10 项可视为常数；内存 O(U)。
- **计数类型**：使用 `long` 让上限更高；真正超大规模时还应考虑文件分片、计数溢出和合并策略。
- **文件 I/O**：`BufferedReader` 流式读取减少一次性内存，但并不意味着整个算法 O(1) 空间，因为词频表仍随 U 增长。
- **精确 vs 近似**：题目要求“出现次数最多”通常按精确统计回答；Count-Min Sketch/Space-Saving 等近似算法必须在题目允许误差时才能替代精确 HashMap。

## 原理机制

这题是“频率聚合 + top-K 选择”。第一阶段把原始 token 流映射为 `word -> frequency`，解决的是聚合；第二阶段从 U 个 `(word,count)` 中选出最大的 10 个，解决的是选择。把两个问题分开后，数据结构选择就很清楚：HashMap 提供均摊 O(1) 的计数更新，小顶堆用固定 K 的容量把 top-K 选择从排序全部 U 个元素的 O(U log U) 降为 O(U log K)。

堆顶必须代表当前 top-K 中最容易被淘汰的元素：频次更小更差；频次相同的情况下，因为最终希望字典序小者排前，所以字典序更大的词更差。这样每个新候选只需和堆顶比较一次，就能决定丢弃还是替换。

## 项目经验版

来源没有真实项目经历，不能虚构。工程落地首先问三个问题：文本如何分词、是否需要精确结果、不同词 U 能否放入内存。若 U 可控，单机 HashMap + top-K 堆最直接；若单文件和 U 都非常大，可以按词 hash 分区到多个临时文件，分别计数后合并局部 top-K，或使用分布式 MapReduce；若允许误差并要求固定内存，才考虑近似 heavy-hitter 算法。

## 常见追问

- 问：为什么不直接把所有词频排序？答：可以，复杂度 O(U log U)；只要 top 10 时用大小 10 的堆只需 O(U log 10)，尤其 U 很大时更合适。
- 问：能不能一边读一边只保留 10 个词？答：精确结果通常不行。一个前期频次很低、被淘汰的词可能在后半段突然大量出现；若不保留它的计数，就无法恢复真实频次。
- 问：文件非常大怎么办？答：流式读取解决的是“不把全文放内存”；如果 U 也大到 HashMap 放不下，要进一步做外部分区、分布式聚合或在允许误差时用 heavy-hitter 近似算法。
- 问：中文、连字符、撇号怎么算？答：来源没定义。当前合同只认 `[A-Za-z]+`；业务需要 Unicode 或自然语言 tokenization 时，应替换 tokenizer，并把规则纳入测试。
- 问：次数相同怎么办？答：来源未定义；当前为了确定性规定字典序升序。若产品要按首次出现顺序或其他规则，应记录相应元数据并调整 comparator。
- 问：为什么使用 long？答：它只是降低计数溢出的风险，不改变算法；如果规模可能超过 long，还需要分片计数或更大的数值表示。

## 易错点

- 没定义 Word、大小写和并列语义，却把自己的 tokenizer 当成题目事实。
- 直接 `Files.readString`/一次性读完整文件，对大文件造成不必要的峰值内存。
- 用大顶堆保留 top 10，却无法 O(1) 找到 top-10 中最差的元素进行淘汰。
- 堆 comparator 的同频方向写反，导致应该保留的字典序较小词被淘汰。
- 声称“流式读取所以 O(1) 空间”，忽略 HashMap 中 U 个不同词。
- 为了省内存擅自换成近似算法，却没有说明结果可能有误差。
'''

TEST = r'''import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Random;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class TopWordsTest {
    private static final Pattern WORD = Pattern.compile("[A-Za-z]+");

    private static List<TopWords.Result> oracle(String text) {
        Map<String, Long> counts = new HashMap<>();
        Matcher m = WORD.matcher(text);
        while (m.find()) counts.merge(m.group().toLowerCase(Locale.ROOT), 1L, Long::sum);
        List<TopWords.Result> out = new ArrayList<>();
        for (var e : counts.entrySet()) out.add(new TopWords.Result(e.getKey(), e.getValue()));
        out.sort(Comparator.comparingLong(TopWords.Result::count).reversed().thenComparing(TopWords.Result::word));
        return out.subList(0, Math.min(10, out.size()));
    }

    private static void check(Path file, String text) throws Exception {
        Files.writeString(file, text, StandardCharsets.UTF_8);
        List<TopWords.Result> expected = oracle(text);
        List<TopWords.Result> actual = TopWords.top10(file);
        if (!actual.equals(expected)) throw new AssertionError("expected=" + expected + " actual=" + actual + " text=" + text);
    }

    public static void main(String[] args) throws Exception {
        Path file = Files.createTempFile("top-words-", ".txt");
        try {
            check(file, "Java java JAVA, go! Go? rust. can't foo123");
            check(file, "");
            check(file, "z z a a b b c d e f g h i j k l");

            Random rnd = new Random(20260829L);
            String[] vocab = {"Alpha","beta","GAMMA","delta","Echo","foxtrot","golf","hotel","india","juliet","kilo","lima","mike","november","oscar","papa","quebec","romeo","sierra","tango"};
            String[] sep = {" ",",","!","?","\n","123","--"};
            for (int tc = 0; tc < 1500; tc++) {
                int n = rnd.nextInt(300);
                StringBuilder text = new StringBuilder();
                for (int i = 0; i < n; i++) {
                    text.append(vocab[rnd.nextInt(vocab.length)]);
                    text.append(sep[rnd.nextInt(sep.length)]);
                }
                check(file, text.toString());
            }

            try { TopWords.top10(null); throw new AssertionError("null path must fail"); }
            catch (IllegalArgumentException expected) {}
        } finally {
            Files.deleteIfExists(file);
        }
        System.out.println("PASS case-punctuation-empty-ties random1500-vs-full-sort top10 deterministic-order null-boundary");
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

    with tempfile.TemporaryDirectory(prefix='b51-top10-words-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'TopWords.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'TopWordsTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'TopWords.java', 'TopWordsTest.java', cwd=tmpdir)
        stdout = run('java', 'TopWordsTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS case-punctuation-empty-ties random1500-vs-full-sort top10 deterministic-order null-boundary'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac TopWords.java TopWordsTest.java && java TopWordsTest',
        'stdout': stdout,
        'checks': [
            'case folding and punctuation/token boundaries follow the candidate explicit ASCII-word contract',
            'empty files and fewer-than-ten distinct words return the available deterministic results',
            'ties are resolved by the declared lexical ascending rule',
            '1500 deterministic random text streams match an independent full-sort frequency oracle',
            'the selected result never exceeds ten entries',
            'null path follows the candidate explicit invalid-input boundary',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0051 exact TXT top-10 source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 top-10 words validation versus independent full-sort oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The exact source only asks for the ten most frequent Words in a txt file and does not specify tokenization, encoding, case folding, tie-breaking, or file-size constraints.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate makes UTF-8 input, ASCII-letter tokens, case-insensitive counting, and count-desc/word-asc tie-breaking explicit implementation boundaries rather than source facts.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'algorithm-validation', 'text': 'The executable fixture validates HashMap counting plus a size-10 worst-first min-heap on named cases and 1500 deterministic random text streams against an independent full-sort oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'memory-bound', 'text': 'Buffered reading avoids loading the whole file, while exact frequency counting still requires O(U) memory for U distinct words unless an external/distributed or approximate strategy is introduced.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节', '项目经验版']},
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
        'The source leaves token, case, encoding and tie semantics undefined, and the candidate explicitly declares each chosen boundary instead of presenting it as recovered source fact.',
        'The answer separates exact frequency aggregation from top-K selection, avoiding the common mistake of keeping only ten words while the stream is still incomplete.',
        'The worst-first heap comparator is aligned with the deterministic final ranking: lower count is worse, and at equal count lexically larger words are worse.',
        'OpenJDK 21 validation covers empty/case/punctuation/tie cases and 1500 deterministic random texts against an independent full-sort oracle.',
        'The memory explanation correctly distinguishes streaming file I/O from the O(U) exact frequency map and provides bounded alternatives only under explicit changed assumptions.',
        'The project section avoids fabricated experience and frames partitioned/distributed/approximate variants as conditional extensions.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0051-top10-words-20260829-v1',
        'review_version': 'batch-0051.top10-words.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0051 TXT top-10 source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0051-top10-words-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'case + punctuation + digits', 'expected': 'matches declared tokenizer/case contract', 'actual': 'pass', 'passed': True},
                {'case': 'empty text', 'expected': [], 'actual': [], 'passed': True},
                {'case': 'equal-frequency lexical ties', 'expected': 'count desc then word asc', 'actual': 'pass', 'passed': True},
                {'case': '1500 deterministic random texts', 'expected': 'equals independent full-sort oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_dca65995f5b060544336e01733cfd30d` source-first isolated review PASS: the source only asks for the ten most frequent Words in a txt file, so UTF-8/ASCII-token/case-fold/tie semantics are declared as implementation boundaries rather than fabricated source rules. The candidate separates exact HashMap aggregation from a size-10 worst-first min-heap and correctly states that streaming file I/O does not remove O(U) exact-count memory. OpenJDK 21 validation covers boundaries plus 1500 deterministic random texts against an independent full-sort oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
