#!/usr/bin/env python3
"""Build and validate the source-bounded Batch 0062 Two Sum candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_ffe5f2da4a3ce9f56c51bce699ab1b13'
QID = 'ffe5f2da4a3ce9f56c51bce699ab1b13'
EXPECTED_VARIANT = '算法：两数之和'
EXPECTED_STDOUT = 'PASS fixed=10 random_cases=30000 oracle=earliest-right-bruteforce overflow=pass input_unchanged=pass'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ffe5f2da4a3ce9f56c51bce699ab1b13","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 两数之和（Two Sum）

## 核心结论

来源只保留“算法：两数之和”，没有给固定 API、目标值是否恒定、是否保证唯一解、无解行为或返回值/下标。本答案声明一个可执行 Java 契约：`twoSum(int[] nums, int target)` 返回一组不同下标 `[i, j]` 且 `i < j`、`nums[i] + nums[j] == target`；若有多组解，返回从左到右扫描时最先完成的那组（最小 `j`，同一 `j` 取最早出现的补数下标）；无解、`null` 或长度不足 2 返回空数组；不修改输入。实现用哈希表保存“某个值第一次出现的下标”，扫描当前 `j` 时先查补数，再登记当前值。

## 1 分钟版

- 暴力双循环是 `O(n^2)`；哈希表把“之前是否出现过补数”降为期望 `O(1)` 查询，因此整体期望 `O(n)`。
- 从左到右扫描 `j`，先算 `target - nums[j]` 并查历史下标；命中就返回 `[i,j]`，这样天然保证不会复用同一个元素。
- 当前值要在查询之后再写入表，否则 `target == 2 * nums[j]` 时可能把同一下标错误地用两次。
- 用 `putIfAbsent` 保存某个值第一次出现的位置，使多解时的返回契约确定；重复值例如 `[3,3]`、target=6 也能正确返回两个不同下标。
- `target - nums[j]` 用 `long` 计算并检查是否落在 `int` 范围，避免整型溢出把不存在的补数映射成另一个值。
- 方法不修改数组；无解返回空数组。这些都是本答案显式契约，不是来源已经规定的条件。

## 3 分钟版

```java
import java.util.HashMap;
import java.util.Map;

public final class TwoSum {
    public static int[] twoSum(int[] nums, int target) {
        if (nums == null || nums.length < 2) return new int[0];

        Map<Integer, Integer> firstIndex = new HashMap<>();
        for (int j = 0; j < nums.length; j++) {
            long needLong = (long) target - nums[j];
            if (needLong >= Integer.MIN_VALUE && needLong <= Integer.MAX_VALUE) {
                Integer i = firstIndex.get((int) needLong);
                if (i != null) return new int[]{i, j};
            }
            firstIndex.putIfAbsent(nums[j], j);
        }
        return new int[0];
    }
}
```

例如 `nums=[2,7,11,15]`、`target=9`：扫描 2 时补数 7 尚未出现，记录 `2 -> 0`；扫描 7 时补数 2 已在表中，于是返回 `[0,1]`。对于 `[3,3]`、target=6，第一个 3 先登记，第二个 3 再查询到历史下标 0，因此返回 `[0,1]`，不会把同一个元素复用两次。

## 关键细节

- **为什么先查后放**：表只代表当前位置左侧已经出现的元素，因此命中的 `i` 必然小于当前 `j`。若先放当前元素，补数等于自身时会误命中同一下标。
- **为何保存第一次出现**：`putIfAbsent` 固定了“同一个值取最早下标”的策略；配合从左到右扫描，返回结果在多解输入上是确定的。
- **溢出边界**：若直接写 `int need = target - nums[j]`，例如 `target=Integer.MIN_VALUE` 且当前值为 1，会溢出成一个错误的正数。先提升到 `long`，超出 int 值域就说明数组中的 int 不可能等于该补数。
- **重复值**：相同数可以来自不同下标；`[3,3]` 对 target=6 是合法答案。哈希表存“值 -> 最早历史下标”，不会把值相同误解成元素相同。
- **无解语义**：来源没有说明是否保证存在答案。本契约明确返回空数组，而不是抛异常或返回 `[-1,-1]`。
- **复杂度**：一次线性扫描，HashMap 查询/插入平均 `O(1)`，所以期望时间 `O(n)`、最坏情况受哈希实现影响；额外空间 `O(n)`。

## 原理机制

核心等式是 `nums[i] + nums[j] = target`。当扫描到右端点 `j` 时，只需要知道左侧是否出现过 `target - nums[j]`。因此哈希表不是简单的“为了快”，而是在维护一个前缀索引：进入第 `j` 轮时，表中只含 `[0, j)` 的值及其最早下标。查询成功就构造出两个不同位置；查询失败再把当前值加入前缀，为后续位置服务。

如果改用排序 + 双指针，可以在 `O(n log n)` 时间内找到值对，但若要求返回原始下标，就需要额外保留索引映射；哈希方案更直接地满足当前“返回下标”的契约。

## 项目经验版

来源是算法题，没有真实项目、吞吐或数据分布信息，不能虚构线上经验。真实工程里若输入极大、内存受限或数据是流式到达，`O(n)` 哈希空间可能成为主要约束；此时应先确认是否允许排序、是否只需判断存在性、是否需要全部解，再选择外排、分桶或流式状态方案，而不是默认套用当前内存算法。

## 常见追问

- 问：为什么不用两层循环？答：两层循环空间是 `O(1)`，但时间 `O(n^2)`；哈希表用 `O(n)` 空间换取期望 `O(n)` 时间。
- 问：为什么先查补数再把当前值放进 Map？答：这样 Map 只包含左侧元素，确保两个下标不同；先放会在“当前值正好是自己补数”时误用同一下标。
- 问：数组有重复值怎么办？答：重复值对应不同下标仍可组成答案，例如 `[3,3]`。保存第一次出现的位置，并在后一个 3 到来时命中前一个。
- 问：如果有多组答案返回哪组？答：来源未规定。本契约返回最早完成的右端点 `j`，同一 `j` 使用补数第一次出现的下标，因此结果确定。
- 问：为什么补数要用 `long`？答：`target - nums[j]` 可能超出 int 范围；若先在 int 中溢出，可能错误命中另一个值。
- 问：如果要求返回所有下标对呢？答：单个“值 -> 一个下标”的 Map 不够，需要保存每个值的多个历史位置或采用另一套枚举策略，输出规模本身也可能达到 `O(n^2)`。

## 易错点

- 先把当前元素放进 Map，再查补数，导致同一下标被使用两次。
- 用 `Map.put` 覆盖早期重复值，却仍声称多解时返回最早历史下标。
- 在 `int` 中直接做 `target - nums[j]`，忽略溢出。
- 题目没说无解行为，却把某一种哨兵值当作来源要求。
- 只返回值对，却没有注意当前契约要求的是原始下标。
'''

JAVA_IMPL = r'''import java.util.HashMap;
import java.util.Map;

public final class TwoSum {
    public static int[] twoSum(int[] nums, int target) {
        if (nums == null || nums.length < 2) return new int[0];
        Map<Integer, Integer> firstIndex = new HashMap<>();
        for (int j = 0; j < nums.length; j++) {
            long needLong = (long) target - nums[j];
            if (needLong >= Integer.MIN_VALUE && needLong <= Integer.MAX_VALUE) {
                Integer i = firstIndex.get((int) needLong);
                if (i != null) return new int[]{i, j};
            }
            firstIndex.putIfAbsent(nums[j], j);
        }
        return new int[0];
    }
}
'''

JAVA_TEST = r'''import java.util.*;

public final class TwoSumWriterTest {
    private static final Random RNG = new Random(0x62FFE5F2L);

    private static int[] oracle(int[] nums, int target) {
        if (nums == null || nums.length < 2) return new int[0];
        for (int j = 0; j < nums.length; j++) {
            for (int i = 0; i < j; i++) {
                if ((long) nums[i] + nums[j] == target) return new int[]{i,j};
            }
        }
        return new int[0];
    }

    private static void check(int[] nums, int target, String label) {
        int[] before = nums == null ? null : nums.clone();
        int[] expected = oracle(nums, target);
        int[] actual = TwoSum.twoSum(nums, target);
        if (!Arrays.equals(actual, expected)) throw new AssertionError(label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
        if (nums != null && !Arrays.equals(nums, before)) throw new AssertionError(label + " mutated input");
    }

    public static void main(String[] args) {
        check(new int[]{2,7,11,15}, 9, "classic");
        check(new int[]{3,2,4}, 6, "middle-pair");
        check(new int[]{3,3}, 6, "duplicates");
        check(new int[]{1,2,3,4}, 100, "no-solution");
        check(new int[]{1,4,2,3}, 5, "multi-solution-earliest-right");
        check(new int[]{1,1,4}, 5, "earliest-complement-index");
        check(new int[]{Integer.MIN_VALUE, 0, Integer.MAX_VALUE}, -1, "extreme-valid");
        check(new int[]{Integer.MAX_VALUE, -1, 0}, Integer.MIN_VALUE, "overflow-complement-no-false-hit");
        check(new int[]{}, 0, "empty");
        check(null, 0, "null");

        for (int t=0; t<30000; t++) {
            int len = RNG.nextInt(18);
            int[] a = new int[len];
            for (int i=0; i<len; i++) {
                int mode=RNG.nextInt(30);
                a[i] = mode==0 ? Integer.MIN_VALUE : mode==1 ? Integer.MAX_VALUE : RNG.nextInt(101)-50;
            }
            int target;
            int mode=RNG.nextInt(20);
            if (mode==0) target=Integer.MIN_VALUE;
            else if (mode==1) target=Integer.MAX_VALUE;
            else target=RNG.nextInt(201)-100;
            check(a,target,"random-"+t);
        }
        System.out.println("PASS fixed=10 random_cases=30000 oracle=earliest-right-bruteforce overflow=pass input_unchanged=pass");
    }
}
'''


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass':
        raise SystemExit('batch 0062 source inventory is not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item or item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: missing or non-coding in frozen inventory')
    if item.get('question_ids') != [QID] or item.get('source_question_count') != 1 or item.get('source_occurrence_count') != 2:
        raise SystemExit(f'{CID}: frozen ownership/occurrence drift')
    if {x.get('original_question') for x in item.get('source_questions', [])} != {EXPECTED_VARIANT}:
        raise SystemExit(f'{CID}: source wording drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    context_proc = run(['node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite'])
    if context_proc.returncode != 0:
        raise SystemExit(context_proc.stderr or context_proc.stdout)
    context = json.loads(context_proc.stdout)
    write_json(out / 'context.json', context)
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: current context/type drift')
    canonical = context.get('canonical') or {}
    if canonical.get('canonical_id') != CID or canonical.get('question_ids') != [QID]:
        raise SystemExit(f'{CID}: current canonical ownership drift')
    rows = list(context.get('source_questions') or [])
    if len(rows) != 2 or {x.get('original_question') for x in rows} != {EXPECTED_VARIANT}:
        raise SystemExit(f'{CID}: source occurrences drift')
    occurrence_ids = {(x.get('question_id'), x.get('source_note_id'), x.get('source_question_index')) for x in rows}
    if len(occurrence_ids) != 2:
        raise SystemExit(f'{CID}: source occurrence identity collapsed')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE, encoding='utf-8')
    (out / 'TwoSum.java').write_text(JAVA_IMPL, encoding='utf-8')
    (out / 'TwoSumWriterTest.java').write_text(JAVA_TEST, encoding='utf-8')

    proc = run(['bash', '-lc', 'javac TwoSum.java TwoSumWriterTest.java && java TwoSumWriterTest'], cwd=out)
    if proc.returncode != 0:
        raise SystemExit(proc.stderr or proc.stdout)
    stdout = proc.stdout.strip()
    if stdout != EXPECTED_STDOUT:
        raise SystemExit(f'{CID}: writer stdout drift: {stdout!r}')
    for class_file in out.glob('*.class'):
        class_file.unlink()

    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    write_json(out / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'validator': 'batch_0062_two_sum_writer_fixture',
        'command': 'javac TwoSum.java TwoSumWriterTest.java && java TwoSumWriterTest',
        'stdout': stdout,
        'checks': [
            'classic, duplicate, multi-solution, no-solution, empty and null boundaries',
            'deterministic earliest-right/earliest-complement-index contract matches brute-force oracle',
            'integer-extreme cases verify overflow-safe complement computation',
            '30,000 seeded random arrays and targets match the deterministic brute-force oracle',
            'input arrays remain unchanged',
        ],
    })
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'candidate_sha256': digest,
        'source_occurrence_count': 2,
        'sources': [
            {'source_id': 'repository-source', 'title': 'Batch 0062 frozen repository source packet for Two Sum', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
            {'source_id': 'fixture', 'title': 'Two Sum deterministic brute-force differential validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
        ],
        'claims': [
            {'claim_id': 'source-boundary', 'text': 'Both preserved primary-source occurrences ask only for Two Sum; API, target guarantee, no-solution behavior and return form are not preserved source constraints.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论','1 分钟版','3 分钟版','关键细节']},
            {'claim_id': 'algorithm-behavior', 'text': 'Under the declared deterministic Java index-pair contract, the hash-prefix implementation matches an earliest-right brute-force oracle on fixed and 30,000 seeded random cases, including integer extremes.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版','关键细节','原理机制','常见追问']},
        ],
        'source_question_coverage': [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问']}],
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    task_path = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0062.md'
    task = task_path.read_text(encoding='utf-8')
    progress_line = (
        '- [x] `cq_q_ffe5f2da4a3ce9f56c51bce699ab1b13` writer stage complete: both frozen primary-source occurrences of the Two Sum question are preserved; '
        'the candidate declares a deterministic Java index-pair/no-solution/non-mutating contract, uses a prefix HashMap with overflow-safe complement arithmetic, and validates fixed duplicate/multi-solution/extreme boundaries plus 30,000 seeded random arrays against an earliest-right brute-force oracle. Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    )
    if progress_line not in task:
        task = task.rstrip() + '\n' + progress_line + '\n'
        task_path.write_text(task, encoding='utf-8')

    print(f'PASS {CID} digest={digest} validation={stdout}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
