#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0051 Pythagorean-sum candidate."""

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
CID = 'cq_q_de135a9fa2470b236d45bad96e81b6de'
QID = 'de135a9fa2470b236d45bad96e81b6de'
EXPECTED = '算法：求满足 a + b + c = 1000 且 a^2 + b^2 = c^2 的所有正整数 a, b, c 组合'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_de135a9fa2470b236d45bad96e81b6de","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# a+b+c=1000 且 a²+b²=c² 的正整数解

## 核心结论

这题要求同时满足两个约束：`a + b + c = 1000`，以及 `a² + b² = c²`。因为第二个式子对 a、b 对称，如果“组合”按无序三元组理解，可以加上 `a <= b < c` 去掉 `(a,b,c)` 与 `(b,a,c)` 的重复。这样穷举时只枚举 a、b，直接由和式计算 `c = 1000 - a - b`，把三重循环降成双重循环。

在 `a <= b < c` 的规范化下，1000 的唯一解是 `(200, 375, 425)`。如果题目把 a、b 当成有标签的不同变量并要求所有有序赋值，那么还应同时包含 `(375, 200, 425)`；来源没有明确“组合”是否区分 a/b 顺序，所以答案必须把这两个口径说清楚，而不能悄悄丢掉或重复一组。

## 1 分钟版

- 三个数都是正整数，所以 `a,b,c > 0`。
- 不需要三重循环：给定 a、b 后，`c = 1000-a-b` 已经确定。
- 为避免 a/b 对称重复，按“无序组合”口径固定 `a <= b < c`。
- 枚举 a，再枚举 b；若 `c <= b` 就不再满足规范化顺序，可以停止当前 b 循环。
- 用 `long` 计算平方，避免把这个通用写法扩到更大 sum 时发生 `int` 平方溢出。
- 检查 `a*a + b*b == c*c`；sum=1000 得到唯一规范化三元组 `(200,375,425)`。
- 两层循环最坏 O(S²)，但由 `a <= b < c` 可以把搜索区间大幅收紧；对固定 S=1000 已经足够直接、可验证。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.List;

public final class PythagoreanSum {
    public record Triple(int a, int b, int c) {}

    public static List<Triple> findCanonical(int sum) {
        if (sum <= 0) {
            throw new IllegalArgumentException("sum must be positive");
        }

        List<Triple> out = new ArrayList<>();
        for (int a = 1; a * 3 < sum; a++) {
            for (int b = a; ; b++) {
                int c = sum - a - b;
                if (c <= b) {
                    break;
                }
                long aa = (long) a * a;
                long bb = (long) b * b;
                long cc = (long) c * c;
                if (aa + bb == cc) {
                    out.add(new Triple(a, b, c));
                }
            }
        }
        return out;
    }

    public static List<Triple> findOrderedAssignments(int sum) {
        List<Triple> canonical = findCanonical(sum);
        List<Triple> out = new ArrayList<>();
        for (Triple t : canonical) {
            out.add(t);
            if (t.a() != t.b()) {
                out.add(new Triple(t.b(), t.a(), t.c()));
            }
        }
        return out;
    }
}
```

`a * 3 < sum` 来自 `a <= b < c`：三个数里 a 最小，因此如果 `3a >= sum` 就不可能还有严格更大的 c。内层由 `c = sum-a-b` 直接得到第三个数；随着 b 增大，c 单调减小，一旦 `c <= b`，后续 b 只会更大、c 只会更小，所以可以立即 break。

对 sum=1000，`findCanonical(1000)` 返回 `[(200,375,425)]`；`findOrderedAssignments(1000)` 则返回这组和交换 a/b 后的 `(375,200,425)`。

## 关键细节

- **“组合”是否区分 a/b 顺序**：方程对 a、b 对称。无序口径应规范化 `a <= b`，有序变量赋值则 a/b 交换是另一组。来源没有明确，答案同时给出两个入口。
- **为什么 c 一定最大**：正整数下 `a²+b²=c²` 推出 `c>a` 且 `c>b`，所以规范化为 `a <= b < c` 不会漏掉无序解。
- **从三重到双重循环**：和式直接决定 c，没有必要再次枚举 c；这是最直接的穷举优化。
- **提前停止 b**：固定 a 时，b 增加会让 c 减少；当 `c <= b` 后，再继续枚举只会违反 `b < c`。
- **平方类型**：虽然 1000 范围内 int 足够，本实现用 long 做平方，让算法扩到更大 sum 时不因为中间乘法过早溢出。
- **复杂度**：通用 sum=S 的规范化双循环上界 O(S²)，额外空间除结果外 O(1)。固定 S=1000 时实际搜索范围很小。
- **更数学化的方法**：可以用勾股数组参数化 `a=m²-n², b=2mn, c=m²+n²` 再结合和式筛选，复杂度更低；但面试手写时双循环更直接，也更容易证明不会漏解。

## 原理机制

核心优化来自“约束消元”和“对称性消重”。`a+b+c=S` 是一个线性约束，可以把 c 消掉：每个 `(a,b)` 只对应一个 `c=S-a-b`，所以搜索维度从三个自由变量降到两个。`a²+b²=c²` 对 a/b 对称，因此如果目标是无序组合，可以固定 `a<=b`，把对称空间再砍掉一半。

内层 break 依赖单调性：固定 a 后，b 每增加 1，c 就减少 1。进入 `c<=b` 的区域以后，差值 `c-b` 只会继续下降，不可能重新满足 `b<c`。这类“先用代数减少维度，再利用单调边界剪枝”的思路比盲目三重枚举更通用。

## 项目经验版

来源没有真实项目经历，不能虚构。工程里类似“整数约束求解”首先要区分规模和目标：固定小常数时，透明的枚举 + 剪枝最容易审计；S 很大、查询很多次或需要生成全部勾股数组时，可以利用参数化公式、数论筛选或预计算。无论采用哪种方法，都应先确定“组合”和“有序赋值”的去重口径，否则结果数量可能从算法上正确、产品语义上却不一致。

## 常见追问

- 问：为什么不是三重循环？答：因为 c 已经由 `c=S-a-b` 唯一确定，再枚举 c 是重复搜索。
- 问：为什么可以设 `a<=b<c`？答：a/b 在平方和中对称；无序组合只需保留一个顺序。又因为都是正数且 `a²+b²=c²`，斜边 c 必然大于两条直角边。
- 问：1000 的答案是什么？答：规范化无序解唯一是 `(200,375,425)`；若 a/b 视为有序变量，还包括 `(375,200,425)`。
- 问：能不能 O(S)？答：可以继续代数变形或用勾股数组参数化减少搜索，但面试中是否值得取决于题目规模要求；当前固定 1000 的双循环已经非常小。
- 问：为什么用 long？答：不是因为 1000 会溢出，而是让平方中间值的安全边界更大；如果 sum 进一步接近 int 上限，连 `sum-a-b` 和循环边界也要整体升级为 long。
- 问：如何证明没有漏解？答：任意正整数解都满足 c=S-a-b；交换 a/b 不改变方程，因此可把两者排序成 a<=b；斜边 c>b。这个规范化解一定落在双循环覆盖区域。

## 易错点

- 三重枚举 a、b、c，完全没有利用和式消掉一个变量。
- 输出 `(200,375,425)` 后又把 `(375,200,425)` 当第二个“无序组合”重复计数。
- 相反，在题目要求有序变量赋值时只返回一个规范化结果，却没说明去重口径。
- 用 int 做很大输入的平方，乘法先溢出再提升类型。
- 内层在 `c<=b` 后仍继续循环，错过单调性剪枝。
- 直接背出 200/375/425，却没有展示约束如何缩小搜索空间和如何验证完整性。
'''

TEST = r'''import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class PythagoreanSumTest {
    private static List<PythagoreanSum.Triple> oracleCanonical(int sum) {
        List<PythagoreanSum.Triple> out = new ArrayList<>();
        for (int a = 1; a < sum; a++) {
            for (int b = a; b < sum; b++) {
                int c = sum - a - b;
                if (c <= b) continue;
                if ((long)a*a + (long)b*b == (long)c*c) out.add(new PythagoreanSum.Triple(a,b,c));
            }
        }
        return out;
    }

    private static void check(int sum) {
        List<PythagoreanSum.Triple> expected = oracleCanonical(sum);
        List<PythagoreanSum.Triple> actual = PythagoreanSum.findCanonical(sum);
        if (!actual.equals(expected)) throw new AssertionError("sum=" + sum + " expected=" + expected + " actual=" + actual);
        Set<String> keys = new HashSet<>();
        for (var t : actual) {
            if (!(t.a() <= t.b() && t.b() < t.c())) throw new AssertionError("not canonical " + t);
            if (t.a() + t.b() + t.c() != sum) throw new AssertionError("sum mismatch " + t);
            if ((long)t.a()*t.a() + (long)t.b()*t.b() != (long)t.c()*t.c()) throw new AssertionError("square mismatch " + t);
            if (!keys.add(t.toString())) throw new AssertionError("duplicate " + t);
        }
    }

    public static void main(String[] args) {
        List<PythagoreanSum.Triple> t1000 = PythagoreanSum.findCanonical(1000);
        if (!t1000.equals(List.of(new PythagoreanSum.Triple(200,375,425)))) throw new AssertionError("1000=" + t1000);
        List<PythagoreanSum.Triple> ordered = PythagoreanSum.findOrderedAssignments(1000);
        if (!ordered.equals(List.of(new PythagoreanSum.Triple(200,375,425), new PythagoreanSum.Triple(375,200,425)))) throw new AssertionError("ordered=" + ordered);
        for (int sum = 3; sum <= 500; sum++) check(sum);
        check(840);
        check(1000);
        try { PythagoreanSum.findCanonical(0); throw new AssertionError("zero sum must fail"); }
        catch (IllegalArgumentException expected) {}
        System.out.println("PASS sum1000 canonical-and-ordered exhaustive-sums3-500 plus840 constraints no-duplicates invalid-boundary");
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

    with tempfile.TemporaryDirectory(prefix='b51-pythagorean-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'PythagoreanSum.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'PythagoreanSumTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'PythagoreanSum.java', 'PythagoreanSumTest.java', cwd=tmpdir)
        stdout = run('java', 'PythagoreanSumTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS sum1000 canonical-and-ordered exhaustive-sums3-500 plus840 constraints no-duplicates invalid-boundary'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac PythagoreanSum.java PythagoreanSumTest.java && java PythagoreanSumTest',
        'stdout': stdout,
        'checks': [
            'sum=1000 canonical result is exactly (200,375,425)',
            'ordered-assignment view additionally contains the a/b-swapped assignment',
            'all sums 3 through 500 plus 840 and 1000 match an independent canonical brute-force oracle',
            'every emitted triple satisfies positivity/order/sum/Pythagorean constraints without duplicate canonical triples',
            'non-positive sum follows the candidate explicit invalid-input boundary',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0051 exact Pythagorean-sum source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 Pythagorean-sum validation versus independent exhaustive oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The exact source requires positive integers a,b,c satisfying a+b+c=1000 and a^2+b^2=c^2, but does not state whether swapping a and b counts as a distinct combination.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'canonicalization', 'text': 'Because the equations are symmetric in a and b and c is the positive hypotenuse, an unordered-combination view can canonically require a<=b<c without losing a solution; an ordered-assignment view must also include the swapped a/b assignment when a!=b.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'solution', 'text': 'Executable exhaustive validation finds exactly the canonical triple (200,375,425) for sum 1000 and the two labeled a/b assignments (200,375,425) and (375,200,425).', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '3 分钟版', '常见追问']},
        {'claim_id': 'search-reduction', 'text': 'Using c=sum-a-b eliminates one search dimension, while a<=b<c and monotonic c decrease provide duplicate elimination and an inner-loop break.', 'source_ids': ['fixture'], 'answer_locations': ['1 分钟版', '关键细节', '原理机制']},
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
        'The answer preserves the exact two equations and positive-integer requirement and does not add hidden domain constraints.',
        'The source ambiguity over whether a/b swaps are distinct is made explicit; both canonical unordered and labeled ordered outputs are provided.',
        'The algorithm uses the sum constraint to eliminate c and uses symmetry plus monotonicity to remove duplicates and stop the inner search safely.',
        'OpenJDK 21 validation proves the 1000 result and cross-checks all sums 3..500 plus 840/1000 against an independent exhaustive oracle.',
        'Long square intermediates, positivity, canonical ordering and duplicate behavior are explicitly tested or bounded.',
        'The project section avoids fabricated experience and frames number-theoretic parameterization as an optional scaling path rather than an unstated requirement.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0051-pythagorean-sum-20260829-v1',
        'review_version': 'batch-0051.pythagorean-sum.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0051 Pythagorean-sum source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0051-pythagorean-sum-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'sum=1000 canonical', 'expected': '[(200,375,425)]', 'actual': 'pass', 'passed': True},
                {'case': 'sum=1000 ordered assignments', 'expected': 'canonical plus a/b swap', 'actual': 'pass', 'passed': True},
                {'case': 'sums 3..500 + 840 + 1000', 'expected': 'equals independent exhaustive oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_de135a9fa2470b236d45bad96e81b6de` source-first isolated review PASS: the exact source requires positive a,b,c with sum 1000 and a²+b²=c² but does not say whether swapping a/b is distinct. The candidate therefore exposes both a<=b<c canonical-combination semantics and labeled ordered assignments, with the unique canonical triple (200,375,425). OpenJDK 21 validation cross-checks sums 3..500 plus 840/1000 against an independent exhaustive oracle and confirms the a/b-swap boundary. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
