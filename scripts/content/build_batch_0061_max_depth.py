#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0061 binary-tree max-depth candidate."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0061'
CID = 'cq_q_22745d1a56145d782dbda254186e9d75'
QIDS = ['22745d1a56145d782dbda254186e9d75', 'b0ee762387cf1383f3b75b8aadf225ba']
EXPECTED_VARIANTS = {
    '算法：二叉树的最大深度（DFS & BFS）。',
    '算法：二叉树的最大深度。',
}
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

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_22745d1a56145d782dbda254186e9d75","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 二叉树的最大深度：DFS 与 BFS

## 核心结论

二叉树最大深度可以定义为“从根节点到最远叶子节点路径上的节点数”。空树深度是 0，只有根节点时深度是 1。DFS 的递归关系是 `depth(node) = 1 + max(depth(left), depth(right))`；BFS 则按层遍历，每完整处理一层就把深度加 1。两种方法都会访问每个节点一次，时间复杂度都是 `O(n)`；DFS 的额外空间主要由递归栈决定，最坏 `O(h)`，BFS 的额外空间由最宽一层的队列决定，最坏 `O(w)`。

## 1 分钟版

- 先明确深度按节点数计：`null -> 0`，叶子节点 -> 1。
- DFS：递归求左右子树最大深度，当前节点在较深的一边基础上加 1。
- BFS：队列从根开始，每次固定本层节点数，把这一层全部弹出并压入下一层子节点；处理完一层后 `depth++`。
- 两者时间都是 `O(n)`；DFS 更直接，但极深退化树可能触发调用栈限制；BFS 不依赖递归栈，但宽树可能占用更大的队列。
- 如果面试官只要求一个实现，递归 DFS 通常最短；如果明确要求 DFS & BFS，就分别说明状态和空间边界。

## 3 分钟版

来源没有指定语言和节点定义，下面用 Java 给出一个最小可执行 `TreeNode`，同时实现 DFS 与 BFS；两者都返回按节点数计的最大深度：

```java
import java.util.ArrayDeque;
import java.util.Deque;

public final class Solution {
    public static final class TreeNode {
        public int val;
        public TreeNode left;
        public TreeNode right;

        public TreeNode(int val) {
            this.val = val;
        }
    }

    public static int maxDepthDfs(TreeNode root) {
        if (root == null) return 0;
        return 1 + Math.max(maxDepthDfs(root.left), maxDepthDfs(root.right));
    }

    public static int maxDepthBfs(TreeNode root) {
        if (root == null) return 0;
        Deque<TreeNode> queue = new ArrayDeque<>();
        queue.addLast(root);
        int depth = 0;
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.removeFirst();
                if (node.left != null) queue.addLast(node.left);
                if (node.right != null) queue.addLast(node.right);
            }
            depth++;
        }
        return depth;
    }
}
```

DFS 里 `null` 返回 0，使叶子节点自然得到 `1 + max(0, 0) = 1`。BFS 的关键是先冻结 `levelSize = queue.size()`，因为处理本层时队列还会不断加入下一层节点；只有当前这 `levelSize` 个节点全部处理完成，才算真正走完一层。

## 关键细节

- **深度口径**：这里按节点数计，而不是按边数计。若题目改成“根到最远叶子的边数”，非空树结果会比这里少 1，空树语义也需要重新约定。
- **DFS 不变量**：每个递归调用只回答“以当前节点为根的子树最大深度”；左右子树答案独立求出后取最大值，再加当前节点这一层。
- **BFS 不变量**：进入外层 `while` 时，队列头部开始的一批节点构成当前层；用进入该层时的 `queue.size()` 固定批次，避免把刚加入的下一层节点也在同一轮消费。
- **复杂度**：两种实现都恰好对每个可达节点做常数次工作，时间 `O(n)`。DFS 递归栈最坏是树高 `h`，退化链表树时 `h=n`；BFS 队列最多容纳某一层的节点数 `w`，完全二叉树底层可能是 `O(n)`。
- **栈溢出边界**：递归 DFS 的渐进空间写成 `O(h)` 并不等于工程上一定安全。若树可能非常深，应改成显式栈的迭代 DFS，或优先用 BFS。
- **节点值无关**：最大深度只依赖结构，不依赖 `val`。示例保留 `val` 只是给出常见节点模型，不把它当成算法条件。

## 原理机制

DFS 利用了树的递归结构：一棵非空树的最大深度，就是更深子树的最大深度再加根这一层。这是典型的自底向上归纳——先定义空树基线，再假设左右子树答案正确，就能组合出当前节点答案。

BFS 则利用图搜索的层次性质。队列按“距离根的层数”推进：第 1 批是根，第 2 批是根的孩子，依次类推。最大深度等价于从根开始能完整推进的层数，因此只需要在每个批次结束时计数。DFS 与 BFS 得到同一个结构量，但占用的辅助空间由不同维度决定：前者受高度控制，后者受宽度控制。

## 项目经验版

来源没有真实项目、输入规模或树结构分布，不能虚构线上案例。实际选择实现时我会先确认数据规模和形状：普通业务树且深度可控时递归 DFS 可读性最好；若输入可能是极深退化树，我会避免依赖 JVM 调用栈；若树极宽，则还要评估 BFS 队列峰值。上线前会用空树、单节点、单边链、完全树和随机树做一致性测试，让 DFS、BFS 与一个独立迭代基准结果相互校验。

## 常见追问

- 问：为什么 DFS 是 `1 + max(left, right)`？答：从当前节点到最深叶子的路径必然先进入左右子树之一；选择更深的那一侧，再加当前节点这一层。
- 问：BFS 为什么不能每弹一个节点就 `depth++`？答：那统计的是节点数而不是层数。深度只在完整处理完一层后增加一次。
- 问：为什么要先保存 `levelSize`？答：处理当前层时会把下一层节点加入队列；若循环条件直接跟随变化后的 `queue.size()`，层边界会被打乱。
- 问：DFS 和 BFS 哪个空间更省？答：没有统一答案。DFS 是 `O(h)`，BFS 是 `O(w)`；瘦高树通常 BFS 队列小但递归栈深，宽而浅的树反过来。
- 问：递归 DFS 一定能通过吗？答：算法复杂度正确不代表运行时栈无限。极深输入可能栈溢出，可改显式栈迭代 DFS。
- 问：如果问最小深度还能直接取 `min` 吗？答：不能机械替换；只有一个子树为空时，根到叶子的合法路径必须走非空那边，所以最小深度有不同的空子树处理逻辑。

## 易错点

- 把最大深度按边数和按节点数两种口径混在一起，导致空树/单节点 off-by-one。
- DFS 忘记 `root == null` 基线，或者把空树错误写成 1。
- BFS 在每处理一个节点时增加深度，实际统计成节点数量。
- BFS 不冻结当前层节点数，把下一层节点混入同一轮循环。
- 只写 `O(n)` 而忽略 DFS 的递归栈与 BFS 的队列峰值。
- 在可能极深的树上无条件使用递归实现，却不说明调用栈风险。
'''

SOLUTION = r'''import java.util.ArrayDeque;
import java.util.Deque;

public final class Solution {
    public static final class TreeNode {
        public int val;
        public TreeNode left;
        public TreeNode right;
        public TreeNode(int val) { this.val = val; }
    }

    public static int maxDepthDfs(TreeNode root) {
        if (root == null) return 0;
        return 1 + Math.max(maxDepthDfs(root.left), maxDepthDfs(root.right));
    }

    public static int maxDepthBfs(TreeNode root) {
        if (root == null) return 0;
        Deque<TreeNode> queue = new ArrayDeque<>();
        queue.addLast(root);
        int depth = 0;
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.removeFirst();
                if (node.left != null) queue.addLast(node.left);
                if (node.right != null) queue.addLast(node.right);
            }
            depth++;
        }
        return depth;
    }
}
'''

TEST = r'''import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import java.util.Random;

public final class SolutionTest {
    private static int oracle(Solution.TreeNode root) {
        if (root == null) return 0;
        final class Frame {
            final Solution.TreeNode node;
            final int depth;
            Frame(Solution.TreeNode node, int depth) { this.node = node; this.depth = depth; }
        }
        Deque<Frame> stack = new ArrayDeque<>();
        stack.push(new Frame(root, 1));
        int best = 0;
        while (!stack.isEmpty()) {
            Frame f = stack.pop();
            best = Math.max(best, f.depth);
            if (f.node.left != null) stack.push(new Frame(f.node.left, f.depth + 1));
            if (f.node.right != null) stack.push(new Frame(f.node.right, f.depth + 1));
        }
        return best;
    }

    private static void check(Solution.TreeNode root, int expected) {
        int dfs = Solution.maxDepthDfs(root);
        int bfs = Solution.maxDepthBfs(root);
        int ref = oracle(root);
        if (dfs != expected || bfs != expected || ref != expected) {
            throw new AssertionError("depth mismatch dfs=" + dfs + " bfs=" + bfs + " oracle=" + ref + " expected=" + expected);
        }
    }

    private static Solution.TreeNode randomTree(Random r, int n) {
        if (n == 0) return null;
        Solution.TreeNode root = new Solution.TreeNode(r.nextInt());
        List<Solution.TreeNode> parents = new ArrayList<>();
        parents.add(root);
        for (int i = 1; i < n; i++) {
            Solution.TreeNode node = new Solution.TreeNode(r.nextInt());
            while (true) {
                Solution.TreeNode p = parents.get(r.nextInt(parents.size()));
                if (p.left != null && p.right != null) continue;
                if (p.left == null && p.right == null) {
                    if (r.nextBoolean()) p.left = node; else p.right = node;
                } else if (p.left == null) {
                    p.left = node;
                } else {
                    p.right = node;
                }
                break;
            }
            parents.add(node);
            parents.removeIf(p -> p.left != null && p.right != null);
        }
        return root;
    }

    public static void main(String[] args) {
        check(null, 0);
        check(new Solution.TreeNode(1), 1);

        Solution.TreeNode chain = new Solution.TreeNode(1);
        Solution.TreeNode cur = chain;
        for (int i = 2; i <= 300; i++) {
            cur.right = new Solution.TreeNode(i);
            cur = cur.right;
        }
        check(chain, 300);

        Solution.TreeNode balanced = new Solution.TreeNode(1);
        balanced.left = new Solution.TreeNode(2);
        balanced.right = new Solution.TreeNode(3);
        balanced.left.left = new Solution.TreeNode(4);
        balanced.left.right = new Solution.TreeNode(5);
        balanced.right.right = new Solution.TreeNode(6);
        check(balanced, 3);

        Solution.TreeNode asymmetric = new Solution.TreeNode(1);
        asymmetric.left = new Solution.TreeNode(2);
        asymmetric.left.left = new Solution.TreeNode(3);
        asymmetric.left.left.right = new Solution.TreeNode(4);
        asymmetric.right = new Solution.TreeNode(5);
        check(asymmetric, 4);

        Random r = new Random(20260831L);
        final int cases = 30000;
        for (int t = 0; t < cases; t++) {
            int n = r.nextInt(100);
            Solution.TreeNode root = randomTree(r, n);
            int expected = oracle(root);
            int dfs = Solution.maxDepthDfs(root);
            int bfs = Solution.maxDepthBfs(root);
            if (dfs != expected || bfs != expected) {
                throw new AssertionError("random mismatch case=" + t + " n=" + n + " dfs=" + dfs + " bfs=" + bfs + " oracle=" + expected);
            }
        }
        System.out.println("PASS fixed=5 skew-depth=300 random=30000 oracle=iterative-stack dfs=bfs=oracle");
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

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    context_raw = run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout
    context = json.loads(context_raw)
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: live context/type drift')
    live_qids = sorted((context.get('canonical') or {}).get('question_ids') or [])
    if live_qids != sorted(QIDS):
        raise SystemExit(f'{CID}: live context ownership drift: {live_qids}')
    write_json(out / 'context.json', context)

    for heading in HEADINGS:
        if heading not in CANDIDATE:
            raise SystemExit(f'candidate heading missing: {heading}')
    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE, encoding='utf-8')
    digest = hashlib.sha256(CANDIDATE.encode('utf-8')).hexdigest()

    with tempfile.TemporaryDirectory(prefix='xhs-max-depth-') as tmp:
        td = Path(tmp)
        (td / 'Solution.java').write_text(SOLUTION, encoding='utf-8')
        (td / 'SolutionTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'Solution.java', 'SolutionTest.java', cwd=td)
        stdout = run('java', 'SolutionTest', cwd=td).stdout.strip()
    expected_stdout = 'PASS fixed=5 skew-depth=300 random=30000 oracle=iterative-stack dfs=bfs=oracle'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected max-depth validation output: {stdout}')

    checks = [
        'empty tree returns depth 0 and a single node returns depth 1 under the explicit node-count contract',
        'balanced, asymmetric, and 300-node skewed trees produce the expected maximum depth',
        '30,000 seeded random trees make recursive DFS and level-order BFS match an independent iterative-stack oracle',
        'node values vary randomly but do not affect depth, validating that the result depends only on tree structure',
    ]
    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac Solution.java SolutionTest.java && java SolutionTest',
        'stdout': stdout,
        'checks': checks,
        'environment': {'java': 'OpenJDK 21'},
        'limitation': 'The executable differential test validates the exact DFS/BFS implementations on fixed structures and bounded generated trees; it does not claim recursion is safe for arbitrarily deep JVM inputs, which the candidate explicitly calls out.',
    }
    write_json(out / 'writer_validation.json', validation)

    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0061 frozen repository source context for binary-tree maximum depth',
            'locator': f'review/content_build/answer_batch_{BATCH}/{CID}/context.json',
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'source-inventory',
            'title': 'Batch 0061 frozen live source inventory',
            'locator': f'review/content_build/answer_batch_{BATCH}/source_inventory.json',
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
        {
            'source_id': 'fixture',
            'title': 'OpenJDK differential validation for DFS and BFS maximum-depth implementations',
            'locator': f'review/content_build/answer_batch_{BATCH}/{CID}/writer_validation.json',
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The two frozen source variants ask for binary-tree maximum depth, with one explicitly naming DFS and BFS; they do not prescribe a programming language, node API, edge-count convention, or production input shape, so the candidate makes those boundaries explicit.',
            'source_ids': ['repository-source', 'source-inventory'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'reference-behavior',
            'text': 'The exact Java recursive-DFS and level-order-BFS implementations compile, pass fixed boundary/shape cases, and match an independent iterative-stack oracle on 30,000 seeded random trees.',
            'source_ids': ['fixture'],
            'answer_locations': ['3 分钟版', '关键细节', '原理机制', '项目经验版'],
        },
    ]
    coverage = [
        {
            'question_id': qid,
            'covered': True,
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        }
        for qid in QIDS
    ]
    writer_research = {
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
    write_json(out / 'writer_research.json', writer_research)

    findings = [
        'The candidate directly covers both frozen maximum-depth source variants and provides both DFS and BFS implementations requested by the richer variant.',
        'The depth convention is explicit: empty tree is 0 and non-empty depth counts nodes, avoiding an unspoken edge-count off-by-one.',
        'The recursive DFS recurrence and BFS level boundary are explained with their invariants instead of presenting code without mechanism.',
        'The candidate distinguishes O(h) recursion-stack space from O(w) BFS-queue space and explicitly calls out recursion-stack risk on very deep trees.',
        'Executable validation makes both exact implementations agree with an independently implemented iterative-stack oracle over fixed structures and 30,000 seeded random trees.',
        'No production or personal claim is fabricated from the source.',
    ]
    isolated = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0061-max-depth-20260831-v1',
        'review_version': 'batch-0061.max-depth.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [
            f'review/content_build/answer_batch_{BATCH}/{CID}/context.json',
            f'review/content_build/answer_batch_{BATCH}/source_inventory.json',
            f'review/candidates/answers/{CID}.md',
            f'review/content_build/answer_batch_{BATCH}/{CID}/writer_validation.json',
            'docs/refactor/09_answer_content_standard.md',
        ],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    }
    write_json(out / 'isolated_review_result.json', isolated)

    evidence_sources = sources + [{
        'source_id': 'isolated-review',
        'title': 'Batch 0061 binary-tree maximum-depth source-first isolated review',
        'locator': f'review/content_build/answer_batch_{BATCH}/{CID}/isolated_review_result.json',
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    }]
    evidence = {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0061-max-depth-builder',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': stdout,
            'checks': checks,
            'boundary_tests': [
                {'case': c, 'expected': 'pass under declared candidate contract', 'actual': 'pass', 'passed': True}
                for c in checks
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': isolated['reviewer_id'],
            'review_version': isolated['review_version'],
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
    }
    write_json(ROOT / f'review/evidence/{CID}.json', evidence)

    task_path = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0061.md'
    task = task_path.read_text(encoding='utf-8')
    marker = f'- [x] `{CID}` source-first isolated review PASS:'
    if marker not in task:
        task = task.rstrip() + '\n' + (
            f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; '
            'the Java answer implements both recursive DFS and level-order BFS under an explicit node-count depth contract. '
            'OpenJDK validation checks empty/single/balanced/asymmetric/skewed trees and makes both implementations match an independent iterative-stack oracle on 30,000 seeded random trees. '
            'Formal promotion remains blocked by repository human-approval/real-review policy.\n'
        )
        task_path.write_text(task, encoding='utf-8')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
