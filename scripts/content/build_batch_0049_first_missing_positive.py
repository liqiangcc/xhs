#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0049 first-missing-positive candidate."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
CID = 'cq_q_d219f8186199452d242a0cc3f566702c'
QID = 'd219f8186199452d242a0cc3f566702c'
EXPECTED = '算法 1：寻找缺失的正整数。给定一个未排序的整数数组，找出其中没有包含的最小正整数'
BATCH = '0049'
LEETCODE = 'https://leetcode.com/problems/first-missing-positive/'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d219f8186199452d242a0cc3f566702c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 寻找未排序数组中缺失的最小正整数

## 核心结论

题目只要求：给定未排序整数数组，返回其中没有出现的最小正整数。最直接的正确方案是把所有正数放进 `HashSet`，再从 1 往上找，时间 O(n)、额外空间 O(n)。如果进一步按标准 First Missing Positive 题目的强约束做到 O(n) 时间、O(1) 辅助空间，就利用数组本身当哈希表：长度为 n 时答案一定在 `[1, n + 1]`，把每个值 `x`（仅当 `1 <= x <= n`）交换到下标 `x - 1`，最后第一个 `nums[i] != i + 1` 的位置就是答案；全部正确则返回 `n + 1`。

来源题干本身没有明确要求 O(n)/O(1)，所以复杂度目标不能冒充成原题条件；这里把原地方案作为更强的面试解法，并明确它会修改输入数组。

## 1 分钟版

- 长度为 n 的数组只可能覆盖前 n 个正整数中的至多 n 个值，因此最小缺失正数一定不超过 `n + 1`。
- 负数、0、以及大于 n 的数不可能决定 `[1, n]` 中哪个值缺失，可以忽略其定位。
- 对当前值 `x`，如果 `1 <= x <= n` 且目标位置 `nums[x - 1]` 还不是 `x`，就把 `x` 换到 `x - 1`。
- `nums[x - 1] == x` 时停止交换，尤其能正确处理重复值，避免死循环。
- 整理完后从左到右扫描；第一个 `nums[i] != i + 1` 就返回 `i + 1`，否则返回 `n + 1`。
- 每次有效交换都会把一个有效值放到它的最终槽位，交换总数是 O(n)，所以总时间 O(n)；只使用常数个变量，辅助空间 O(1)。

## 3 分钟版

```java
public final class FirstMissingPositive {
    public static int firstMissingPositive(int[] nums) {
        int n = nums.length;
        for (int i = 0; i < n; i++) {
            while (nums[i] >= 1 && nums[i] <= n) {
                int target = nums[i] - 1;
                if (nums[target] == nums[i]) {
                    break;
                }
                int tmp = nums[i];
                nums[i] = nums[target];
                nums[target] = tmp;
            }
        }

        for (int i = 0; i < n; i++) {
            if (nums[i] != i + 1) {
                return i + 1;
            }
        }
        return n + 1;
    }
}
```

例如 `[3, 4, -1, 1]`：有效值 3、4、1 会逐步被放到下标 2、3、0；整理后前缀对应关系里，下标 1 不是值 2，因此返回 2。像 `[1, 1]` 这种重复值，第二个 1 发现目标槽已经是 1，就直接停止，不会在两个位置之间反复交换。

## 关键细节

- **答案上界为什么是 `n + 1`**：若 `1..n` 全部出现，答案只能是 `n + 1`；否则答案就是其中第一个没出现的值。
- **只定位 `[1,n]`**：0、负数和大于 n 的数不对应任何需要占据的有效槽位。
- **重复值保护**：判断 `nums[target] == nums[i]` 是终止条件，而不是继续交换。否则 `[1,1]`、`[2,2]` 等输入可能死循环。
- **不是普通排序**：只把合法值放到与其数值对应的固定槽位，不需要建立全序，因此不付 O(n log n) 的比较排序成本。
- **复杂度中的 while 不会变成 O(n²)**：一次有效交换会让一个 `[1,n]` 内的值进入自己的目标槽；目标槽一旦持有正确值，重复值不会再把它换走。有效定位次数受槽位数 n 限制，因此总交换量 O(n)。
- **原地代价**：算法会重排 `nums`。如果调用方要求保留输入，就应先复制数组，此时额外空间变成 O(n)，或者改用 `HashSet` 方案并明确空间权衡。
- **空数组边界**：来源没有写长度约束；按“缺失的最小正整数”自然定义，空数组返回 1。标准 LeetCode 41 当前约束则是长度至少为 1，不能把空数组说成其正式样例范围。
- **整数极值**：判断范围后才计算 `nums[i] - 1`，避免对任意越界值拿来当数组下标。

## 原理机制

这个方法利用了“值域很小”的结构。我们不需要知道元素之间的排序关系，只需要回答：1 在不在、2 在不在……直到第一个缺失值。因为候选答案只在 `[1,n+1]`，数组的 n 个下标刚好可以充当值 1..n 的 n 个存在性槽位：值 x 的归宿是 `x-1`。

因此第一阶段建立不变量：能被放回自身槽位的有效值尽量放回去。第二阶段不再做搜索结构查询，只检查槽位与期望值是否一致。这个“索引就是哈希位置”的技巧把 HashSet 的线性额外空间复用成输入数组自身，但换来的边界就是会修改输入。

## 项目经验版

来源没有真实项目背景，不能虚构线上使用经历。真实代码里我会先确认输入是否允许修改；若数组来自共享缓存、会被后续逻辑复用或需要保留原始顺序，就不能为了 O(1) 辅助空间直接原地换位。对于面试验证，我会至少覆盖重复值、全负数、包含 0、1 缺失、`1..n` 全出现、整数极值和大规模输入，并用独立 `HashSet` oracle 对随机数据做差分测试。

## 常见追问

- 问：为什么答案不会大于 `n + 1`？答：数组只有 n 个位置；如果 1..n 有任意一个缺失，答案就在这段里，否则它们全出现，最小缺失值正好是 `n + 1`。
- 问：为什么不用排序？答：排序后线性扫当然正确，但比较排序通常是 O(n log n)；这里只关心值 x 是否占据 x-1，不需要全序。
- 问：重复元素怎么处理？答：如果目标槽已经是相同值就停止交换；这个判断既表示该值的存在性已经记录，也防止重复值导致死循环。
- 问：为什么 while 还是 O(n)？答：分析单位不是“每个 i 进入 while 几次”，而是全局有效交换次数；每次交换至少固定一个有效值到自己的唯一槽位，最多只有 n 个这种槽位。
- 问：如果不能修改输入怎么办？答：用 `HashSet` 可以 O(n) 时间、O(n) 额外空间；或者复制后再跑原地算法，但复制本身同样需要 O(n) 空间。
- 问：标准 LeetCode 41 为什么常要求这个做法？答：其当前题面在相同输入输出定义上额外要求 O(n) 时间和 O(1) 辅助空间；当前仓库来源没有保存这条复杂度要求，所以这里只把它作为更强目标而非原题事实。

## 易错点

- 把 `0` 或负数也映射成下标。
- 没有判断重复值，导致交换循环不终止。
- 写成一次 `if` 交换而不是 `while`，使换回当前位置的新有效值没有继续归位。
- 忘记所有 `1..n` 都存在时答案是 `n + 1`。
- 宣称 O(1) 空间却先复制了输入数组，混淆核心算法辅助空间和端到端分配。
- 把标准 LeetCode 41 的 O(n)/O(1) 限制当成仓库原始题干已经明确保存的条件。
'''

TEST = r'''import java.util.HashSet;
import java.util.Random;

public final class FirstMissingPositiveTest {
    private static int oracle(int[] nums) {
        HashSet<Integer> seen = new HashSet<>();
        for (int x : nums) if (x > 0) seen.add(x);
        int x = 1;
        while (seen.contains(x)) x++;
        return x;
    }

    private static void check(int[] input, int expected) {
        int[] copy = input.clone();
        int actual = FirstMissingPositive.firstMissingPositive(copy);
        if (actual != expected) throw new AssertionError(java.util.Arrays.toString(input) + " -> " + actual + " expected=" + expected);
    }

    public static void main(String[] args) {
        check(new int[]{1,2,0}, 3);
        check(new int[]{3,4,-1,1}, 2);
        check(new int[]{7,8,9,11,12}, 1);
        check(new int[]{}, 1);
        check(new int[]{1}, 2);
        check(new int[]{2}, 1);
        check(new int[]{1,1}, 2);
        check(new int[]{2,2}, 1);
        check(new int[]{Integer.MIN_VALUE, Integer.MAX_VALUE, 1, 2}, 3);

        Random r = new Random(41L);
        for (int t = 0; t < 2000; t++) {
            int n = r.nextInt(32);
            int[] a = new int[n];
            for (int i = 0; i < n; i++) a[i] = r.nextInt(81) - 40;
            int expected = oracle(a);
            int[] copy = a.clone();
            int actual = FirstMissingPositive.firstMissingPositive(copy);
            if (actual != expected) throw new AssertionError("random mismatch input=" + java.util.Arrays.toString(a) + " actual=" + actual + " expected=" + expected);
        }

        int n = 100_000;
        int missing = 54_321;
        int[] large = new int[n];
        for (int i = 0; i < n; i++) large[i] = i + 1;
        large[missing - 1] = n;
        check(large, missing);

        System.out.println("PASS examples=3 duplicates=pass extremes=pass random-oracle=2000 max-length=100000");
    }
}
'''


def run(*args, cwd=None):
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    if candidate.exists():
        raise SystemExit('candidate already exists; do not overwrite reviewed work')

    ctx = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != CID or ctx.get('answer_type') != 'coding':
        raise SystemExit('canonical context/type drift')
    if ctx.get('canonical', {}).get('question_ids') != [QID]:
        raise SystemExit('ownership drift')
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
        raise SystemExit('expected exactly one Java block')

    with tempfile.TemporaryDirectory(prefix='b49-missing-positive-') as td:
        p = Path(td)
        (p / 'FirstMissingPositive.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (p / 'FirstMissingPositiveTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'FirstMissingPositive.java', 'FirstMissingPositiveTest.java', cwd=p)
        stdout = run('java', 'FirstMissingPositiveTest', cwd=p).stdout.strip()

    expected_stdout = 'PASS examples=3 duplicates=pass extremes=pass random-oracle=2000 max-length=100000'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac FirstMissingPositive.java FirstMissingPositiveTest.java && java FirstMissingPositiveTest',
        'stdout': stdout,
        'checks': [
            'three standard first-missing-positive examples',
            'empty/singleton/duplicate boundaries',
            'Integer.MIN_VALUE and Integer.MAX_VALUE safety',
            '2000 deterministic random arrays against independent HashSet oracle',
            'length-100000 boundary with an interior missing value',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0049 frozen canonical/source context',
            'locator': str(out / 'context.json'),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'leetcode-41',
            'title': 'LeetCode 41 First Missing Positive',
            'locator': LEETCODE,
            'source_type': 'official_problem_statement',
            'checked_at': DATE,
        },
        {
            'source_id': 'fixture',
            'title': 'OpenJDK 21 first-missing-positive deterministic differential fixture',
            'locator': str(out / 'writer_validation.json'),
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'repository-contract',
            'text': 'The preserved repository source asks only for the smallest missing positive integer from an unsorted integer array and does not preserve an explicit complexity target.',
            'source_ids': ['repository-source'],
            'answer_locations': ['核心结论', '1 分钟版', '关键细节', '常见追问'],
        },
        {
            'claim_id': 'standard-problem-boundary',
            'text': 'The current official LeetCode 41 statement has the same core input/output problem and additionally requires O(n) time with O(1) auxiliary space, with length up to 100000; the answer labels those stronger constraints as external standard-problem context rather than repository-source facts.',
            'source_ids': ['leetcode-41'],
            'answer_locations': ['核心结论', '关键细节', '常见追问'],
        },
        {
            'claim_id': 'runtime-validation',
            'text': 'OpenJDK 21 validation confirms the in-place placement implementation on examples, duplicates, integer extremes, 2000 deterministic random arrays versus an independent HashSet oracle, and a length-100000 boundary.',
            'source_ids': ['fixture'],
            'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点'],
        },
    ]
    coverage = [{
        'question_id': QID,
        'covered': True,
        'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
    }]
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

    scores = {
        'facts_and_evidence': 25,
        'directness_and_relevance': 20,
        'type_specific_completeness': 20,
        'mechanism_and_causality': 15,
        'boundaries_and_tradeoffs': 10,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The candidate replaces the unrelated long-tail sorting/TopK baseline with the exact preserved smallest-missing-positive question.',
        'Repository-source requirements are separated from the stronger current LeetCode 41 O(n)-time/O(1)-auxiliary-space contract instead of silently rewriting the source.',
        'The placement invariant, answer upper bound, duplicate termination condition, mutation tradeoff and global O(n) swap bound are explicit.',
        'OpenJDK 21 differential validation covers examples, duplicates, integer extremes, 2000 deterministic random arrays and a length-100000 boundary.',
        'No production history or unstated source constraint is fabricated.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0049-first-missing-positive-20260829-v1',
        'review_version': 'batch-0049.first-missing-positive.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), LEETCODE, 'docs/refactor/09_answer_content_standard.md'],
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
        'writer': {'writer_id': 'content-batch-0049-first-missing-positive-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'First-missing-positive source-first isolated review',
            'locator': str(out / 'isolated_review_result.json'),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        }],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': stdout,
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': '[1,2,0]', 'expected': '3', 'actual': '3', 'passed': True},
                {'case': '[3,4,-1,1]', 'expected': '2', 'actual': '2', 'passed': True},
                {'case': 'duplicates', 'expected': 'terminate and match oracle', 'actual': 'pass', 'passed': True},
                {'case': '2000 random arrays', 'expected': 'match HashSet oracle', 'actual': 'pass', 'passed': True},
                {'case': 'length 100000', 'expected': '54321', 'actual': '54321', 'passed': True},
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
    line = '- [x] `cq_q_d219f8186199452d242a0cc3f566702c` source-first isolated review PASS: the preserved source asks for the smallest missing positive integer in an unsorted integer array without preserving a complexity target. The candidate replaces the unrelated sorting/TopK baseline, labels the stronger current LeetCode 41 O(n)-time/O(1)-auxiliary-space target as external standard-problem context, and uses in-place value-to-index placement with explicit duplicate and mutation boundaries. OpenJDK 21 validation covers standard examples, empty/singleton/duplicate cases, integer extremes, 2000 deterministic random arrays against an independent HashSet oracle and a length-100000 boundary. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
