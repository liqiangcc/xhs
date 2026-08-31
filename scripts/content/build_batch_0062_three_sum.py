#!/usr/bin/env python3
"""Build and validate the source-bounded Batch 0062 3Sum candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_e1cbd1e9e8df435dfb30e81ea69018c8'
QIDS = ['e1cbd1e9e8df435dfb30e81ea69018c8']
EXPECTED_VARIANT = '算法手撕：三数之和（3Sum）。'
EXPECTED_STDOUT = 'PASS fixed=9 random_cases=20000 oracle=bruteforce-triples overflow=pass input_unchanged=pass dedupe=pass'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e1cbd1e9e8df435dfb30e81ea69018c8","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 三数之和（3Sum）

## 核心结论

这里按当前来源上下文中的 3Sum / LeetCode 15 口径，求数组中所有“值三元组”使三数之和为 `0`，结果不能重复。来源没有规定语言、返回顺序或是否允许修改输入；本答案声明一个可执行 Java 契约：输入为 `int[]`，方法不修改原数组，返回所有唯一三元组；每个三元组内部升序。实现先复制并排序，再枚举第一个数 `i`，对右侧区间用左右双指针寻找另外两个数，同时在 `i`、`left`、`right` 三个层面跳过重复值。

## 1 分钟版

- 先排序，把无序的三数组合问题转成“固定一个数 + 在有序区间里找两数之和”。
- 枚举 `a[i]`；若它和前一个值相同就跳过，避免同一个首元素产生重复三元组。
- 对 `[i+1, n-1]` 放 `left/right`。和小于 0 就增大 `left`，和大于 0 就减小 `right`。
- 找到 0 后记录 `[a[i], a[left], a[right]]`，两边都移动，并跳过相同值，保证值三元组唯一。
- 求和用 `long`，避免三个 `int` 相加发生溢出后把比较方向判断错。
- 排序是 `O(n log n)`，外层最多 `n` 次、每次双指针线性扫描，所以总时间 `O(n^2)`；若不计返回结果，额外工作空间取决于排序实现。本答案为了“不修改输入”先 clone 一份数组，因此额外数组空间 `O(n)`。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class ThreeSum {
    public static List<List<Integer>> threeSum(int[] nums) {
        List<List<Integer>> ans = new ArrayList<>();
        if (nums == null || nums.length < 3) return ans;

        int[] a = nums.clone();
        Arrays.sort(a);

        for (int i = 0; i < a.length - 2; i++) {
            if (i > 0 && a[i] == a[i - 1]) continue;
            if (a[i] > 0) break;

            int left = i + 1;
            int right = a.length - 1;
            while (left < right) {
                long sum = (long) a[i] + a[left] + a[right];
                if (sum < 0) {
                    left++;
                } else if (sum > 0) {
                    right--;
                } else {
                    ans.add(List.of(a[i], a[left], a[right]));
                    int lv = a[left], rv = a[right];
                    while (left < right && a[left] == lv) left++;
                    while (left < right && a[right] == rv) right--;
                }
            }
        }
        return ans;
    }
}
```

例如 `[-1, 0, 1, 2, -1, -4]` 排序后是 `[-4, -1, -1, 0, 1, 2]`。固定第一个 `-1` 时，双指针可以找到 `[-1,-1,2]` 和 `[-1,0,1]`；第二个连续的 `-1` 作为首元素会被跳过，因此不会重复生成同样的值三元组。

## 关键细节

- **为什么双指针成立**：固定 `a[i]` 后，需要在有序区间找 `a[left] + a[right] = -a[i]`。当前和偏小，只增大左值才可能接近目标；当前和偏大，只减小右值才可能接近目标。
- **去重有三层**：`i` 去重避免相同首元素重复扫描；命中后 `left/right` 都跳过本次值，避免相同二元组合重复输出。不能仅靠最后把结果放进 Set 来掩盖搜索层面的重复逻辑。
- **为何 `a[i] > 0` 可提前结束**：数组已升序，若当前最小的首元素都大于 0，则后面的两个数也不小于它，三数之和不可能回到 0。
- **溢出边界**：三个 `int` 直接相加可能溢出，因此先把首项提升成 `long` 再求和。
- **输入修改**：很多写法直接 `Arrays.sort(nums)`；本答案明确选择 `clone` 后排序，所以调用者的数组保持不变。这是答案契约，不是来源要求。
- **重复值不是重复记录**：例如 `[0,0,0,0]` 有很多索引组合，但值三元组只有 `[0,0,0]` 一种。

## 原理机制

暴力做法枚举三个下标是 `O(n^3)`。排序提供了单调性：固定一个数后，剩余目标成为有序数组上的 Two Sum。左右指针每轮至少有一个向中间移动，因此一次固定首元素的扫描是 `O(n)`；再乘外层 `O(n)`，得到 `O(n^2)`。

去重必须和“值组合”语义绑定。题目要的是不重复的三元组值，不是所有不同下标组合，所以排序后可以用“相邻相同值”判断本轮是否会重复产生同一值组合。若题目改成要求返回所有索引三元组，去重策略和输出契约就必须重新定义。

## 项目经验版

来源是算法题，没有真实项目、数据规模或延迟指标，不能虚构线上经历。实际工程里如果 `n` 很大，应先确认是否真的需要枚举全部解，因为结果数量本身可能很大；如果数据流不能整体排序，或目标不是 0，也要重新选择契约与算法，而不是机械套用本实现。

## 常见追问

- 问：为什么不能用 HashSet 做两数之和？答：可以做到固定一个数后近似线性查找，但唯一三元组的去重、确定性输出和额外空间处理更复杂；排序 + 双指针把移动方向和去重都放在有序结构上表达。
- 问：为什么命中后左右都要移动？答：当前这两个值已经和固定首元素组成一个解；若只移动一侧，会继续撞到相同值组合，必须越过这次左右值的重复段。
- 问：`a[i] == 0` 能提前结束吗？答：不能直接结束；后面可能还有两个 0，`[0,0,0]` 是合法解。只有 `a[i] > 0` 才能确定后续三数都为正。
- 问：为什么求和要用 `long`？答：比较逻辑依赖和的正负，`int` 溢出会改变符号并让指针朝错误方向移动。
- 问：如果目标是任意 `target` 呢？答：把比较对象从 0 改为 `target`，并注意 `target - a[i]` 的溢出；当前来源上下文对应的是和为 0 的 3Sum 口径。
- 问：能否做到比 `O(n^2)` 更快？答：当前实现给出标准确定性排序双指针解；若讨论更强的模型或特定值域，需要额外前提，不能在本来源上直接承诺通用次平方复杂度。

## 易错点

- 只跳过重复 `i`，命中后没有跳过重复 `left/right`，导致重复结果。
- 用 `int sum = a[i] + a[left] + a[right]`，在极值输入上发生溢出。
- `a[i] >= 0` 就 break，错误漏掉 `[0,0,0]`。
- 直接排序调用者数组，却没有说明会修改输入。
- 把“不同索引组合”和“唯一值三元组”混为一谈，导致去重契约不清。
'''

JAVA_IMPL = r'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class ThreeSum {
    public static List<List<Integer>> threeSum(int[] nums) {
        List<List<Integer>> ans = new ArrayList<>();
        if (nums == null || nums.length < 3) return ans;
        int[] a = nums.clone();
        Arrays.sort(a);
        for (int i = 0; i < a.length - 2; i++) {
            if (i > 0 && a[i] == a[i - 1]) continue;
            if (a[i] > 0) break;
            int left = i + 1, right = a.length - 1;
            while (left < right) {
                long sum = (long) a[i] + a[left] + a[right];
                if (sum < 0) {
                    left++;
                } else if (sum > 0) {
                    right--;
                } else {
                    ans.add(List.of(a[i], a[left], a[right]));
                    int lv = a[left], rv = a[right];
                    while (left < right && a[left] == lv) left++;
                    while (left < right && a[right] == rv) right--;
                }
            }
        }
        return ans;
    }
}
'''

JAVA_TEST = r'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Random;
import java.util.Set;
import java.util.TreeSet;

public final class ThreeSumWriterTest {
    private static final Random RNG = new Random(0x62E1CBD1L);

    static String key(int x, int y, int z) {
        int[] a = {x,y,z}; Arrays.sort(a);
        return a[0] + "," + a[1] + "," + a[2];
    }
    static Set<String> normalize(List<List<Integer>> rows) {
        Set<String> out = new TreeSet<>();
        for (List<Integer> row : rows) {
            if (row.size() != 3) throw new AssertionError("not a triplet: " + row);
            String k = key(row.get(0), row.get(1), row.get(2));
            if (!out.add(k)) throw new AssertionError("duplicate result triplet: " + k);
            long sum = (long) row.get(0) + row.get(1) + row.get(2);
            if (sum != 0L) throw new AssertionError("non-zero triplet: " + row);
        }
        return out;
    }
    static Set<String> oracle(int[] nums) {
        Set<String> out = new TreeSet<>();
        for (int i=0;i<nums.length;i++) for (int j=i+1;j<nums.length;j++) for (int k=j+1;k<nums.length;k++) {
            if ((long)nums[i] + nums[j] + nums[k] == 0L) out.add(key(nums[i],nums[j],nums[k]));
        }
        return out;
    }
    static void check(int[] input, Set<String> expected, String label) {
        int[] before = input.clone();
        Set<String> actual = normalize(ThreeSum.threeSum(input));
        if (!actual.equals(expected)) throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        if (!Arrays.equals(input,before)) throw new AssertionError(label + " mutated input");
    }
    static Set<String> set(String... xs) { return new TreeSet<>(Arrays.asList(xs)); }

    public static void main(String[] args) {
        check(new int[]{-1,0,1,2,-1,-4}, set("-1,-1,2","-1,0,1"), "classic");
        check(new int[]{0,0,0,0}, set("0,0,0"), "all-zero");
        check(new int[]{1,2,-2,-1}, set(), "none");
        check(new int[]{-2,0,0,2,2}, set("-2,0,2"), "dedupe-both-sides");
        check(new int[]{-4,-2,-2,-2,0,1,2,2,2,3,3,4}, oracle(new int[]{-4,-2,-2,-2,0,1,2,2,2,3,3,4}), "many-duplicates");
        check(new int[]{Integer.MIN_VALUE,1,Integer.MAX_VALUE}, set(Integer.MIN_VALUE + ",1," + Integer.MAX_VALUE), "overflow-zero");
        check(new int[]{Integer.MAX_VALUE,Integer.MAX_VALUE,2,-3,-1}, oracle(new int[]{Integer.MAX_VALUE,Integer.MAX_VALUE,2,-3,-1}), "overflow-direction");
        check(new int[]{-1,-1,-1,2,2,2}, set("-1,-1,2"), "duplicate-index-combos");
        check(new int[]{}, set(), "empty");
        if (!ThreeSum.threeSum(null).isEmpty()) throw new AssertionError("null contract");

        int cases=0;
        for (int t=0;t<20000;t++) {
            int len=RNG.nextInt(10);
            int[] input=new int[len];
            for(int i=0;i<len;i++) input[i]=RNG.nextInt(21)-10;
            int[] before=input.clone();
            Set<String> expected=oracle(input);
            Set<String> actual=normalize(ThreeSum.threeSum(input));
            if(!expected.equals(actual)) throw new AssertionError("random-"+t+" input="+Arrays.toString(input)+" expected="+expected+" actual="+actual);
            if(!Arrays.equals(input,before)) throw new AssertionError("random mutation-"+t);
            cases++;
        }
        if(cases!=20000) throw new AssertionError("case count");
        System.out.println("PASS fixed=9 random_cases=20000 oracle=bruteforce-triples overflow=pass input_unchanged=pass dedupe=pass");
    }
}
'''


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass':
        raise SystemExit('batch source inventory not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item or item.get('answer_type') != 'coding' or item.get('question_ids') != QIDS:
        raise SystemExit(f'{CID}: inventory/type/ownership drift')
    rows = list(item.get('source_questions') or [])
    if item.get('source_question_count') != 1 or item.get('source_occurrence_count') != 2 or len(rows) != 2:
        raise SystemExit(f'{CID}: occurrence inventory drift')
    if any(x.get('question_id') != QIDS[0] or x.get('original_question') != EXPECTED_VARIANT for x in rows):
        raise SystemExit(f'{CID}: source wording drift')
    if len({(x.get('source_note_id'), x.get('source_question_index')) for x in rows}) != 2:
        raise SystemExit(f'{CID}: source occurrences collapsed')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context = json.loads((out / 'context.json').read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'coding' or (context.get('canonical') or {}).get('question_ids') != QIDS:
        raise SystemExit(f'{CID}: context drift')
    ctx_rows = list(context.get('source_questions') or [])
    if len(ctx_rows) != 2 or any(x.get('original_question') != EXPECTED_VARIANT for x in ctx_rows):
        raise SystemExit(f'{CID}: context occurrences drift')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE.rstrip() + '\n', encoding='utf-8')
    (out / 'ThreeSum.java').write_text(JAVA_IMPL, encoding='utf-8')
    (out / 'ThreeSumWriterTest.java').write_text(JAVA_TEST, encoding='utf-8')
    subprocess.run(['javac', 'ThreeSum.java', 'ThreeSumWriterTest.java'], cwd=out, check=True)
    proc = subprocess.run(['java', 'ThreeSumWriterTest'], cwd=out, text=True, capture_output=True, check=True)
    stdout = proc.stdout.strip()
    if stdout != EXPECTED_STDOUT:
        raise SystemExit(f'writer stdout drift: {stdout!r}')
    for cls in out.glob('*.class'):
        cls.unlink()

    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    write_json(out / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'validator': 'batch_0062_three_sum_writer_fixture',
        'command': 'javac ThreeSum.java ThreeSumWriterTest.java && java ThreeSumWriterTest',
        'stdout': stdout,
        'checks': [
            'classic, all-zero, no-solution and duplicate-heavy fixed boundaries',
            'integer-extreme cases verify long-sum comparison behavior',
            '20,000 seeded random arrays match exhaustive brute-force unique value triplets',
            'input array remains byte-for-byte value-equivalent after the call',
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
            {
                'source_id': 'repository-source',
                'title': 'Batch 0062 frozen repository source packet for 3Sum',
                'locator': str(out / 'context.json'),
                'source_type': 'repository_source_record',
                'checked_at': DATE,
            },
            {
                'source_id': 'fixture',
                'title': '3Sum deterministic and randomized brute-force differential validation',
                'locator': str(out / 'writer_validation.json'),
                'source_type': 'executable_test_or_reproducible_experiment',
                'checked_at': DATE,
            },
        ],
        'claims': [
            {
                'claim_id': 'source-boundary',
                'text': 'Both preserved primary-source occurrences ask the same 3Sum coding question; the repository context ties one occurrence to LeetCode 15 while language, return ordering and input-mutation behavior are not source constraints.',
                'source_ids': ['repository-source'],
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节'],
            },
            {
                'claim_id': 'algorithm-behavior',
                'text': 'Under the declared zero-target Java contract, sort plus fixed-first-element two pointers returns exactly the exhaustive brute-force set of unique value triplets on fixed boundaries and 20,000 seeded random arrays, including integer-extreme cases.',
                'source_ids': ['fixture'],
                'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问'],
            },
        ],
        'source_question_coverage': [
            {
                'question_id': QIDS[0],
                'covered': True,
                'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问'],
            }
        ],
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    line = f'- [x] `{CID}` writer stage complete: both frozen primary-source occurrences of the 3Sum question are preserved; the candidate declares a zero-target Java contract, clone-before-sort input behavior and long-sum overflow protection, then validates unique triplets over fixed duplicate/extreme boundaries plus 20,000 seeded random arrays against exhaustive brute-force enumeration. Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    if line not in task:
        task_path.write_text(task + '\n' + line + '\n', encoding='utf-8')

    print(json.dumps({'ok': True, 'canonical_id': CID, 'candidate_sha256': digest, 'stdout': stdout}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
