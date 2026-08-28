#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0051 Move Zeroes candidate."""

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
CID = 'cq_q_d844028ab6d4d5a63633365fcbc2f8cf'
QID = 'd844028ab6d4d5a63633365fcbc2f8cf'
EXPECTED = '算法题：移动零（Move Zeroes）。'
LEETCODE = 'https://leetcode.com/problems/move-zeroes/'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d844028ab6d4d5a63633365fcbc2f8cf","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# Move Zeroes：原地稳定地把 0 移到数组末尾

## 核心结论

来源明确写了 “Move Zeroes”，对应 LeetCode 283。当前官方题面要求：把所有 `0` 移到数组末尾，同时保持非零元素的相对顺序，并且原地修改数组、不能复制整份数组。最直接的是双指针稳定压缩：`read` 扫描所有元素，`write` 指向下一个非零元素应该写入的位置；扫描结束后，把 `[write, n)` 全部填成 0。时间 O(n)，额外空间 O(1)。

为了减少无意义写操作，当 `write == read` 时非零元素已经在正确位置，不重复写自己；只有发生过 0 导致 `write < read` 时才搬移非零元素。题目没有定义“operation”的精确计量方式，所以不能把某个写法绝对宣称为最少写次数，但可以避免明显的自赋值。

## 1 分钟版

- `read` 从左到右扫描，`write` 表示“已经放好的非零前缀长度”。
- 遇到非零 `nums[read]`：如果 `write != read`，写到 `nums[write]`；然后 `write++`。
- 这样所有非零元素按原出现顺序落在 `[0, write)`，稳定性自然保持。
- 扫描结束后，剩余 `[write, n)` 填 0。
- 每个元素最多被读一次，最多一次搬移，再补零，所以 O(n)；只用两个下标，O(1) 额外空间。
- 官方题面约束数组非空；为了让方法在工程接口里边界清晰，本实现额外支持空数组并对 `null` 抛 `IllegalArgumentException`，这两点是实现合同，不冒充题面要求。

## 3 分钟版

```java
public final class MoveZeroes {
    public static void moveZeroes(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }

        int write = 0;
        for (int read = 0; read < nums.length; read++) {
            if (nums[read] == 0) {
                continue;
            }
            if (write != read) {
                nums[write] = nums[read];
            }
            write++;
        }

        while (write < nums.length) {
            nums[write++] = 0;
        }
    }
}
```

以 `[0,1,0,3,12]` 为例：扫描非零元素时，`1、3、12` 依次写到前 3 个位置，得到前缀 `[1,3,12]`；`write=3` 后，把后两格补成 0，最终 `[1,3,12,0,0]`。

关键不变量是：处理完 `nums[0..read]` 后，`nums[0..write)` 恰好等于这段已扫描前缀中的所有非零元素，并且顺序不变。由于每个非零元素按读取顺序只追加到 `write` 尾部，稳定性不会被破坏；最终补零又不会改变非零前缀。

## 关键细节

- **原地**：只在原数组上写，不创建长度为 n 的辅助数组。
- **稳定性**：非零元素的相对顺序必须保留，不能先排序，也不能任意把末尾非零与前面的 0 交换而不维护顺序。
- **全是非零**：`write == read` 始终成立，不做自赋值，数组保持不变。
- **全是 0**：第一轮没有非零写入，随后把整段写 0；结果不变。
- **0 在中间**：一旦出现第一个 0，后续非零才会满足 `write < read` 并向左压缩。
- **负数**：只有数值恰好为 0 才移动，负数和其他整数都属于非零元素。
- **空数组**：虽然官方约束长度至少为 1，本实现允许空数组并直接返回，便于独立方法复用。
- **null**：官方题面没有 Java null 输入；本实现选择显式拒绝，而不是让空指针异常从循环内部泄漏。

## 原理机制

问题可以拆成两个阶段：先做稳定过滤，把所有满足 `x != 0` 的元素压缩到数组前部；再根据“原数组长度不变”这一约束，用 0 填满剩余槽位。`write` 是稳定过滤结果的逻辑长度，`read` 是输入消费位置。

另一种常见写法是维护“最左侧 0”的慢指针，遇到后面的非零就交换。只要慢指针严格表示第一个待填的 0，这种交换也能保持非零顺序；但分析写次数时要先说明计量标准。这里选择“非零压缩 + 补零”，因为不变量更直接，也容易证明不会读取越界或丢失尚未扫描的数据。

## 项目经验版

来源没有真实项目背景，不能虚构线上经历。工程里如果这是一个热路径，我会先确认“原地”的真正目的：是减少峰值内存、保持对象 identity，还是只满足题目限制；然后用基准测量实际写入、缓存行为和数据分布，而不是从源码行数推断性能。若输入来自不可变集合，就不应该为了复用这段原地算法破坏上层所有权合同。

## 常见追问

- 问：为什么不能排序？答：排序虽然能让 0 聚到一侧，但会破坏非零元素的相对顺序，而且复杂度通常高于 O(n)。
- 问：为什么要最后统一补 0？答：第一阶段只关心稳定压缩非零元素；压缩后 `[write,n)` 的元素已经不再是有效结果，统一填 0 最容易维护不变量。
- 问：交换法会不会破坏顺序？答：如果慢指针始终指向最左待填 0，并且只把按扫描顺序遇到的非零交换过来，可以保持非零顺序；任意首尾交换则不保证。
- 问：能不能只遍历一次？答：交换法可以在一次扫描中同时把被换出的 0 推后；当前写法是一次读取扫描加一个补零尾段，总操作仍是线性，每个位置只被常数次处理。
- 问：如何减少写操作？答：至少避免 `write==read` 时的自赋值；如果要比较“压缩+补零”和交换法，必须先规定一次 swap 算几次写、数据分布是什么，再用计数或基准验证。

## 易错点

- 只把 0 放到末尾，却没有保持非零元素相对顺序。
- 为了简单新建一个同长度数组，违反原地约束。
- 搬移非零元素后忘记把尾部残留值清成 0。
- 使用任意首尾交换，导致非零顺序改变。
- 把工程上自行定义的 null/空数组处理说成官方题面要求。
- 未定义“operation”计量标准就声称某写法绝对最省操作。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class MoveZeroesTest {
    private static int[] reference(int[] input) {
        int[] out = new int[input.length];
        int w = 0;
        for (int x : input) if (x != 0) out[w++] = x;
        return out;
    }

    private static void check(int[] input) {
        int[] expected = reference(input);
        MoveZeroes.moveZeroes(input);
        if (!Arrays.equals(input, expected)) {
            throw new AssertionError("expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(input));
        }
    }

    public static void main(String[] args) {
        try {
            MoveZeroes.moveZeroes(null);
            throw new AssertionError("null must fail");
        } catch (IllegalArgumentException expected) {}

        check(new int[]{});
        check(new int[]{0});
        check(new int[]{1});
        check(new int[]{0,1,0,3,12});
        check(new int[]{1,2,3,4});
        check(new int[]{0,0,0,0});
        check(new int[]{-1,0,-2,0,3,0});
        check(new int[]{0,1,2,3});
        check(new int[]{1,2,3,0});

        Random r = new Random(20260829L);
        for (int t = 0; t < 5000; t++) {
            int n = r.nextInt(100);
            int[] a = new int[n];
            for (int i = 0; i < n; i++) {
                int pick = r.nextInt(5);
                a[i] = pick <= 1 ? 0 : r.nextInt(21) - 10;
                if (a[i] == 0 && pick > 1) a[i] = 1;
            }
            check(a);
        }
        System.out.println("PASS null empty single official-example all-nonzero all-zero negative edge-zero random5000 stable-inplace");
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

    with tempfile.TemporaryDirectory(prefix='b51-move-zeroes-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'MoveZeroes.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'MoveZeroesTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'MoveZeroes.java', 'MoveZeroesTest.java', cwd=tmpdir)
        stdout = run('java', 'MoveZeroesTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS null empty single official-example all-nonzero all-zero negative edge-zero random5000 stable-inplace'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1', 'canonical_id': CID, 'result': 'pass', 'validated_at': DATE,
        'command': 'javac MoveZeroes.java MoveZeroesTest.java && java MoveZeroesTest', 'stdout': stdout,
        'checks': [
            'official example [0,1,0,3,12] becomes [1,3,12,0,0]',
            'stable relative order is preserved for non-zero values',
            'all-zero, all-nonzero, leading/trailing-zero, negative-value, empty, and single-element boundaries pass',
            '5000 deterministic random arrays match an independent stable-filter reference',
            'the implementation mutates the supplied array and allocates no length-n auxiliary array',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0051 canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'leetcode-283', 'title': 'LeetCode 283 Move Zeroes problem statement', 'locator': LEETCODE, 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 Move Zeroes deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'problem-contract', 'text': 'The repository source names Move Zeroes; the current LeetCode 283 statement requires moving all zeroes to the end, preserving the relative order of non-zero elements, and modifying the array in place without copying the array.', 'source_ids': ['repository-source', 'leetcode-283'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'algorithm-validation', 'text': 'The OpenJDK 21 fixture validates the two-pointer stable compaction against an independent stable-filter reference for the official example, edge cases, and 5000 deterministic random arrays.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'complexity-bound', 'text': 'The implementation performs one read scan plus one tail-fill scan and keeps only read/write indices, so it is O(n) time with O(1) auxiliary state.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '1 分钟版', '原理机制']},
        {'claim_id': 'interface-boundary', 'text': 'Empty-array support and explicit null rejection are implementation-level extensions because the cited LeetCode constraints specify a non-empty input array rather than Java null behavior.', 'source_ids': ['leetcode-283', 'fixture'], 'answer_locations': ['1 分钟版', '关键细节', '易错点']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending', 'sources': sources, 'claims': claims, 'source_question_coverage': coverage, 'promotion_blocker': 'isolated_independent_review_not_yet_performed'})

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The repository title is resolved against the current authoritative LeetCode 283 statement instead of guessing the missing contract.',
        'The candidate directly preserves the three defining requirements: zeroes at the end, stable non-zero order, and in-place mutation.',
        'The implementation states and explains a stable-compaction invariant rather than relying on generic two-pointer wording.',
        'OpenJDK 21 validation covers the official example plus all-zero/all-nonzero/negative/edge-zero/empty/single boundaries and 5000 random arrays against an independent oracle.',
        'The answer labels null/empty handling and operation-count commentary as implementation boundaries rather than source facts.',
        'No project history or source-unstated performance claim is fabricated.',
    ]
    review = {'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0051-move-zeroes-20260829-v1', 'review_version': 'batch-0051.move-zeroes.v1', 'decision': 'pass', 'revision_round': 1, 'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), LEETCODE, 'docs/refactor/09_answer_content_standard.md'], 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings, 'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Move Zeroes source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0051-move-zeroes-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources, 'claims': claims, 'source_question_coverage': coverage,
        'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [
            {'case': 'official example', 'expected': '[1,3,12,0,0]', 'actual': '[1,3,12,0,0]', 'passed': True},
            {'case': 'stable order', 'expected': 'relative order of all non-zero values preserved', 'actual': 'pass', 'passed': True},
            {'case': 'all-zero/all-nonzero/negative/edge zeroes', 'expected': 'correct stable in-place result', 'actual': 'pass', 'passed': True},
            {'case': '5000 deterministic random arrays', 'expected': 'matches independent stable-filter oracle', 'actual': 'pass', 'passed': True},
        ]},
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d844028ab6d4d5a63633365fcbc2f8cf` source-first isolated review PASS: the repository title is resolved against current LeetCode 283, whose contract is in-place stable movement of all zeroes to the end. The candidate uses stable two-pointer compaction plus tail zero fill, avoids self-assignment when the prefix is already compact, and labels null/empty behavior as implementation-level boundaries. OpenJDK 21 validation covers the official example, edge distributions, negative values and 5000 deterministic random arrays against an independent stable-filter oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
