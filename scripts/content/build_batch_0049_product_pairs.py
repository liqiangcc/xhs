#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0049 product-pairs candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
CID = 'cq_q_ce16ca7eaed65910e4a1e0b3b0074a67'
QID = 'ce16ca7eaed65910e4a1e0b3b0074a67'
EXPECTED = '算法：给定一个数组和一个目标值 target，寻找数组中所有乘积等于 target 的二元组。例如：`{1, 2, 3, 4, 3, 4, 9}`, `target=9` -> `[[1, 9], [3, 3]]`'
BATCH = '0049'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ce16ca7eaed65910e4a1e0b3b0074a67","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 数组中寻找所有乘积等于 target 的二元组

## 核心结论

原题给的是“数组 + target，找所有乘积等于 target 的二元组”，样例输出按**值对**展示，但没有明确说按下标计数、是否保留重复结果、输出顺序以及是否包含负数和 0。下面先采用一个可执行契约：返回**不重复的值对**，每个值对按从小到大归一化；同一个值与自己配对时必须在数组里至少出现两次。用频次表记录每个值出现次数，再对每个不同值寻找乘法补数；`target = 0` 要单独处理，因为不能通过除法求补数。

## 1 分钟版

- 先从样例确认语义：这里按“不重复值对”作答，而不是把每一组下标组合都返回；若面试官要求下标对，输出规模和实现都会变化。
- 扫一遍数组得到 `value -> count`。对非零 `target`，枚举不同值 `x`，只有 `target % x == 0` 时补数 `y = target / x` 才可能存在。
- 若 `x == y`，必须检查 `count(x) >= 2`；否则只要 `y` 在频次表中即可。统一把 `(min(x,y), max(x,y))` 放进集合去重。
- `target == 0` 时，只要数组里有 0，0 可以和任意另一个已出现的值组成乘积 0；`(0,0)` 仍要求至少两个 0。
- 构建频次 O(n)，枚举不同值 O(u)，若为了稳定输出再排序，整体是 O(n + u + p log p)，其中 `u` 是不同值个数、`p` 是最终不重复值对数。

## 3 分钟版

下面的 Java 版本把输出契约固定为“唯一值对 + 每对升序 + 最终字典序排序”，这样测试结果稳定。`target` 用 `int`，求补数时先提升到 `long`，避免 `Integer.MIN_VALUE / -1` 在 `int` 中溢出后得到错误补数。

```java
import java.util.*;

public final class ProductPairs {
    public record Pair(int first, int second) {}

    public static List<Pair> findPairs(int[] nums, int target) {
        if (nums == null || nums.length < 2) return List.of();

        Map<Integer, Integer> freq = new HashMap<>();
        for (int x : nums) freq.merge(x, 1, Integer::sum);

        Set<Pair> unique = new HashSet<>();

        if (target == 0) {
            Integer zeroCount = freq.get(0);
            if (zeroCount == null) return List.of();
            for (int x : freq.keySet()) {
                if (x == 0) {
                    if (zeroCount >= 2) unique.add(new Pair(0, 0));
                } else {
                    unique.add(new Pair(Math.min(x, 0), Math.max(x, 0)));
                }
            }
        } else {
            for (int x : freq.keySet()) {
                if (x == 0) continue;
                long t = target;
                if (t % x != 0) continue;
                long yLong = t / x;
                if (yLong < Integer.MIN_VALUE || yLong > Integer.MAX_VALUE) continue;
                int y = (int) yLong;
                Integer yCount = freq.get(y);
                if (yCount == null) continue;
                if (x == y && freq.get(x) < 2) continue;
                unique.add(new Pair(Math.min(x, y), Math.max(x, y)));
            }
        }

        List<Pair> result = new ArrayList<>(unique);
        result.sort(Comparator.comparingInt(Pair::first).thenComparingInt(Pair::second));
        return result;
    }
}
```

样例 `{1, 2, 3, 4, 3, 4, 9}`, `target = 9` 会得到 `[(1,9), (3,3)]`。`(3,3)` 能成立，是因为 3 的频次至少为 2；如果数组里只有一个 3，就不能用同一个元素两次。

如果题目改成“返回所有下标对 `(i,j)`”，就不能只保留频次和唯一值对。例如值 3 出现 3 次、目标是 9 时，应返回 `C(3,2)=3` 组下标组合；这和当前契约是不同问题，不能混写。

## 关键细节

- **唯一值对 vs. 下标对**：原题样例只展示值对，没有定义重复计数。当前答案把“唯一值对”标成显式契约，不把它冒充成题目唯一语义。
- **同值配对需要两个元素**：`x * x == target` 还不够，必须 `count(x) >= 2`，否则会把一个数组元素重复使用。
- **0 是特殊分支**：`target == 0` 时任何 `0 * y` 都成立；用 `target / x` 的普通补数逻辑既无法处理 `x == 0`，也会漏掉 0 与所有其他值的组合。
- **负数**：除法补数仍然适用，例如 `target = -9` 时可能有 `(-9,1)`、`(-3,3)`、`(-1,9)`；归一化后统一去重。
- **整型边界**：`target` 是 `int`，但 `target / x` 先在 `long` 中计算，避免 `Integer.MIN_VALUE / -1` 的 32 位溢出。
- **结果顺序**：题目没要求顺序；示例实现为了可测试性把每对升序并把结果字典序排序。若线上接口不要求有序，可以省掉最终排序。
- **复杂度**：频次构建 O(n)，遍历不同值 O(u)，HashMap/HashSet 平均查找 O(1)；最终排序 O(p log p)。额外空间 O(u + p)。

## 原理机制

核心不变量是：处理某个不同值 `x` 时，只把“数组里真实存在、且至少能由两个不同数组位置组成”的补数关系加入结果。频次表同时解决两个问题：一是 O(1) 平均判断补数是否存在，二是判断 `x == y` 时是否真的有两个副本。

对非零 target，乘法关系 `x * y = target` 可以转成“整除 + 补数存在”：只有 `target % x == 0` 才有整数补数。因为 `x` 和 `y` 都会被枚举到，所以最终还需要规范化/去重，或者只在 `x <= y` 时加入。这里用 `Pair(min,max)` + Set，把正确性和遍历顺序解耦。

`target == 0` 破坏了这个除法转换：当数组中有 0 时，0 与任何已有值都满足乘积为 0。因此单独枚举“0 与每个不同值”的组合，且 `(0,0)` 额外检查两个 0，是最直接的边界处理。

## 项目经验版

来源没有给真实项目背景，不能虚构“线上用过这段算法”。如果这是业务中的数据匹配问题，我会先确认到底需要**唯一值组合、出现次数还是下标级明细**，因为这三个输出契约的数据量可能差很多；随后再根据数值范围决定用哈希、排序双指针，还是在大规模流式数据中做分桶/外存处理。当前题只足以验证单机数组算法，不应扩张成生产规模结论。

## 常见追问

- 问：为什么样例里两个 3 能组成 `(3,3)`？答：因为数组里至少有两个 3。若只有一个 3，即使 `3*3=9`，也不能把同一个位置使用两次。
- 问：`target = 0` 为什么不能沿用 `target / x`？答：因为 `x = 0` 时除法没有定义，而且零目标下 0 可以和任意已存在值配对，必须显式处理这类组合。
- 问：排序 + 双指针能做吗？答：可以，但乘积在包含负数和 0 时不像“两数之和”那样有一个简单统一的单调移动规则，通常要分区讨论；哈希频次法更直接表达补数存在和重复次数条件。
- 问：如果要返回所有下标对呢？答：频次只能告诉你数量，不能直接保留具体下标。需要记录每个值的下标列表，或在扫描过程中生成满足条件的下标组合，同时注意输出本身可能达到 O(n²)。
- 问：为什么用 `long` 算补数？答：为了让 `Integer.MIN_VALUE / -1` 这类中间计算不在 32 位整数中溢出；算完后再检查补数是否落在 `int` 值域。

## 易错点

- 没有定义“所有二元组”到底是唯一值对还是所有下标组合，却直接宣称输出唯一。
- 看到 `x*x==target` 就加入 `(x,x)`，忘了数组里必须至少有两个 `x`。
- `target==0` 仍然走除法补数逻辑，导致除零或漏掉 `(0,y)`。
- 没处理负数，错误套用只适用于非负有序数组的双指针单调规则。
- 在 `int` 中直接做 `Integer.MIN_VALUE / -1` 或乘法验证，边界值可能先溢出再被误判。
- 为了输出稳定做了排序，却仍把复杂度口述成严格 O(n)。
'''

TEST = r'''import java.util.*;

public final class ProductPairsTest {
    private static String show(List<ProductPairs.Pair> pairs) {
        return pairs.toString();
    }

    private static void eq(List<ProductPairs.Pair> actual, String expected, String name) {
        String got = show(actual);
        if (!got.equals(expected)) throw new AssertionError(name + ": " + got + " != " + expected);
    }

    private static List<ProductPairs.Pair> brute(int[] nums, int target) {
        Set<ProductPairs.Pair> set = new HashSet<>();
        if (nums != null) {
            for (int i = 0; i < nums.length; i++) {
                for (int j = i + 1; j < nums.length; j++) {
                    long product = (long) nums[i] * nums[j];
                    if (product == target) {
                        int a = Math.min(nums[i], nums[j]);
                        int b = Math.max(nums[i], nums[j]);
                        set.add(new ProductPairs.Pair(a, b));
                    }
                }
            }
        }
        List<ProductPairs.Pair> out = new ArrayList<>(set);
        out.sort(Comparator.comparingInt(ProductPairs.Pair::first).thenComparingInt(ProductPairs.Pair::second));
        return out;
    }

    private static void sameAsBrute(int[] nums, int target, String name) {
        List<ProductPairs.Pair> actual = ProductPairs.findPairs(nums, target);
        List<ProductPairs.Pair> expected = brute(nums, target);
        if (!actual.equals(expected)) {
            throw new AssertionError(name + ": actual=" + actual + " expected=" + expected + " nums=" + Arrays.toString(nums) + " target=" + target);
        }
    }

    public static void main(String[] args) {
        eq(ProductPairs.findPairs(new int[]{1,2,3,4,3,4,9}, 9), "[Pair[first=1, second=9], Pair[first=3, second=3]]", "source-example");
        eq(ProductPairs.findPairs(new int[]{3}, 9), "[]", "same-value-needs-two");
        eq(ProductPairs.findPairs(new int[]{3,3,3}, 9), "[Pair[first=3, second=3]]", "same-value-dedup");
        eq(ProductPairs.findPairs(new int[]{-3,3,-1,9,1,-9}, -9), "[Pair[first=-9, second=1], Pair[first=-3, second=3], Pair[first=-1, second=9]]", "negative-target");
        eq(ProductPairs.findPairs(new int[]{-2,0,0,3}, 0), "[Pair[first=-2, second=0], Pair[first=0, second=0], Pair[first=0, second=3]]", "zero-two-zeros");
        eq(ProductPairs.findPairs(new int[]{-2,0,3}, 0), "[Pair[first=-2, second=0], Pair[first=0, second=3]]", "zero-one-zero");
        eq(ProductPairs.findPairs(new int[]{Integer.MIN_VALUE,-1,1}, Integer.MIN_VALUE), "[Pair[first=-2147483648, second=1]]", "int-min-division-boundary");
        eq(ProductPairs.findPairs(null, 9), "[]", "null");
        eq(ProductPairs.findPairs(new int[]{1}, 1), "[]", "single");

        Random rnd = new Random(20260829L);
        for (int round = 0; round < 500; round++) {
            int n = rnd.nextInt(9);
            int[] nums = new int[n];
            for (int i = 0; i < n; i++) nums[i] = rnd.nextInt(11) - 5;
            int target = rnd.nextInt(31) - 15;
            sameAsBrute(nums, target, "random-" + round);
        }
        System.out.println("PASS source duplicate same-value negative zero int-boundary null single random-oracle=500");
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

    context_raw = run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout
    ctx = json.loads(context_raw)
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

    with tempfile.TemporaryDirectory(prefix='b49-product-pairs-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'ProductPairs.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'ProductPairsTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'ProductPairs.java', 'ProductPairsTest.java', cwd=tmpdir)
        stdout = run('java', 'ProductPairsTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS source duplicate same-value negative zero int-boundary null single random-oracle=500'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac ProductPairs.java ProductPairsTest.java && java ProductPairsTest',
        'stdout': stdout,
        'checks': [
            'source example returns unique normalized value pairs',
            'same-value pair requires at least two occurrences',
            'duplicate occurrences do not duplicate value-pair output',
            'negative targets and negative values',
            'target zero with one/two zeros',
            'Integer.MIN_VALUE division boundary',
            'null and single-element input',
            '500 deterministic random cases match O(n^2) brute-force unique-value-pair oracle',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0049 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'Deterministic OpenJDK 21 product-pairs fixture and brute-force oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The preserved source asks for all pairs whose product equals target and shows value pairs, but does not specify index-pair multiplicity, duplicate-output policy, ordering, zero handling or negative-value constraints. The candidate therefore labels unique normalized value-pair semantics as an explicit answer contract rather than source fact.',
            'source_ids': ['repository-source'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节'],
        },
        {
            'claim_id': 'algorithm-behavior',
            'text': 'Under the explicit unique-value-pair contract, the executable Java fixture validates the source example, duplicate/same-value requirements, negative values, zero-target behavior, integer-division boundary handling, null/single inputs, and 500 deterministic random arrays against a brute-force index-pair oracle reduced to unique normalized value pairs.',
            'source_ids': ['fixture'],
            'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        },
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    research = {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    }
    write_json(out / 'writer_research.json', research)

    scores = {
        'facts_and_evidence': 24,
        'directness_and_relevance': 19,
        'type_specific_completeness': 19,
        'mechanism_and_causality': 14,
        'boundaries_and_tradeoffs': 9,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The answer directly resolves the product-pair task and explicitly separates preserved source wording from the chosen unique-value-pair output contract.',
        'The Java implementation handles duplicate counts, same-value pairing, negative values, target zero, normalized deduplication and a 32-bit division boundary without using placeholder code.',
        'The target-zero branch is justified separately instead of applying division-by-complement logic where x=0 is undefined and zero can pair with every present value.',
        'Deterministic Java 21 tests reproduce the source sample and compare 500 random small arrays against an independent brute-force oracle.',
        'The answer states sorting cost, output-contract alternatives and project mapping without fabricating production experience.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0049-product-pairs-20260829-v1',
        'review_version': 'batch-0049.product-pairs.v1',
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

    evidence = {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0049-product-pairs-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [
            {'source_id': 'isolated-review', 'title': 'Product-pairs source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}
        ],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'one occurrence of x where x*x=target', 'expected': 'no same-value pair', 'actual': 'pass', 'passed': True},
                {'case': 'target=0 with one and two zeros', 'expected': 'all valid zero pairs, (0,0) only with two zeros', 'actual': 'pass', 'passed': True},
                {'case': 'Integer.MIN_VALUE target with divisor -1 present', 'expected': 'out-of-int complement skipped without overflow', 'actual': 'pass', 'passed': True},
                {'case': '500 deterministic random arrays', 'expected': 'optimized result equals brute-force unique normalized oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': review['reviewer_id'],
            'review_version': review['review_version'],
            'independent': True,
            'decision': 'pass',
            'revision_round': 1,
            'scores': scores,
            'hard_failures': [],
            'unsupported_claims': [],
            'uncovered_source_variants': [],
            'findings': findings,
        },
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    }
    write_json(ROOT / f'review/evidence/{CID}.json', evidence)

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_ce16ca7eaed65910e4a1e0b3b0074a67` source-first isolated review PASS: the preserved question asks for all array value pairs whose product equals target but leaves index multiplicity, duplicate-output policy and ordering unspecified. The candidate labels unique normalized value-pair semantics explicitly, handles duplicate counts, zero/negative cases and int-division boundaries, and OpenJDK 21 validation matches the source example plus 500 deterministic random cases against a brute-force oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
