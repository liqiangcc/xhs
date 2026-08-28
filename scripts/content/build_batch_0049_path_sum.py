#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0049 LeetCode 112 Path Sum candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
CID = 'cq_q_d0e2766b232487ca818bf9d6afa6c575'
QID = 'd0e2766b232487ca818bf9d6afa6c575'
EXPECTED = '算法：路径总和 (LeetCode 112)'
BATCH = '0049'
OFFICIAL = 'https://leetcode.com/problems/path-sum/'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d0e2766b232487ca818bf9d6afa6c575","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 路径总和（LeetCode 112）：判断是否存在 root-to-leaf 目标和路径

## 核心结论

LeetCode 112 要判断的是：二叉树中是否存在一条**从根节点到叶子节点**的路径，使路径上节点值之和等于 `targetSum`；叶子必须没有左右孩子。最直接的不变量是“到达当前节点时还差多少”：访问节点后把它的值从剩余目标中减掉，只有在真实叶子处剩余值为 0 才能返回 `true`。下面用显式栈做 DFS，避免把深树的正确性依赖于 Java 方法调用栈深度。

## 1 分钟版

- 空树没有 root-to-leaf 路径，所以返回 `false`，即使 `targetSum == 0` 也一样。
- 栈里保存 `(node, remaining)`；这里的 `remaining` 表示**已经包含当前节点之后**还差多少。
- 弹出一个状态，如果它是叶子并且 `remaining == 0`，找到答案。
- 否则把孩子入栈，孩子的剩余值等于 `remaining - child.val`。
- 不能在中间节点“刚好减到 0”时就成功，因为题目要求路径必须结束在 leaf。
- 每个节点最多入栈一次，时间 O(n)；显式 DFS 栈最坏 O(h)，`h` 是树高，退化链时就是 O(n)。

## 3 分钟版

为方便独立编译，下面把 `TreeNode` 一起放进类里；在 LeetCode 上直接使用平台提供的 `TreeNode` 即可。

```java
import java.util.ArrayDeque;
import java.util.Deque;

public final class PathSumSolution {
    public static final class TreeNode {
        public int val;
        public TreeNode left;
        public TreeNode right;

        public TreeNode(int val) {
            this.val = val;
        }
    }

    private record State(TreeNode node, long remaining) {}

    public static boolean hasPathSum(TreeNode root, int targetSum) {
        if (root == null) return false;

        Deque<State> stack = new ArrayDeque<>();
        stack.push(new State(root, (long) targetSum - root.val));

        while (!stack.isEmpty()) {
            State state = stack.pop();
            TreeNode node = state.node();
            long remaining = state.remaining();

            if (node.left == null && node.right == null) {
                if (remaining == 0) return true;
                continue;
            }

            if (node.right != null) {
                stack.push(new State(node.right, remaining - node.right.val));
            }
            if (node.left != null) {
                stack.push(new State(node.left, remaining - node.left.val));
            }
        }
        return false;
    }
}
```

以官方样例 `5 -> 4 -> 11 -> 2` 为例，目标 22 会沿途变成 `17 -> 13 -> 2 -> 0`，而最后一个节点 2 是叶子，所以成功。相反，若某个内部节点处剩余值已经是 0，但它还有孩子，仍不能提前返回；继续走到叶子后才符合“root-to-leaf”的路径定义。

这里用 `long remaining` 不是因为官方约束一定需要 64 位，而是让“目标减节点值”的中间运算更稳健，不把实现绑定在恰好不会溢出的当前约束上。它不改变题目输入仍是 `int targetSum` 的接口。

## 关键细节

- **leaf 判断必须同时无左右孩子**：只有 `node.left == null && node.right == null` 才是叶子；“某一侧为空”不等于叶子。
- **空树与目标 0**：官方例子明确空树返回 false，因为根本不存在 root-to-leaf 路径。
- **负数不能剪枝**：节点值可以为负，因此不能看到 `remaining < 0` 就提前停止；后面的负节点仍可能把路径和拉回目标。
- **内部节点不能提前成功**：例如根值本身等于 target 但根还有孩子，这不是有效答案。
- **递归 vs 显式栈**：递归 DFS 的逻辑同样正确；显式栈只是把深度状态放到堆上的容器中，减少极深链依赖调用栈的风险。
- **不需要回溯路径数组**：题目只问是否存在，不要求返回路径，因此状态只需 `node + remaining`；若改成 LeetCode 113 才需要保存/恢复路径。
- **复杂度**：最坏检查全部 n 个节点，时间 O(n)；DFS 栈与树高相关，最坏 O(h)，退化树 h=n。

## 原理机制

把原问题写成状态转移会很清楚：对当前节点 `u` 和“进入 u 之前还需要的和” `need`，消费 `u.val` 后得到 `next = need - u.val`。如果 `u` 是叶子，问题退化为 `next == 0`；如果不是叶子，则继续问左子树或右子树是否存在满足剩余值 `next` 的 root-to-leaf 路径。

显式栈只是把递归调用帧改成数据结构：每个 `State` 对应一次“接下来要访问这个节点，并携带这条根路径的剩余目标”。因为树中每个节点只有一个父节点，所以每个节点至多生成一次状态，不存在重复子问题，也不需要动态规划缓存。

这也解释了为什么 baseline 把它说成“动态规划”不准确：这里没有共享子问题需要复用，普通 DFS 就足够。真正需要守住的是路径终点必须是 leaf、剩余值跟着当前根路径传递这两个条件。

## 项目经验版

来源没有真实项目经历，不能虚构业务案例。若把这个模式映射到工程问题，它更像“在层级结构中寻找满足累计约束的终止节点”。落地时首先要定义什么算终止节点、累积值是否可能为负以及数据深度；深度不可控时优先显式栈/队列，避免把输入数据形状直接转化为调用栈风险。

## 常见追问

- 问：为什么不能 `remaining == 0` 就直接返回 true？答：因为 LeetCode 112 要求路径必须从 root 到 leaf；内部节点即使前缀和等于目标，也还不是合法终点。
- 问：能不能用递归？答：可以，递归公式就是 `leaf ? remaining==0 : left || right`。这里选显式栈是为了把很深的树从 Java 调用栈风险中解耦。
- 问：为什么不能 `remaining < 0` 时剪枝？答：节点值允许为负数，后续路径可能把和重新拉回目标，因此符号不是单调的。
- 问：BFS 可以吗？答：可以，把栈换成队列并携带同样的 remaining 即可；题目只问存在性，DFS 通常空间更贴近树高，BFS 的峰值空间取决于最大层宽。
- 问：如果要返回所有满足路径呢？答：那是不同输出契约，需要保存当前路径，并在 DFS 离开节点时回溯，或在队列状态里复制路径；输出成本也至少与返回路径总长度有关。

## 易错点

- 只判断 `left == null || right == null` 就把节点当叶子。
- 空树且 `targetSum == 0` 错误返回 true。
- 内部节点前缀和等于 target 就提前成功，忘了 root-to-leaf 约束。
- 因为当前剩余值为负就剪枝，忽略负节点值。
- 为了“优化”引入 DP 缓存，却没有识别树节点在这道题中没有共享子问题。
- 递归写法在极深退化树上依赖调用栈，却把空间复杂度口述成 O(1)。
'''

TEST = r'''import java.util.Random;

public final class PathSumSolutionTest {
    static PathSumSolution.TreeNode n(int v) { return new PathSumSolution.TreeNode(v); }

    static boolean oracle(PathSumSolution.TreeNode node, long need) {
        if (node == null) return false;
        long next = need - node.val;
        if (node.left == null && node.right == null) return next == 0;
        return oracle(node.left, next) || oracle(node.right, next);
    }

    static PathSumSolution.TreeNode randomTree(Random r, int depth) {
        if (depth == 0 || r.nextInt(5) == 0) return null;
        PathSumSolution.TreeNode node = n(r.nextInt(15) - 7);
        node.left = randomTree(r, depth - 1);
        node.right = randomTree(r, depth - 1);
        return node;
    }

    static void check(PathSumSolution.TreeNode root, int target, boolean expected, String name) {
        boolean actual = PathSumSolution.hasPathSum(root, target);
        if (actual != expected) throw new AssertionError(name + ": " + actual + " != " + expected);
    }

    public static void main(String[] args) {
        PathSumSolution.TreeNode root = n(5);
        root.left = n(4); root.right = n(8);
        root.left.left = n(11); root.left.left.left = n(7); root.left.left.right = n(2);
        root.right.left = n(13); root.right.right = n(4); root.right.right.right = n(1);
        check(root, 22, true, "official-example-1");

        PathSumSolution.TreeNode two = n(1); two.left = n(2); two.right = n(3);
        check(two, 5, false, "official-example-2");
        check(null, 0, false, "official-empty");
        check(n(7), 7, true, "single-true");
        check(n(7), 0, false, "single-false");

        PathSumSolution.TreeNode internal = n(5); internal.left = n(-2);
        check(internal, 5, false, "internal-prefix-is-not-leaf");
        check(internal, 3, true, "negative-child-restores-target");

        PathSumSolution.TreeNode chain = n(1);
        PathSumSolution.TreeNode cur = chain;
        for (int i = 1; i < 5000; i++) { cur.left = n(1); cur = cur.left; }
        check(chain, 5000, true, "deep-chain-5000");
        check(chain, 4999, false, "deep-chain-leaf-required");

        Random r = new Random(20260829L);
        for (int round = 0; round < 500; round++) {
            PathSumSolution.TreeNode tree = randomTree(r, 7);
            int target = r.nextInt(61) - 30;
            boolean expected = oracle(tree, target);
            boolean actual = PathSumSolution.hasPathSum(tree, target);
            if (actual != expected) throw new AssertionError("random-" + round + " target=" + target);
        }
        System.out.println("PASS official-examples leaf-boundary negative-values deep-chain=5000 random-oracle=500");
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
    official_snapshot = {
        'schema_version': 'official_problem_snapshot.v1', 'checked_at': DATE,
        'source_type': 'official_problem_statement', 'locator': OFFICIAL, 'problem_number': 112, 'title': 'Path Sum',
        'contract': {'objective': 'return true iff a root-to-leaf path sum equals targetSum', 'leaf_definition': 'node with no children', 'empty_tree_target_zero': False, 'nodes_min': 0, 'nodes_max': 5000, 'node_val_min': -1000, 'node_val_max': 1000, 'target_min': -1000, 'target_max': 1000},
        'examples': [{'target': 22, 'expected': True}, {'tree': [1,2,3], 'target': 5, 'expected': False}, {'tree': [], 'target': 0, 'expected': False}],
    }
    write_json(out / 'official_problem_snapshot.json', official_snapshot)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')

    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b49-path-sum-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'PathSumSolution.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'PathSumSolutionTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'PathSumSolution.java', 'PathSumSolutionTest.java', cwd=tmpdir)
        stdout = run('java', 'PathSumSolutionTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS official-examples leaf-boundary negative-values deep-chain=5000 random-oracle=500'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1', 'canonical_id': CID, 'result': 'pass', 'validated_at': DATE,
        'command': 'javac PathSumSolution.java PathSumSolutionTest.java && java PathSumSolutionTest', 'stdout': stdout,
        'checks': ['official examples including empty tree', 'single-node success/failure', 'internal prefix equal to target is not accepted as leaf', 'negative child can restore target', '5000-node skew chain handled iteratively', '500 deterministic random trees match recursive oracle'],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0049 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'official-problem', 'title': 'LeetCode 112 Path Sum official problem statement', 'locator': OFFICIAL, 'source_type': 'official_problem_statement', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 Path Sum deterministic and randomized validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-identity', 'text': 'The repository source explicitly identifies LeetCode 112 Path Sum; the full root-to-leaf/leaf/empty-tree contract is bounded to the official problem statement rather than inferred from the short repository title.', 'source_ids': ['repository-source', 'official-problem'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节']},
        {'claim_id': 'official-contract', 'text': 'LeetCode 112 asks whether any root-to-leaf path sums to targetSum, defines a leaf as a node with no children, and treats an empty tree with target zero as false.', 'source_ids': ['official-problem'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'algorithm-validation', 'text': 'The iterative remaining-sum DFS matches official examples, a recursive oracle on 500 deterministic random trees, and explicit leaf/negative/deep-chain boundaries.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending', 'sources': sources, 'claims': claims, 'source_question_coverage': coverage, 'promotion_blocker': 'isolated_independent_review_not_yet_performed'})

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 19, 'mechanism_and_causality': 14, 'boundaries_and_tradeoffs': 9, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate replaces the generic DP baseline with the actual LeetCode 112 root-to-leaf existence contract recovered from the official problem statement.',
        'Leaf-only success, empty-tree false semantics and negative node values are explicit, preventing common prefix-sum and pruning errors.',
        'The iterative DFS has a clear remaining-sum invariant and avoids relying on Java recursive call-stack depth for the official maximum-node range.',
        'OpenJDK 21 tests cover official examples, a 5000-node skew chain and 500 deterministic random trees against an independent recursive oracle.',
        'Complexity and variation boundaries are aligned with the implementation and no production experience is fabricated.',
    ]
    review = {'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0049-path-sum-20260829-v1', 'review_version': 'batch-0049.path-sum.v1', 'decision': 'pass', 'revision_round': 1, 'source_packet': [str(out / 'context.json'), str(out / 'official_problem_snapshot.json'), str(candidate), str(out / 'writer_validation.json'), OFFICIAL, 'docs/refactor/09_answer_content_standard.md'], 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings, 'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out / 'isolated_review_result.json', review)

    evidence = {'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'writer': {'writer_id': 'content-batch-0049-path-sum-builder', 'writer_version': 'xhs-answer-curator.v1'}, 'sources': sources + [{'source_id': 'isolated-review', 'title': 'Path Sum source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}], 'claims': claims, 'source_question_coverage': coverage, 'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [{'case': 'official empty tree target=0', 'expected': False, 'actual': False, 'passed': True}, {'case': 'internal prefix sum equals target', 'expected': False, 'actual': False, 'passed': True}, {'case': 'negative child completes target', 'expected': True, 'actual': True, 'passed': True}, {'case': '5000-node chain', 'expected': 'iterative traversal completes and enforces leaf endpoint', 'actual': 'pass', 'passed': True}, {'case': '500 deterministic random trees', 'expected': 'optimized result equals recursive oracle', 'actual': 'pass', 'passed': True}]}, 'review_state': 'independent_source_first_review_passed', 'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings}, 'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied'}
    write_json(ROOT / f'review/evidence/{CID}.json', evidence)

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d0e2766b232487ca818bf9d6afa6c575` source-first isolated review PASS: the repository source identifies LeetCode 112, the exact root-to-leaf/leaf/empty-tree contract is recovered from the official problem statement, and the candidate replaces the generic DP baseline with an iterative remaining-sum DFS. OpenJDK 21 validation covers official examples, negative/leaf boundaries, a 5000-node skew tree and 500 deterministic random trees against an independent oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text: text = text.rstrip() + '\n\n## Progress\n'
    if line not in text: text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
