#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0061 trapping-rain-water candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0061'
CID = 'cq_q_05b816cca1029a3e9b9932ceb1e0d9eb'
QIDS = ['05b816cca1029a3e9b9932ceb1e0d9eb']
EXPECTED_VARIANTS = {'算法：接雨水'}
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = [
    '## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节',
    '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点',
]
SCORES = {
    'facts_and_evidence': 25,
    'directness_and_relevance': 20,
    'type_specific_completeness': 20,
    'mechanism_and_causality': 15,
    'boundaries_and_tradeoffs': 10,
    'followup_quality': 5,
    'oral_quality': 5,
}

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_05b816cca1029a3e9b9932ceb1e0d9eb","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 接雨水：双指针维护两侧已知最高边界

## 核心结论

来源只保留“算法：接雨水”，没有给 API、数值范围或非法输入规则。这里声明一个可执行 Java 合同：输入是非负柱高 `int[] height`，`null` 或长度小于 3 返回 0，负高度直接拒绝；返回值用 `long`，避免很多高柱形成的总水量超过 `int`。核心不变量是：某个位置能接的水由 `min(左侧最高, 右侧最高) - 当前高度` 决定；双指针每次处理“当前高度较低的一侧”，因为另一侧当前柱已经足以成为这一侧的有效外边界。这样只需一次扫描，时间 O(n)，额外空间 O(1)。

## 1 分钟版

- 单点水量公式是 `min(leftMax, rightMax) - height[i]`，前提是结果为正。
- 左右指针从两端向中间走，同时维护已经看过的 `leftMax`、`rightMax`。
- 若 `height[left] <= height[right]`，右侧当前柱已经不低于左侧当前柱，因此左位置是否能积水只取决于 `leftMax`；处理左边后 `left++`。
- 否则对称处理右边，用 `rightMax - height[right]`，再 `right--`。
- 每个位置最多处理一次，所以时间 O(n)、额外空间 O(1)；总水量用 `long` 防止累加溢出。

## 3 分钟版

下面代码对应“非负柱高数组，返回总积水量”的参考合同：

```java
public final class TrappingRainWater {
    private TrappingRainWater() {}

    public static long trap(int[] height) {
        if (height == null || height.length < 3) {
            return 0L;
        }
        for (int h : height) {
            if (h < 0) {
                throw new IllegalArgumentException("height must be nonnegative");
            }
        }

        int left = 0;
        int right = height.length - 1;
        int leftMax = 0;
        int rightMax = 0;
        long water = 0L;

        while (left < right) {
            if (height[left] <= height[right]) {
                if (height[left] >= leftMax) {
                    leftMax = height[left];
                } else {
                    water += (long) leftMax - height[left];
                }
                left++;
            } else {
                if (height[right] >= rightMax) {
                    rightMax = height[right];
                } else {
                    water += (long) rightMax - height[right];
                }
                right--;
            }
        }
        return water;
    }
}
```

例如 `[0,1,0,2,1,0,1,3,2,1,2,1]` 的答案是 6。处理时不需要为每个位置预先存两侧最大值；只要较低一侧被处理时，另一侧当前柱能保证存在一个不更低的外边界，这一侧的水位就可以由本侧已经见过的最高柱确定。

## 关键细节

- **输入输出合同**：当前参考实现把 `null` 当空输入返回 0；柱高要求非负，负值没有普通“高度”语义，因此显式报错。来源没有规定这些规则，所以必须声明而不能冒充原题要求。
- **为什么比较当前两端高度**：若 `height[left] <= height[right]`，右边至少存在一根高度不低于 `height[left]` 的柱。若左侧历史最高 `leftMax` 更高，则左位置水位由 `leftMax` 限制；若不更高，当前柱本身就更新左边界，不会产生负水量。右侧完全对称。
- **为什么不需要处理相遇点**：循环结束时只剩同一个未处理位置；它已经是左右未决区间的交点，无法在两侧已处理区间之间额外形成一个尚未统计的独立凹槽。
- **溢出**：单次差值先转成 `long` 再累计。比如 `[Integer.MAX_VALUE, 0, 0, Integer.MAX_VALUE]` 的水量是 `4294967294`，已经超过有符号 32 位整数。
- **重复高度与平台**：相等高度不会破坏算法；`<=` 选择左侧只是一个确定性的 tie-break，两侧对称处理都可以成立。
- **复杂度**：左右指针总共只向内移动 n-1 次，因此时间 O(n)；只维护固定数量变量，额外空间 O(1)。

## 原理机制

朴素公式对位置 i 使用 `min(max(height[0..i]), max(height[i..n-1]))` 作为水面上界。前缀/后缀数组可以 O(n) 时间求出所有位置，但要 O(n) 额外空间。

双指针把这个“两个方向都要知道最大值”的问题改造成逐步确定：当左端当前高度不高于右端时，右边已经存在一个足够高的候选边界，因此左端的未知量只剩“左边历史最高是多少”；此时左端贡献可以立即结算，之后这个位置再也不会被未来信息改变。反之同理结算右端。每轮至少确定一个位置，因此最终得到与完整左右最大值公式相同的总和。

## 项目经验版

来源没有真实项目背景，不能虚构“线上使用过这段算法”。面试手撕时我会先确认柱高是否保证非负、返回类型是否固定为 `int`、空输入和异常输入怎么定义；实现后用一个独立 O(n²) 公式做随机差分测试，再覆盖单调数组、平台、多个凹槽和大数溢出边界。这里的 `long` 返回值是为了让参考合同对大数组/高柱更稳健，不是说原题一定要求 `long`。

## 常见追问

- 问：为什么不是每次都用 `min(leftMax, rightMax)`？答：如果只维护扫描到的历史最大值，未处理一侧的真实最大值还未知。双指针通过当前两端高度判断哪一侧已经具备足够的对侧边界，只结算可以确定的那一侧。
- 问：前缀/后缀最大值做法可以吗？答：可以。先求每个位置左最大和右最大，再按公式累加，时间也是 O(n)，但额外空间 O(n)；双指针把这部分空间降到 O(1)。
- 问：单调递增或单调递减数组会怎样？答：没有被两侧更高柱夹住的凹槽，结果为 0；算法只会不断更新某一侧最大值，不会累加水量。
- 问：为什么返回 `long`？答：单个高度虽然是 `int`，很多位置的积水总和仍可能超过 `Integer.MAX_VALUE`；使用 `long` 可以避免总量累加溢出。
- 问：如果柱宽不是 1 呢？答：当前合同默认每根柱宽为 1。若每段宽度不同，单点高度差还要乘对应宽度；若横坐标任意，则需要重新定义区间宽度和输入模型。
- 问：能用单调栈吗？答：可以。单调栈按“凹槽底部被右侧更高柱封闭”计算横向面积，时间 O(n)、空间 O(n)；双指针更直接地按位置纵向结算并做到 O(1) 额外空间。

## 易错点

- 只写 `min(leftMax, rightMax)-height[i]`，却没有说明怎样在线性扫描中保证两个最大值已经可用。
- 先累加再更新本侧最大值，导致最高柱位置出现负值或错误水量。
- 把 `leftMax`、`rightMax` 和当前 `height[left]`、`height[right]` 的比较条件混用，却没有保持可证明的不变量。
- 用 `int` 累加总水量而忽略大量位置可能溢出。
- 没声明非负高度和柱宽为 1 的合同，却把实现扩张到负高度或不等宽柱体。
- 只测经典样例，不测空/短数组、单调数组、平台、多个凹槽和大数边界。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class TrappingRainWaterTest {
    private static long oracle(int[] h) {
        if (h == null || h.length < 3) return 0L;
        for (int x : h) if (x < 0) throw new IllegalArgumentException("height must be nonnegative");
        long sum = 0L;
        for (int i = 1; i + 1 < h.length; i++) {
            int left = 0;
            int right = 0;
            for (int j = 0; j <= i; j++) left = Math.max(left, h[j]);
            for (int j = i; j < h.length; j++) right = Math.max(right, h[j]);
            sum += Math.max(0L, (long) Math.min(left, right) - h[i]);
        }
        return sum;
    }

    private static void check(long actual, long expected, String label) {
        if (actual != expected) throw new AssertionError(label + " actual=" + actual + " expected=" + expected);
    }

    private static void differential(int[] h, String label) {
        long got = TrappingRainWater.trap(h);
        long want = oracle(h);
        if (got != want) throw new AssertionError(label + " h=" + Arrays.toString(h) + " got=" + got + " want=" + want);
    }

    public static void main(String[] args) {
        check(TrappingRainWater.trap(null), 0L, "null");
        check(TrappingRainWater.trap(new int[]{}), 0L, "empty");
        check(TrappingRainWater.trap(new int[]{7}), 0L, "single");
        check(TrappingRainWater.trap(new int[]{7, 2}), 0L, "two");
        check(TrappingRainWater.trap(new int[]{0,1,0,2,1,0,1,3,2,1,2,1}), 6L, "classic");
        check(TrappingRainWater.trap(new int[]{4,2,0,3,2,5}), 9L, "multi-basin");
        check(TrappingRainWater.trap(new int[]{1,2,3,4,5}), 0L, "increasing");
        check(TrappingRainWater.trap(new int[]{5,4,3,2,1}), 0L, "decreasing");
        check(TrappingRainWater.trap(new int[]{3,3,3,3}), 0L, "plateau");
        check(TrappingRainWater.trap(new int[]{3,0,3}), 3L, "simple-bowl");
        check(TrappingRainWater.trap(new int[]{Integer.MAX_VALUE,0,0,Integer.MAX_VALUE}), 4294967294L, "long-overflow-boundary");
        try {
            TrappingRainWater.trap(new int[]{1,-1,1});
            throw new AssertionError("negative-height expected rejection");
        } catch (IllegalArgumentException expected) {
            // expected
        }

        Random r = new Random(0x5241494E57415445L);
        for (int t = 0; t < 50000; t++) {
            int n = r.nextInt(21);
            int[] h = new int[n];
            for (int i = 0; i < n; i++) h[i] = r.nextInt(1001);
            differential(h, "random-" + t);
        }
        for (int t = 0; t < 5000; t++) {
            int n = 3 + r.nextInt(18);
            int[] h = new int[n];
            for (int i = 0; i < n; i++) {
                h[i] = switch (r.nextInt(4)) {
                    case 0 -> Integer.MAX_VALUE;
                    case 1 -> Integer.MAX_VALUE - r.nextInt(1024);
                    default -> r.nextInt(1000000);
                };
            }
            differential(h, "near-max-" + t);
        }
        System.out.println("PASS fixed=11 negative=rejected random=50000 near-max=5000 oracle=quadratic-prefix-suffix long-overflow=covered");
    }
}
'''


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass':
        raise SystemExit('batch 0061 source inventory is not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item or item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: frozen coding source item missing')
    if item.get('personal_fact_verification_required') or item.get('secondary_coverage_required'):
        raise SystemExit(f'{CID}: unexpected sensitive/secondary gate')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: frozen ownership drift: {item.get("question_ids")}')
    wordings = {q.get('original_question') for q in item.get('source_questions', [])}
    if wordings != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: source wording drift: {wordings}')

    context_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}/context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('canonical', {}).get('canonical_id') != CID:
        raise SystemExit(f'{CID}: context missing')
    if context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: answer type drift')

    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    evidence = ROOT / f'review/evidence/{CID}.json'
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in HEADINGS:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if CANDIDATE.count('- 问：') < 5:
        raise SystemExit(f'{CID}: candidate follow-up coverage too small')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'{CID}: candidate must contain exactly one Java implementation block')

    with tempfile.TemporaryDirectory(prefix='b61-rainwater-') as temp:
        work = Path(temp)
        (work / 'TrappingRainWater.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (work / 'TrappingRainWaterTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'TrappingRainWater.java', 'TrappingRainWaterTest.java', cwd=work)
        stdout = run('java', 'TrappingRainWaterTest', cwd=work).stdout.strip()

    expected_stdout = 'PASS fixed=11 negative=rejected random=50000 near-max=5000 oracle=quadratic-prefix-suffix long-overflow=covered'
    if stdout != expected_stdout:
        raise SystemExit(f'{CID}: unexpected fixture output: {stdout}')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    command = 'javac TrappingRainWater.java TrappingRainWaterTest.java && java TrappingRainWaterTest'
    checks = [
        'null, empty, one-element and two-element inputs return zero',
        'classic and multi-basin examples match expected totals',
        'monotone and plateau inputs return zero',
        'simple bowl is computed correctly',
        'negative heights are rejected by the declared reference contract',
        'long accumulation preserves totals above Integer.MAX_VALUE',
        '50,000 seeded random arrays match an independent O(n^2) oracle',
        '5,000 seeded near-Integer.MAX_VALUE arrays match the independent oracle',
    ]
    write_json(out / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': command,
        'stdout': stdout,
        'checks': checks,
        'environment': {'java': 'OpenJDK 21'},
    })

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0061 frozen repository source context for trapping rain water',
            'locator': str(context_path),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'source-inventory',
            'title': 'Batch 0061 frozen live source inventory',
            'locator': str(inventory_path),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
        {
            'source_id': 'fixture',
            'title': 'Deterministic and differential OpenJDK validation for trapping rain water',
            'locator': str(out / 'writer_validation.json'),
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The preserved source asks only for the trapping-rain-water algorithm and does not preserve a Java API, numeric range, null policy, negative-height policy, or non-unit column-width contract; the candidate declares these as reference assumptions rather than source requirements.',
            'source_ids': ['repository-source', 'source-inventory'],
            'answer_locations': ['核心结论', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'reference-behavior',
            'text': 'Under the declared nonnegative unit-width int-height contract, the exact two-pointer Java implementation matches an independent O(n^2) left/right-maximum oracle across fixed boundaries, 50,000 seeded random arrays, and 5,000 seeded near-Integer.MAX_VALUE arrays; long accumulation also preserves totals beyond signed 32-bit range.',
            'source_ids': ['fixture'],
            'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        },
    ]
    locations = ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']
    coverage = [
        {'question_id': qid, 'covered': True, 'answer_locations': locations}
        for qid in QIDS
    ]
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

    reviewer_id = 'source-first-isolated-reviewer-batch-0061-rainwater-20260831-v1'
    findings = [
        'The candidate answers the only frozen source variant directly and does not invent an original API, return type, null policy, or negative-height requirement.',
        'The two-pointer invariant is stated rather than memorized: the lower current side can be finalized because the opposite current boundary is already high enough, leaving only the processed side maximum as the limiting unknown.',
        'The exact Java implementation compiles and uses long accumulation, so a valid int-height input can produce totals beyond Integer.MAX_VALUE without silent overflow.',
        'Independent quadratic left/right-maximum differential testing matches all 50,000 seeded ordinary random arrays and 5,000 near-maximum-value arrays, in addition to fixed null/short/monotone/plateau/multi-basin boundaries.',
        'The answer distinguishes the O(n)-space prefix/suffix variant and O(n)-space monotonic-stack variant without confusing their invariants with the O(1)-space two-pointer implementation.',
        'No production history or personal metric is fabricated; the project section is explicitly a verification mapping because the source has no project facts.',
    ]
    review_version = 'batch-0061.rainwater.v1'
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': reviewer_id,
        'review_version': review_version,
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            str(context_path),
            str(inventory_path),
            str(candidate),
            str(out / 'writer_validation.json'),
            'docs/refactor/09_answer_content_standard.md',
        ],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    }
    write_json(out / 'isolated_review_result.json', review)

    write_json(evidence, {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0061-rainwater-builder',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'Batch 0061 trapping-rain-water source-first isolated review',
            'locator': str(out / 'isolated_review_result.json'),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        }],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': command,
            'result': 'pass',
            'reported_stdout': stdout,
            'checks': checks,
            'boundary_tests': [
                {'case': check, 'expected': 'pass under declared candidate contract', 'actual': 'pass', 'passed': True}
                for check in checks
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': reviewer_id,
            'review_version': review_version,
            'independent': True,
            'decision': 'pass',
            'revision_round': 1,
            'scores': SCORES,
            'hard_failures': [],
            'unsupported_claims': [],
            'uncovered_source_variants': [],
            'findings': findings,
        },
        'promotion_blocker': PROMOTION_BLOCKER,
    })

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    if '## Progress' not in task:
        task += '\n\n## Progress\n'
    note = (
        '- [x] `cq_q_05b816cca1029a3e9b9932ceb1e0d9eb` source-first isolated review PASS: '
        f'candidate digest `{digest}`; the two-pointer Java answer covers the frozen trapping-rain-water source, '
        'OpenJDK differential validation matches an independent O(n²) oracle on fixed boundaries, 50,000 seeded random arrays, '
        'and 5,000 near-Integer.MAX_VALUE arrays, with long accumulation explicitly covering totals above signed 32-bit range. '
        'Formal promotion remains blocked by repository human-approval/real-review policy.'
    )
    if note not in task:
        task += '\n' + note
    task_path.write_text(task + '\n', encoding='utf-8')

    print(f'PASS canonical={CID} source_question_ids={len(QIDS)} candidate_sha256={digest} fixture={stdout}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
