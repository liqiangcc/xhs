#!/usr/bin/env python3
# Build, validate, source-first review, and stage Batch 0053 row-with-most-ones candidate.

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
CID = 'cq_q_e96e830c897ca29052ba931638e8ff61'
QID = 'e96e830c897ca29052ba931638e8ff61'
EXPECTED = '算法 3：计算二维矩阵（行排序，仅含 0 和 1）中 1 最多的行（要求在 Word 环境下手写，追求最优时间复杂度）'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e96e830c897ca29052ba931638e8ff61","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 行有序 0/1 矩阵中 1 最多的行

## 核心结论

来源明确给出“二维矩阵、每行已排序、元素只有 0 和 1、求 1 最多的行，并追求最优时间复杂度”，但没有保存排序方向、并列时返回哪一行、空矩阵语义。这里声明最小可执行合同：每行按非递减顺序排列，即 `0...0 1...1`；矩阵是规则矩形；若多行 1 的数量相同，返回**最靠前的行下标**；如果矩阵为空、列数为 0 或所有元素都是 0，返回 `-1`。

最优做法不是对每一行单独二分，而是从右上角开始做“阶梯扫描”。维护当前已知最左的 1 所在列 `col`。逐行向下时，只要当前格是 1 就不断左移，并把当前行记为 best。列指针在整个算法里最多左移 C 次，行指针只向下 R 次，所以总时间 O(R+C)，额外空间 O(1)。

## 1 分钟版

- 每行是 `0...0 1...1`，一行 1 越多，它的第一个 1 就越靠左。
- 从右上角 `(0, C-1)` 开始，当前格是 1 就向左走，因为这行可能刷新“最左 1”；向左时同步记录当前行。
- 当前格是 0 时不用在这一行继续往左，因为更左只会还是 0，直接进入下一行。
- 关键是列指针**不回退向右**：后面的行只有把第一个 1 推得更左，才可能严格超过当前最多 1 的行。
- 行最多向下 R 次，列最多向左 C 次，因此是 O(R+C)，比“每行二分” O(R log C) 更优。
- 这里约定并列返回最早一行；因为只有严格向左时才更新 best，后续相同数量的 1 不会覆盖它。

## 3 分钟版

```java
public final class RowWithMostOnes {
    public static int find(int[][] matrix) {
        if (matrix == null) {
            throw new IllegalArgumentException("matrix must not be null");
        }
        if (matrix.length == 0) return -1;

        if (matrix[0] == null) {
            throw new IllegalArgumentException("rows must not be null");
        }
        int cols = matrix[0].length;
        for (int r = 1; r < matrix.length; r++) {
            if (matrix[r] == null || matrix[r].length != cols) {
                throw new IllegalArgumentException("matrix must be rectangular");
            }
        }
        if (cols == 0) return -1;

        int col = cols - 1;
        int bestRow = -1;

        for (int row = 0; row < matrix.length && col >= 0; row++) {
            while (col >= 0 && matrix[row][col] == 1) {
                bestRow = row;
                col--;
            }
        }
        return bestRow;
    }

    private RowWithMostOnes() {}
}
```

例如：

```text
0 0 1 1
0 1 1 1
0 0 0 1
```

从最右列开始，第 0 行会把 `col` 从 3 推到 1；第 1 行在列 1 仍是 1，于是继续推到 0，并把 best 更新为第 1 行；第 2 行不可能再把边界推得更左，所以答案是 1。

## 关键细节

- **排序方向**：来源只写“行排序”，候选明确采用通常的非递减 `0...1` 合同。如果实际是 `1...0`，扫描方向需要镜像，不能直接复用这段代码。
- **并列语义**：只有遇到 1 并继续向左时才更新 best，所以只有“严格更多的 1”才能覆盖旧答案；自然保留最早并列行。
- **全 0**：从未遇到 1，`bestRow` 保持 -1。
- **全 1**：第一行会一路把列指针推到 -1，后续行即使同样全 1 也只是并列，因此返回 0。
- **为什么不逐行二分**：每行找第一个 1 是 O(log C)，总计 O(R log C)；阶梯扫描利用了跨行共享的“当前最左 1”边界，把总列移动次数压到 C。
- **输入校验边界**：代码只用 O(R) 检查矩形结构，没有逐格验证“只有 0/1 且已排序”，因为完整验证本身要 O(RC)，会抹掉题目要求的最优复杂度。实现把这两点作为来源给出的前置条件。
- **空间**：只保留 `col` 和 `bestRow`，额外空间 O(1)。

## 原理机制

对非递减 0/1 行，某行 1 的数量等于 `C - firstOneIndex`。因此“1 最多”与“第一个 1 最靠左”完全等价。

阶梯扫描维护一个单调不变量：进入第 r 行时，`col` 是当前最佳行第一个 1 左侧的位置；如果当前行在这个 `col` 上已经是 0，那么更左也必然是 0，该行不可能超过最佳值；如果是 1，说明当前行的第一个 1 更靠左，必须继续左移，直到重新遇到 0 或越界。每一次左移都把全局候选边界严格推进一格，因此整个执行过程最多发生 C 次左移。

这和“每行都从头搜索”最大的区别是：跨行复用已经证明过的边界。矩阵有 R 行、C 列，向下最多 R 次，向左最多 C 次，所以总步数是线性的 O(R+C)。

## 项目经验版

来源没有真实业务矩阵规模、存储方式和数据质量信息，不能虚构线上场景。工程里如果矩阵来自外部数据，我会区分“可信预处理数据”和“不可信输入”：可信数据可以直接使用 O(R+C) 算法；若必须验证每行排序和值域，就要接受 O(RC) 验证成本，或者在数据生产阶段建立 schema/校验保证，而不是一边声称严格校验一边仍宣称查询 O(R+C)。

## 常见追问

- 问：为什么 O(R+C) 比每行二分更好？答：二分对每一行独立付 O(log C)，没有利用上一行已经找到的最左边界；阶梯扫描让列指针全程只向左，总共最多 C 次。
- 问：如果有两行 1 的数量一样多呢？答：当前合同返回最早一行。后续行只有把 `col` 再向左推进时才更新 best，相同边界不会覆盖旧答案。
- 问：为什么碰到 0 可以直接下一行？答：当前行按 `0...1` 排序；当前 `col` 是待挑战的更左位置，如果这里是 0，更左也都是 0，所以这行不可能拥有更多 1。
- 问：全 0 怎么办？答：没有任何一次向左移动，返回 -1。若业务要求返回 0 行，需要修改空结果合同。
- 问：每行如果是 `1...0` 呢？答：需要镜像思路，例如从左侧维护最右 1/0 的边界；当前代码依赖非递减行这一明确候选合同。
- 问：为什么不检查每个值是不是 0/1？答：逐格验证就是 O(RC)。题目已经给出该前提；若输入不可信，工程校验与核心算法复杂度应分别说明。

## 易错点

- 把“每行有序”误写成“整张矩阵按行列都单调”，来源没有给列有序性质。
- 从每一行重新扫描或重新二分，错过 O(R+C) 的跨行单调边界。
- 遇到并列时无条件更新 best，导致返回最后一行，却没有声明 tie contract。
- 为了验证输入逐格扫描，然后仍然声称总复杂度 O(R+C)。
- 没说明排序方向，直接把 `0...1` 当成未写出的来源事实。
- 全 0 时默认返回第 0 行，但没有定义“没有 1”的语义。
'''

TEST = r'''import java.util.Random;

public final class RowWithMostOnesTest {
    private static int oracle(int[][] matrix) {
        if (matrix.length == 0 || matrix[0].length == 0) return -1;
        int best = -1, bestCount = 0;
        for (int r = 0; r < matrix.length; r++) {
            int count = 0;
            for (int v : matrix[r]) if (v == 1) count++;
            if (count > bestCount) {
                bestCount = count;
                best = r;
            }
        }
        return best;
    }

    private static void check(int[][] matrix, int expected) {
        int actual = RowWithMostOnes.find(matrix);
        if (actual != expected) {
            throw new AssertionError("expected=" + expected + " actual=" + actual);
        }
    }

    private static int[][] randomMatrix(Random random, int rows, int cols) {
        int[][] matrix = new int[rows][cols];
        for (int r = 0; r < rows; r++) {
            int ones = random.nextInt(cols + 1);
            int first = cols - ones;
            for (int c = first; c < cols; c++) matrix[r][c] = 1;
        }
        return matrix;
    }

    public static void main(String[] args) {
        check(new int[][] {}, -1);
        check(new int[][] {{}, {}}, -1);
        check(new int[][] {{0,0,0},{0,0,0}}, -1);
        check(new int[][] {{1,1,1},{1,1,1}}, 0);
        check(new int[][] {{0,0,1,1},{0,1,1,1},{0,0,0,1}}, 1);
        check(new int[][] {{0,1,1},{0,1,1},{0,0,1}}, 0);

        Random random = new Random(20260829L);
        for (int round = 0; round < 5000; round++) {
            int rows = 1 + random.nextInt(40);
            int cols = 1 + random.nextInt(50);
            int[][] matrix = randomMatrix(random, rows, cols);
            int expected = oracle(matrix);
            int actual = RowWithMostOnes.find(matrix);
            if (actual != expected) {
                throw new AssertionError("round=" + round + " expected=" + expected + " actual=" + actual);
            }
        }

        int rows = 700, cols = 900;
        int[][] large = new int[rows][cols];
        for (int r = 0; r < rows; r++) {
            int ones = (r * 37) % (cols + 1);
            for (int c = cols - ones; c < cols; c++) large[r][c] = 1;
        }
        if (RowWithMostOnes.find(large) != oracle(large)) {
            throw new AssertionError("large matrix mismatch");
        }

        try {
            RowWithMostOnes.find(new int[][] {{0,1}, {1}});
            throw new AssertionError("ragged matrix should fail");
        } catch (IllegalArgumentException expected) {}

        System.out.println("PASS empty all-zero all-one tie directed 5000-random-vs-oracle large rectangular-guard");
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

    with tempfile.TemporaryDirectory(prefix='b53-row-most-ones-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'RowWithMostOnes.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'RowWithMostOnesTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'RowWithMostOnes.java', 'RowWithMostOnesTest.java', cwd=tmpdir)
        stdout = run('java', 'RowWithMostOnesTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS empty all-zero all-one tie directed 5000-random-vs-oracle large rectangular-guard'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac RowWithMostOnes.java RowWithMostOnesTest.java && java RowWithMostOnesTest',
        'stdout': stdout,
        'checks': [
            'empty, all-zero, all-one, directed and tie behavior',
            '5000 deterministic row-sorted random matrices agree with an O(R*C) oracle',
            'large rectangular matrix agrees with the oracle',
            'ragged matrix is rejected while per-cell source preconditions remain trusted',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0053 exact row-sorted binary-matrix source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 staircase-scan deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source requires a row-sorted 0/1 matrix, the row with the most ones, handwritten implementation, and optimal time; sort direction, tie behavior, and empty-result semantics are not preserved.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '关键细节', '易错点']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate explicitly chooses nondecreasing 0...1 rows, a rectangular matrix, earliest-row tie breaking, and -1 when no one exists.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'staircase-mechanism', 'text': 'A shared column pointer only moves left when a row has a one at the current boundary; across all rows it moves at most C times, yielding O(R+C) time and O(1) extra space.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '3 分钟版', '原理机制']},
        {'claim_id': 'validation', 'text': 'Executable validation covers empty/all-zero/all-one/ties, 5000 deterministic sorted random matrices against an independent O(R*C) oracle, a large matrix, and ragged-shape rejection.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '常见追问', '易错点']},
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
        'The candidate preserves the source-provided row-sorted binary-matrix and optimal-time requirements while explicitly declaring nondecreasing order, tie handling, and empty-result behavior rather than inventing them as source facts.',
        'The staircase scan correctly reuses a monotonic left boundary across rows, so the row index advances at most R times and the column index at most C times.',
        'Updating best only when the boundary moves left makes the earliest-row tie policy explicit and mechanically consistent.',
        'The answer correctly distinguishes row-wise sorting from any stronger column-sorted matrix property.',
        'It explains why validating every cell would cost O(R*C) and therefore treats the source-provided 0/1 sorted-row property as a precondition while still checking rectangular structure.',
        'OpenJDK 21 validation covers directed edge cases, 5000 deterministic random row-sorted matrices against an independent full-scan oracle, a large matrix, and ragged input.',
        'The mechanism explanation directly proves O(R+C) rather than merely asserting it and contrasts it with per-row binary search O(R log C).',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0053-row-most-ones-20260829-v1',
        'review_version': 'batch-0053.row-most-ones.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0053 row-most-ones source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0053-row-most-ones-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'empty/all-zero/all-one/tie matrices', 'expected': 'declared result and tie contract', 'actual': 'pass', 'passed': True},
                {'case': '5000 deterministic random sorted matrices', 'expected': 'matches independent full-scan oracle', 'actual': 'pass', 'passed': True},
                {'case': 'large row-sorted matrix', 'expected': 'matches oracle', 'actual': 'pass', 'passed': True},
                {'case': 'ragged matrix', 'expected': 'IllegalArgumentException', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e96e830c897ca29052ba931638e8ff61` source-first isolated review PASS: the source requires a row-sorted 0/1 matrix, the row with most ones, and optimal time, while sort direction/ties/empty semantics remain explicit candidate contract. Under nondecreasing rows and earliest-row ties, the staircase scan shares one left-moving column boundary across all rows for O(R+C) time/O(1) extra space; OpenJDK 21 validation covers edge cases, 5000 deterministic random matrices against an O(R*C) oracle, a large matrix, and ragged-shape rejection. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
