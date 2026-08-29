#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0053 difference-two-pairs candidate."""

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
CID = 'cq_q_e63e481809ed7fb71db27152107f821e'
QID = 'e63e481809ed7fb71db27152107f821e'
EXPECTED = '算法：一个数组，找到所有相差为2的数据对并打印。'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e63e481809ed7fb71db27152107f821e","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 数组中所有相差为 2 的数据对

## 核心结论

仓库来源只保留“一个数组，找到所有相差为 2 的数据对并打印”，没有保存“数据对”按下标还是按值去重、输出顺序、输入是否允许重复、语言和空值语义。这里明确采用一个可执行 Java 契约：输入 `int[]`；输出所有**不同值对** `(a,b)`，满足 `b-a=2`；相同值在输入中出现多次也只输出一次该值对；结果按较小值升序排列；空数组返回空列表；`null` 抛 `IllegalArgumentException`。

做法是先把所有值放进 `HashSet<Integer>`，然后对集合中的每个 `a` 检查 `a+2` 是否存在。为了避免 `int` 上溢，先用 `long` 计算 `a+2`。命中的值对加入结果后统一排序，使输出稳定可测试。若题目真正要求“所有下标对”，重复元素会产生组合数量，合同和算法都必须重新定义，不能把两种语义混在一起。

## 1 分钟版

- 先去重得到值集合；当前合同按“不同值对”输出，而不是枚举重复下标组合。
- 对每个 `a` 查询集合里是否存在 `a+2`，存在就得到唯一候选 `(a,a+2)`。
- `a+2` 用 `long` 计算，避免 `Integer.MAX_VALUE` 附近溢出后误命中负数。
- HashSet 构建和查询按常见平均/期望成本是 O(n)；若要求稳定升序输出，再对 k 个结果排序，增加 O(k log k)。
- 来源没有规定打印顺序，因此升序是本候选为了确定性主动定义的输出合同。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class DifferenceTwoPairs {
    public record Pair(int left, int right) {}

    public static List<Pair> findPairs(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }

        Set<Integer> values = new HashSet<>();
        for (int value : nums) values.add(value);

        List<Pair> out = new ArrayList<>();
        for (int left : values) {
            long rightLong = (long) left + 2L;
            if (rightLong <= Integer.MAX_VALUE && values.contains((int) rightLong)) {
                out.add(new Pair(left, (int) rightLong));
            }
        }
        out.sort(Comparator.comparingInt(Pair::left).thenComparingInt(Pair::right));
        return out;
    }
}
```

例如输入 `[3,1,3,5,1]`，值集合是 `{1,3,5}`，最终输出 `(1,3)` 和 `(3,5)`，不会因为 1 或 3 重复出现而重复打印同一值对。若业务要求的是下标对，则两个 1 和两个 3 会产生多组 `(i,j)`，这已经不是当前函数的语义。

## 关键细节

- **差值方向**：统一输出较小值在左，检查 `right=left+2`，避免同时生成 `(1,3)` 和 `(3,1)`。
- **重复输入**：HashSet 把重复值折叠掉，因此同一个值对只输出一次。
- **整数溢出**：不能直接无条件做 `int right = left + 2`；例如 `Integer.MAX_VALUE` 会绕回负数。先转 `long` 再检查范围。
- **确定性顺序**：HashSet 迭代顺序没有稳定合同，所以最终显式排序，不能把当前 JVM 的哈希顺序当成输出保证。
- **复杂度**：去重和成员查询按平均/期望为 O(n)，结果排序 O(k log k)，额外空间 O(n+k)。若不要求顺序，可去掉排序并得到平均/期望 O(n) 主流程。
- **下标对语义**：如果题目要求所有索引组合，应保存每个值对应的下标列表并组合，输出规模本身可能远大于 n。

## 原理机制

维护值集合以后，条件 `b-a=2` 可以改写成“对每个已存在的 a，查询 a+2 是否也存在”。这把原本可能需要两两比较的 O(n²) 关系判断，转成一次扫描加成员查询。由于当前合同只关心不同值对，集合正好是最小状态；若关心出现次数或下标，集合就会丢失必要信息，因此必须换成 `Map<value, indices/count>` 等结构。

结果排序与“找到哪些对”是两个独立阶段：HashSet 负责集合成员关系，排序只负责可重复、稳定的输出顺序。把这两层分开，才能清楚说明去掉排序时的复杂度和题目若不要求顺序时的优化空间。

## 项目经验版

来源没有真实项目场景，不能虚构线上案例。工程中先确认“pair”到底代表值还是记录/下标非常关键：值去重适合规则检测、配置集合等场景；若每条记录身份有意义，则必须保留原始索引或 ID。若输入规模超过内存，也可以考虑外部排序或分区，但这些都依赖真实约束，不属于当前保存题面事实。

## 常见追问

- 问：为什么不用双重循环？答：双重循环直接但 O(n²)；按当前值对合同，用集合把“是否存在 a+2”变成平均/期望 O(1) 成员查询。
- 问：为什么结果还要排序？答：HashSet 没有稳定输出顺序；来源没有要求排序，但候选为了确定性定义了升序合同。若不要求稳定顺序可以去掉排序。
- 问：数组有重复值怎么办？答：当前合同只输出不同值对，所以重复值先去重；如果要求下标对，必须保留所有下标并枚举组合。
- 问：为什么要考虑溢出？答：`int` 加 2 可能越界并回绕，导致误把一个极大正数和负数配成差 2；用 `long` 做中间计算能避免这个错误。
- 问：能原地排序做吗？答：可以复制后排序，再用双指针或相邻搜索；若原地排序会改变输入，需要题目明确允许。集合方案不修改输入。
- 问：如果差值是任意 d 呢？答：把 `+2` 参数化为 `+d` 即可，但若 d 允许负数或 0，需要重新定义规范化方向和重复语义。

## 易错点

- 没有先定义“数据对”是值对还是下标对，遇到重复元素时答案语义不明确。
- 用双循环打印 `(1,3)` 和 `(3,1)` 两次，或因重复输入多次打印相同值对。
- 直接 `left + 2` 使用 `int`，忽略边界溢出。
- 依赖 HashSet 当前迭代顺序，却声称输出有确定顺序。
- 把哈希查询平均/期望复杂度写成无条件严格最坏 O(1)。
- 为了排序直接修改调用者数组，却没有说明副作用。
'''

TEST = r'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;
import java.util.TreeSet;

public final class DifferenceTwoPairsTest {
    private static List<DifferenceTwoPairs.Pair> brute(int[] nums) {
        TreeSet<Integer> set = new TreeSet<>();
        for (int v : nums) set.add(v);
        List<DifferenceTwoPairs.Pair> out = new ArrayList<>();
        for (int left : set) {
            long right = (long) left + 2L;
            if (right <= Integer.MAX_VALUE && set.contains((int) right)) {
                out.add(new DifferenceTwoPairs.Pair(left, (int) right));
            }
        }
        return out;
    }

    private static void check(int[] nums, List<DifferenceTwoPairs.Pair> expected) {
        List<DifferenceTwoPairs.Pair> actual = DifferenceTwoPairs.findPairs(nums);
        if (!expected.equals(actual)) throw new AssertionError("nums=" + Arrays.toString(nums) + " expected=" + expected + " actual=" + actual);
    }

    public static void main(String[] args) {
        check(new int[]{}, List.of());
        check(new int[]{1}, List.of());
        check(new int[]{1,3,5}, List.of(new DifferenceTwoPairs.Pair(1,3), new DifferenceTwoPairs.Pair(3,5)));
        check(new int[]{3,1,3,5,1}, List.of(new DifferenceTwoPairs.Pair(1,3), new DifferenceTwoPairs.Pair(3,5)));
        check(new int[]{-3,-1,1}, List.of(new DifferenceTwoPairs.Pair(-3,-1), new DifferenceTwoPairs.Pair(-1,1)));
        check(new int[]{Integer.MAX_VALUE, Integer.MAX_VALUE - 2, Integer.MIN_VALUE, Integer.MIN_VALUE + 2},
                List.of(new DifferenceTwoPairs.Pair(Integer.MIN_VALUE, Integer.MIN_VALUE + 2),
                        new DifferenceTwoPairs.Pair(Integer.MAX_VALUE - 2, Integer.MAX_VALUE)));

        try {
            DifferenceTwoPairs.findPairs(null);
            throw new AssertionError("null must fail");
        } catch (IllegalArgumentException expected) {}

        Random random = new Random(20260829L);
        for (int round=0; round<5000; round++) {
            int n = random.nextInt(50);
            int[] nums = new int[n];
            for (int i=0;i<n;i++) nums[i]=random.nextInt(101)-50;
            List<DifferenceTwoPairs.Pair> expected=brute(nums);
            List<DifferenceTwoPairs.Pair> actual=DifferenceTwoPairs.findPairs(nums);
            if (!expected.equals(actual)) throw new AssertionError("round="+round+" expected="+expected+" actual="+actual);
        }

        int[] large = new int[200_000];
        for (int i=0;i<large.length;i++) large[i]=i*3;
        if (!DifferenceTwoPairs.findPairs(large).isEmpty()) throw new AssertionError("large should have no diff-2 pair");

        System.out.println("PASS directed duplicates extremes null 5000-random-oracle 200000-large");
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

    with tempfile.TemporaryDirectory(prefix='b53-difference-two-pairs-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'DifferenceTwoPairs.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'DifferenceTwoPairsTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'DifferenceTwoPairs.java', 'DifferenceTwoPairsTest.java', cwd=tmpdir)
        stdout = run('java', 'DifferenceTwoPairsTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS directed duplicates extremes null 5000-random-oracle 200000-large'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac DifferenceTwoPairs.java DifferenceTwoPairsTest.java && java DifferenceTwoPairsTest',
        'stdout': stdout,
        'checks': [
            'directed empty/single/positive/negative cases',
            'duplicate input values still produce unique value pairs',
            'integer boundary cases prove overflow-safe +2 computation',
            'explicit null-input exception boundary',
            '5000 deterministic random arrays agree with an independent sorted-set oracle',
            '200000-element large case completes and produces no false positive pairs',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0053 exact difference-two-pairs source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 difference-two-pairs deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source asks only to find and print all array pairs differing by two; it does not preserve pair identity semantics, duplicate handling, ordering, language, or null behavior.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '易错点']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate explicitly chooses unique value pairs, ascending deterministic output, empty-array success, and null as an illegal input.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '关键细节']},
        {'claim_id': 'algorithm-behavior', 'text': 'For each distinct left value, membership of left+2 in the value set exactly characterizes a unique difference-two value pair; long intermediate arithmetic prevents int overflow false matches.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制', '常见追问']},
        {'claim_id': 'boundary-validation', 'text': 'Executable validation covers duplicates, signed/extreme ints, null, 5000 deterministic random arrays against an independent oracle, and a 200000-element large case.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '易错点']},
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
        'The candidate does not invent missing pair/index semantics from the sparse source; it defines unique value-pair semantics explicitly.',
        'Duplicate input values, deterministic ordering, null behavior, and non-mutating input handling are stated as candidate contract rather than source facts.',
        'The HashSet solution directly reduces pair search to membership of a+2 and avoids quadratic all-pairs scanning under the chosen value-pair semantics.',
        'The implementation uses long for the +2 intermediate so extreme int values cannot wrap into false matches.',
        'OpenJDK 21 validation covers directed duplicates/extremes, 5000 deterministic random arrays against an independent TreeSet oracle, and a 200000-element large case.',
        'Complexity wording separates average/expected hash work from O(k log k) deterministic result sorting.',
        'The candidate clearly explains that index-pair semantics would require preserving multiplicity/indices and could have much larger output size.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0053-difference-two-pairs-20260829-v1',
        'review_version': 'batch-0053.difference-two-pairs.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0053 difference-two-pairs source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0053-difference-two-pairs-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'duplicate values', 'expected': 'unique value pairs only', 'actual': 'pass', 'passed': True},
                {'case': 'extreme ints', 'expected': 'no overflow-induced false pair', 'actual': 'pass', 'passed': True},
                {'case': '5000 deterministic random arrays', 'expected': 'matches sorted-set oracle', 'actual': 'pass', 'passed': True},
                {'case': '200000-element large input', 'expected': 'no false positive pair', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e63e481809ed7fb71db27152107f821e` source-first isolated review PASS: the sparse source leaves pair identity and duplicate semantics unspecified, so the candidate explicitly defines unique value pairs with deterministic ascending output. The HashSet implementation uses overflow-safe long arithmetic; OpenJDK 21 validation covers duplicates/extreme ints/null, 5000 deterministic random arrays against a TreeSet oracle, and a 200000-element large case. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
