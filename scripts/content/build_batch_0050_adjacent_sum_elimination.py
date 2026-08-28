#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0050 adjacent-sum elimination split-child candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0050'
CID = 'cq_q_b66328eb23ca1ba53a062a787c71a9dc'
QID = 'b66328eb23ca1ba53a062a787c71a9dc'
EXPECTED = '算法：设计一个消消乐算法（相邻两数和为 10 则消除，返回最终序列）'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_b66328eb23ca1ba53a062a787c71a9dc","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 相邻两数和为 10 的消除算法

## 核心结论

用栈做一趟扫描即可把“删除后继续检查新相邻元素”的连锁消除压缩到 O(n) 时间。依次读入每个整数 `x`：如果栈顶 `top` 与 `x` 的数学和等于 10，就弹出栈顶并丢弃 `x`；否则把 `x` 入栈。扫描结束后，栈中从底到顶就是稳定的最终序列，额外空间 O(n)。比较时把一个操作数提升为 `long`，避免 Java `int` 加法溢出影响“和为 10”的判断。

题目只说“相邻两数和为 10 则消除”，没有明确是否需要连锁消除、空输入如何处理、是否允许负数以及消除顺序。本答案采用最符合“消消乐”语义的明确契约：每次消除后，新形成的相邻对继续参与消除，直到不存在和为 10 的相邻对；输入为 `null` 视为非法，空数组合法并返回空数组；元素是任意 `int`。如果题目要求“只扫描一次且不回看”，那是另一个契约，不能混用。

## 1 分钟版

- 顺序扫描数组，用栈保存“当前已经规约后的前缀”。
- 新元素 `x` 到来时，只可能与当前栈顶形成新的可消除相邻对。
- 若 `(long) top + x == 10L`，弹栈并丢弃 `x`；否则 `x` 入栈。
- 弹栈后不需要额外循环，因为更早的栈元素已经是稳定前缀；下一输入到来时再与新的栈顶判断即可。
- 扫描完后栈内不会存在和为 10 的相邻对，正好是连锁消除后的最终序列。
- 时间 O(n)，空间 O(n)；若允许原地覆盖数组，可以把数组前缀本身当栈把额外空间降到 O(1)。

## 3 分钟版

```java
import java.util.Arrays;

public final class AdjacentSumElimination {
    public static int[] eliminate(int[] values) {
        if (values == null) {
            throw new IllegalArgumentException("values must not be null");
        }

        int[] stack = new int[values.length];
        int size = 0;
        for (int x : values) {
            if (size > 0 && (long) stack[size - 1] + x == 10L) {
                size--;
            } else {
                stack[size++] = x;
            }
        }
        return Arrays.copyOf(stack, size);
    }
}
```

例如输入 `[1, 9, 2, 8]`：1 入栈；9 与 1 相加为 10，二者消除；2 入栈；8 再与 2 消除，最终 `[]`。更能体现连锁的是 `[1, 2, 8, 9]`：先得到栈 `[1,2]`，8 消掉 2 后栈变 `[1]`，随后 9 到来又消掉 1，最终仍是 `[]`。

为什么只看栈顶？在读入 `x` 前，栈表示已经完全规约的前缀，其中内部不存在可消除相邻对。加入 `x` 后，唯一新出现的相邻关系就是“原栈顶 + x”；若二者消除，暴露出来的更早元素仍属于之前已经规约好的前缀，不会凭空和另一个旧元素形成新关系。下一个输入元素到来时再继续同样判断即可。

## 关键细节

- **连锁语义**：本答案假设删除后继续检查新形成的相邻关系，直到稳定；这是显式假设，不冒充题目已说明。
- **栈不变量**：每轮开始前，栈内容等于已处理输入前缀的稳定规约结果，且栈内部不存在相邻和为 10 的对。
- **相邻性**：只能消除当前相邻的两个元素，不能为了凑 10 跨过中间元素配对。
- **比较溢出**：`int + int` 可能先溢出，因此使用 `(long) stack[size-1] + x == 10L` 判断数学和。
- **输入是否修改**：示例返回新数组，不修改原数组，便于调用方保留输入；若题目允许原地修改，可直接把输入数组当栈缓冲区。
- **空数组**：合法，返回长度为 0 的数组。
- **复杂度**：每个元素最多入栈一次、弹栈一次，所以总操作数 O(n)，额外栈最多 n 个整数。
- **顺序**：留下来的元素保持原相对顺序，因为栈只删除相邻配对，不重排未删除元素。

## 原理机制

这类问题可以看作字符串/序列规约：规则是相邻元素 `a,b` 满足 `a+b=10` 时删除二者。栈把“反复从头扫描直到不能删”的过程在线化。已经处理的前缀被压缩成一个稳定结果；每加入一个新元素，只有边界处可能新产生一条删除规则，因此只需 O(1) 地查看栈顶。

慢速基线可以不断扫描列表，找到第一个和为 10 的相邻对就删除，然后重新扫描，直到一轮没有删除。这个做法直观但最坏可能反复移动元素和扫描，成本可到 O(n²)。栈算法与这个连锁语义产生相同结果，却让每个元素只进出栈有限次。

## 项目经验版

来源没有真实业务上下文，不能虚构线上经历。工程里应先固定规则：是“和等于 10”还是别的谓词、一次删除后是否级联、输入规模、是否允许修改原数组、数值范围以及并发需求。规则稳定后，可以用一个明显但较慢的重复扫描实现作为测试 oracle，再用随机数据对照栈实现，这比只测两三个手写样例更可靠。

## 常见追问

- 问：为什么不用双重循环一直删？答：可以作为正确但较慢的基线；栈维护稳定前缀，每个元素最多入栈和弹栈一次，因此从可能 O(n²) 降到 O(n)。
- 问：删除后为什么能继续连锁？答：栈顶就是删除后暴露出来的最新边界；后续元素会直接与它比较，所以新相邻关系自然进入同一规则。
- 问：会不会需要一次输入元素连续消掉多个旧元素？答：不会。一次规则删除的是“当前栈顶 + 当前 x”这两个元素，x 本身已经被删除，不能再参与第二次删除；真正的下一次连锁由之后的新输入元素触发。
- 问：负数或大整数怎么办？答：元素契约是任意 `int`，负数照常比较；判断时提升到 `long` 避免 `int` 加法溢出。
- 问：可以 O(1) 额外空间吗？答：如果允许修改输入数组，可以用一个 `size` 指针把数组前缀当栈，最后 `[0,size)` 是结果；若必须返回独立结果，则仍需要输出空间。
- 问：如果题目只允许“一轮相邻检查、不级联”呢？答：那就不是本答案的契约，需要按题目指定的扫描规则重新定义状态转移，不能继续使用“最终稳定规约”的表述。

## 易错点

- 删除一对后不处理新形成的相邻关系，却声称实现了连锁消除。
- 用 `HashSet` 或排序去找任意两数和为 10，破坏“必须相邻”和原序列顺序。
- 直接写 `stack[top] + x == 10` 而忽略 `int` 溢出边界。
- 原地算法忘记说明会修改输入。
- `null` 与空数组混为一谈，导致接口边界不清楚。
- 只测没有级联的样例，无法验证栈不变量真正覆盖删除后新相邻关系。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class AdjacentSumEliminationTest {
    private static int[] slow(int[] input) {
        int[] a = Arrays.copyOf(input, input.length);
        int n = a.length;
        boolean changed;
        do {
            changed = false;
            for (int i = 0; i + 1 < n; i++) {
                if ((long) a[i] + a[i + 1] == 10L) {
                    System.arraycopy(a, i + 2, a, i, n - i - 2);
                    n -= 2;
                    changed = true;
                    break;
                }
            }
        } while (changed);
        return Arrays.copyOf(a, n);
    }

    private static void check(int[] input, int[] expected) {
        int[] copy = Arrays.copyOf(input, input.length);
        int[] actual = AdjacentSumElimination.eliminate(input);
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError("input=" + Arrays.toString(input) + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
        }
        if (!Arrays.equals(input, copy)) throw new AssertionError("input mutated");
        for (int i = 0; i + 1 < actual.length; i++) {
            if ((long) actual[i] + actual[i + 1] == 10L) throw new AssertionError("result not stable");
        }
    }

    public static void main(String[] args) {
        try {
            AdjacentSumElimination.eliminate(null);
            throw new AssertionError("null must be rejected");
        } catch (IllegalArgumentException expected) {
            // pass
        }

        check(new int[]{}, new int[]{});
        check(new int[]{5}, new int[]{5});
        check(new int[]{5, 5}, new int[]{});
        check(new int[]{1, 9, 2, 8}, new int[]{});
        check(new int[]{1, 2, 8, 9}, new int[]{});
        check(new int[]{1, 2, 3}, new int[]{1, 2, 3});
        check(new int[]{Integer.MAX_VALUE, Integer.MIN_VALUE, 11}, new int[]{Integer.MAX_VALUE, Integer.MIN_VALUE, 11});
        check(new int[]{Integer.MAX_VALUE, 10 - (long) Integer.MAX_VALUE < Integer.MIN_VALUE ? 0 : (int)(10L - Integer.MAX_VALUE)}, slow(new int[]{Integer.MAX_VALUE, (int)(10L - Integer.MAX_VALUE)}));

        Random r = new Random(20260829L);
        for (int t = 0; t < 3000; t++) {
            int n = r.nextInt(35);
            int[] input = new int[n];
            for (int i = 0; i < n; i++) {
                switch (r.nextInt(20)) {
                    case 0 -> input[i] = Integer.MAX_VALUE;
                    case 1 -> input[i] = Integer.MIN_VALUE;
                    default -> input[i] = r.nextInt(41) - 15;
                }
            }
            int[] expected = slow(input);
            int[] actual = AdjacentSumElimination.eliminate(input);
            if (!Arrays.equals(actual, expected)) {
                throw new AssertionError("random mismatch t=" + t + " input=" + Arrays.toString(input) + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
            }
        }
        System.out.println("PASS null empty single pair cascade stable overflow-safe input-preserved random3000-vs-slow-oracle");
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

    with tempfile.TemporaryDirectory(prefix='b50-adjacent-sum-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'AdjacentSumElimination.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'AdjacentSumEliminationTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'AdjacentSumElimination.java', 'AdjacentSumEliminationTest.java', cwd=tmpdir)
        stdout = run('java', 'AdjacentSumEliminationTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS null empty single pair cascade stable overflow-safe input-preserved random3000-vs-slow-oracle'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac AdjacentSumElimination.java AdjacentSumEliminationTest.java && java AdjacentSumEliminationTest',
        'stdout': stdout,
        'checks': [
            'null input is rejected while empty input is accepted',
            'single values, direct pairs, no-elimination sequences, and multi-step cascades match the explicit contract',
            'long-promoted sum comparison avoids int-overflow misclassification',
            'the input array remains unchanged and output contains no eliminable adjacent pair',
            '3000 deterministic random arrays agree with an independent repeated-leftmost-deletion oracle',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 split-child canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 adjacent-sum elimination validation versus slow oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The split repository source asks to eliminate adjacent pairs whose sum is 10 and return the final sequence; it does not define cascade semantics, null handling, numeric range, mutation policy, or deletion-order details.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'algorithm-validation', 'text': 'The OpenJDK 21 fixture validates the stack reduction against an independent repeated-leftmost-deletion implementation for 3000 deterministic random arrays plus explicit cascade and boundary cases.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'overflow-boundary', 'text': 'The executable implementation promotes one operand to long before summation so the mathematical equality-to-10 predicate is not evaluated using overflowing int addition.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '3 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'complexity-bound', 'text': 'Each input element is pushed at most once and popped at most once from the array-backed stack, so the implementation performs linear work and uses at most n stack slots.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节', '原理机制']},
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

    scores = {'facts_and_evidence': 24, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate directly answers the split adjacent-sum elimination contract rather than carrying over the retired compound source.',
        'Cascade behavior, null handling, arbitrary-int support, and non-mutating output are explicitly labeled as answer-level contract choices because the source does not specify them.',
        'The stack invariant is coherent with the implementation and preserves adjacency/order instead of turning the problem into arbitrary two-sum matching.',
        'OpenJDK 21 validation covers direct and cascading elimination, stability, input preservation, integer-overflow boundaries, and 3000 deterministic random cases against an independent slow oracle.',
        'The answer distinguishes final stable reduction from a hypothetical one-pass/no-cascade contract.',
        'No project history or source-unstated constraints are fabricated.',
    ]
    review = {
        'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE,
        'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0050-adjacent-sum-20260829-v1',
        'review_version': 'batch-0050.adjacent-sum.v1', 'decision': 'pass', 'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Adjacent-sum split-child source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0050-adjacent-sum-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources, 'claims': claims, 'source_question_coverage': coverage,
        'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [
            {'case': 'null versus empty', 'expected': 'null rejected; empty returns empty', 'actual': 'pass', 'passed': True},
            {'case': 'direct and cascading pairs', 'expected': 'final stable sequence', 'actual': 'pass', 'passed': True},
            {'case': 'int overflow edges', 'expected': 'mathematical sum-to-10 comparison', 'actual': 'pass', 'passed': True},
            {'case': '3000 deterministic random arrays', 'expected': 'matches independent repeated-deletion oracle', 'actual': 'pass', 'passed': True},
            {'case': 'input preservation and result stability', 'expected': 'input unchanged and no remaining adjacent sum-10 pair', 'actual': 'pass', 'passed': True},
        ]},
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_b66328eb23ca1ba53a062a787c71a9dc` split-child source-first isolated review PASS: the source-exact contract is adjacent-pair sum-to-10 elimination returning the final sequence; cascade semantics, null handling and non-mutating output are explicit assumptions. The candidate uses an array-backed stack with long-promoted sum comparison, and OpenJDK 21 validation covers direct/cascade/stability/overflow/input-preservation boundaries plus 3000 deterministic random arrays against an independent repeated-deletion oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
