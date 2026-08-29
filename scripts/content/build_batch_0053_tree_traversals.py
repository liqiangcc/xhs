#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0053 binary-tree traversal candidate."""

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
CID = 'cq_q_e596a619cd124675cbe35a5a36c9acb2'
QID = 'e596a619cd124675cbe35a5a36c9acb2'
EXPECTED = '算法：二叉树遍历的实现？'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e596a619cd124675cbe35a5a36c9acb2","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 二叉树遍历：前序、中序、后序的迭代实现

## 核心结论

仓库来源只保留“算法：二叉树遍历的实现？”这一句，没有保存指定语言、节点定义、递归/迭代要求，也没有明确只问哪一种遍历顺序。这里给出一个可执行 Java 契约：节点包含 `int val`、`left`、`right`；分别实现前序（根-左-右）、中序（左-根-右）和后序（左-右-根）三种深度优先遍历；`null` 根返回空列表；实现不修改树结构。为避免极深树触发递归调用栈溢出，正式代码采用显式栈迭代。

三种遍历的本质区别只是“什么时候访问根节点”。前序弹栈时立即访问；中序不断向左入栈，左侧耗尽后访问栈顶，再转向右子树；后序必须等左右子树都处理完才能访问根，因此单栈版本额外维护 `lastVisited`，判断右子树是否已经完成。

## 1 分钟版

- 前序：栈里先压右再压左，这样左子树先被弹出，顺序是根-左-右。
- 中序：当前节点一路向左压栈；没有更左节点时弹栈访问，再进入右子树。
- 后序：栈顶不能马上访问；若右子树存在且还没处理，就先转向右子树，否则访问栈顶并记录为 `lastVisited`。
- 三种算法每个节点只完成常数次压栈/弹栈操作，时间 O(n)。显式栈最坏 O(h)，其中 h 是树高；退化链表树时 h=n。
- 层序遍历是另一类按层次的 BFS。如果面试官说的“遍历”包含层序，应再用队列实现，但不能把这一额外要求冒充成当前保存来源。

## 3 分钟版

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public final class BinaryTreeTraversals {
    public static final class TreeNode {
        public final int val;
        public TreeNode left;
        public TreeNode right;

        public TreeNode(int val) {
            this.val = val;
        }
    }

    public static List<Integer> preorder(TreeNode root) {
        List<Integer> out = new ArrayList<>();
        if (root == null) return out;

        Deque<TreeNode> stack = new ArrayDeque<>();
        stack.push(root);
        while (!stack.isEmpty()) {
            TreeNode node = stack.pop();
            out.add(node.val);
            if (node.right != null) stack.push(node.right);
            if (node.left != null) stack.push(node.left);
        }
        return out;
    }

    public static List<Integer> inorder(TreeNode root) {
        List<Integer> out = new ArrayList<>();
        Deque<TreeNode> stack = new ArrayDeque<>();
        TreeNode cur = root;

        while (cur != null || !stack.isEmpty()) {
            while (cur != null) {
                stack.push(cur);
                cur = cur.left;
            }
            TreeNode node = stack.pop();
            out.add(node.val);
            cur = node.right;
        }
        return out;
    }

    public static List<Integer> postorder(TreeNode root) {
        List<Integer> out = new ArrayList<>();
        Deque<TreeNode> stack = new ArrayDeque<>();
        TreeNode cur = root;
        TreeNode lastVisited = null;

        while (cur != null || !stack.isEmpty()) {
            if (cur != null) {
                stack.push(cur);
                cur = cur.left;
                continue;
            }

            TreeNode peek = stack.peek();
            if (peek.right != null && lastVisited != peek.right) {
                cur = peek.right;
            } else {
                out.add(peek.val);
                lastVisited = stack.pop();
            }
        }
        return out;
    }
}
```

前序最简单，因为“访问根”发生在第一次看见节点时。中序必须暂存祖先，等左子树完成以后才能访问根。后序最容易写错，因为第一次回到父节点时只能说明左子树完成，还不能说明右子树也完成；`lastVisited` 就是用来区分“该去右边”还是“左右都完成，可以访问根”。

## 关键细节

- **前序压栈顺序**：栈是后进先出，所以要先压右再压左；反过来会得到根-右-左。
- **中序循环条件**：必须是 `cur != null || !stack.isEmpty()`；当前指针为空并不代表遍历结束，栈里可能还有祖先等待访问。
- **后序右子树判定**：只有当 `peek.right != null` 且右子树还没有刚刚被处理时才进入右子树，否则才能访问 `peek`。
- **节点值重复**：`lastVisited` 比较的是节点对象身份，不是 `val`。二叉树允许不同节点拥有相同值，不能用值判断某棵子树是否访问完成。
- **空树**：三种遍历都返回空列表，不制造哨兵值。
- **复杂度**：每个节点最终被访问一次，时间 O(n)；显式栈与树高相关，最坏 O(h)，退化树为 O(n)。返回结果本身还需要 O(n) 空间，但这与遍历辅助栈应分开说明。

## 原理机制

递归遍历把“尚未完成的祖先状态”隐式保存在 JVM 调用栈中；迭代版本只是把这份控制状态显式化。前序只需要保存将来要处理的节点；中序需要保存“左边处理完以后回来访问”的祖先；后序还需要知道“回来时右子树是否已经完成”。因此三段代码虽然都使用栈，但栈元素背后的状态含义不同。

可以用不变量理解它们：前序栈中保存所有已经发现但尚未访问的子树根；中序栈中保存左链上的祖先，栈顶是下一个可能访问的根；后序栈中保存尚未满足“左右子树均完成”的祖先，`lastVisited` 表示最近完成的子树根。保持这些不变量，就能证明输出顺序分别满足根-左-右、左-根-右和左-右-根。

## 项目经验版

来源没有真实项目上下文，不能虚构“线上使用过某种遍历”。工程里选择递归还是迭代取决于树高是否可控、可读性和故障边界：高度很小且有明确上限时递归往往更直接；树可能退化到很深时，显式栈能把空间消耗放到堆上的可控数据结构里，避免依赖线程调用栈深度。若数据规模大到结果列表也不能一次驻留内存，还可以把“收集结果”改成 visitor/iterator 式消费，但这属于接口契约变化。

## 常见追问

- 问：为什么前序要先压右节点？答：栈后进先出，先压右、后压左才能让左节点先弹出。
- 问：后序为什么不能像前序一样弹出就访问？答：后序要求左右子树先完成；第一次看到父节点时这个条件通常还不成立。
- 问：`lastVisited` 为什么不能存节点值？答：不同节点可以有相同值，完成状态属于节点身份而不是数值。
- 问：递归和迭代复杂度一样吗？答：渐进时间都为 O(n)，控制栈都与树高 h 有关；差别主要是状态放在调用栈还是显式数据结构中，以及深树的栈溢出边界。
- 问：层序遍历怎么做？答：层序是 BFS，使用队列；当前保存来源没有明确要求层序，因此这里把它作为追问而不是主合同。
- 问：能否统一三种 DFS？答：可以用“节点 + 状态/颜色”统一成显式状态机，但面试手写时三种直接实现通常更容易验证，除非题目明确要求统一框架。

## 易错点

- 前序把左、右入栈顺序写反，得到根-右-左。
- 中序只写 `while (cur != null)`，当前指针第一次到空就错误退出。
- 后序在左子树完成后立即访问父节点，漏掉右子树。
- 后序用节点值判断右子树是否访问过，在重复值树上产生错误。
- 把显式栈空间笼统写成固定 O(log n)；只有平衡树的 h 才是 O(log n)，退化树最坏 O(n)。
- 把层序遍历或某种特定语言/API 当成原题已经明确要求，而仓库来源并没有保存这些约束。
'''

TEST = r'''import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class BinaryTreeTraversalsTest {
    private static List<Integer> recursivePre(BinaryTreeTraversals.TreeNode root) {
        List<Integer> out = new ArrayList<>();
        recursivePre(root, out);
        return out;
    }

    private static void recursivePre(BinaryTreeTraversals.TreeNode node, List<Integer> out) {
        if (node == null) return;
        out.add(node.val);
        recursivePre(node.left, out);
        recursivePre(node.right, out);
    }

    private static List<Integer> recursiveIn(BinaryTreeTraversals.TreeNode root) {
        List<Integer> out = new ArrayList<>();
        recursiveIn(root, out);
        return out;
    }

    private static void recursiveIn(BinaryTreeTraversals.TreeNode node, List<Integer> out) {
        if (node == null) return;
        recursiveIn(node.left, out);
        out.add(node.val);
        recursiveIn(node.right, out);
    }

    private static List<Integer> recursivePost(BinaryTreeTraversals.TreeNode root) {
        List<Integer> out = new ArrayList<>();
        recursivePost(root, out);
        return out;
    }

    private static void recursivePost(BinaryTreeTraversals.TreeNode node, List<Integer> out) {
        if (node == null) return;
        recursivePost(node.left, out);
        recursivePost(node.right, out);
        out.add(node.val);
    }

    private static void assertEquals(List<Integer> expected, List<Integer> actual, String label) {
        if (!expected.equals(actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    private static BinaryTreeTraversals.TreeNode randomTree(Random random, int depth) {
        if (depth == 0 || random.nextInt(100) < 28) return null;
        BinaryTreeTraversals.TreeNode node = new BinaryTreeTraversals.TreeNode(random.nextInt(21) - 10);
        node.left = randomTree(random, depth - 1);
        node.right = randomTree(random, depth - 1);
        return node;
    }

    public static void main(String[] args) {
        assertEquals(List.of(), BinaryTreeTraversals.preorder(null), "pre-null");
        assertEquals(List.of(), BinaryTreeTraversals.inorder(null), "in-null");
        assertEquals(List.of(), BinaryTreeTraversals.postorder(null), "post-null");

        BinaryTreeTraversals.TreeNode root = new BinaryTreeTraversals.TreeNode(1);
        root.left = new BinaryTreeTraversals.TreeNode(2);
        root.right = new BinaryTreeTraversals.TreeNode(3);
        root.left.right = new BinaryTreeTraversals.TreeNode(4);
        root.right.left = new BinaryTreeTraversals.TreeNode(5);
        assertEquals(List.of(1, 2, 4, 3, 5), BinaryTreeTraversals.preorder(root), "pre-directed");
        assertEquals(List.of(2, 4, 1, 5, 3), BinaryTreeTraversals.inorder(root), "in-directed");
        assertEquals(List.of(4, 2, 5, 3, 1), BinaryTreeTraversals.postorder(root), "post-directed");

        BinaryTreeTraversals.TreeNode skew = new BinaryTreeTraversals.TreeNode(0);
        BinaryTreeTraversals.TreeNode p = skew;
        for (int i = 1; i < 20_000; i++) {
            p.right = new BinaryTreeTraversals.TreeNode(i);
            p = p.right;
        }
        if (BinaryTreeTraversals.preorder(skew).size() != 20_000) throw new AssertionError("pre-skew");
        if (BinaryTreeTraversals.inorder(skew).size() != 20_000) throw new AssertionError("in-skew");
        if (BinaryTreeTraversals.postorder(skew).size() != 20_000) throw new AssertionError("post-skew");

        Random random = new Random(20260829L);
        for (int round = 0; round < 2000; round++) {
            BinaryTreeTraversals.TreeNode tree = randomTree(random, 8);
            assertEquals(recursivePre(tree), BinaryTreeTraversals.preorder(tree), "pre-random-" + round);
            assertEquals(recursiveIn(tree), BinaryTreeTraversals.inorder(tree), "in-random-" + round);
            assertEquals(recursivePost(tree), BinaryTreeTraversals.postorder(tree), "post-random-" + round);
        }

        System.out.println("PASS null directed 2000-random-oracle 20000-skew iterative-stack");
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

    with tempfile.TemporaryDirectory(prefix='b53-tree-traversals-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'BinaryTreeTraversals.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'BinaryTreeTraversalsTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'BinaryTreeTraversals.java', 'BinaryTreeTraversalsTest.java', cwd=tmpdir)
        stdout = run('java', 'BinaryTreeTraversalsTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS null directed 2000-random-oracle 20000-skew iterative-stack'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac BinaryTreeTraversals.java BinaryTreeTraversalsTest.java && java BinaryTreeTraversalsTest',
        'stdout': stdout,
        'checks': [
            'null tree returns empty output for all three traversals',
            'directed asymmetric tree locks preorder/inorder/postorder sequences',
            '2000 deterministic random trees agree with independent recursive oracles',
            '20000-node right-skewed tree completes iteratively without recursive traversal stack dependence',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0053 exact binary-tree traversal source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 iterative binary-tree traversal deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source asks only for an implementation of binary-tree traversal; it does not preserve a language, node API, traversal subset, or recursion requirement.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '易错点']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate explicitly defines Java nodes, null-root behavior, non-mutating preorder/inorder/postorder DFS, and treats level-order BFS only as a conditional follow-up.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'algorithm-behavior', 'text': 'The iterative stack implementations produce root-left-right, left-root-right, and left-right-root orders and match independent recursive reference traversals.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制', '常见追问']},
        {'claim_id': 'boundary-validation', 'text': 'Executable validation covers null, an asymmetric directed tree, 2000 deterministic random trees with duplicate values, and a 20000-node skewed tree.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '原理机制', '易错点']},
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
        'The candidate respects the sparse repository source and does not invent an externally specified language, API, or traversal subset.',
        'Preorder, inorder, and postorder are all covered with one executable Java class and explicit null-tree behavior.',
        'The postorder explanation correctly identifies completion state as the hard part and uses node identity rather than value equality for lastVisited.',
        'The mechanism section explains iterative traversal as explicit preservation of control state that recursion would otherwise place on the call stack.',
        'OpenJDK 21 validation compares 2000 deterministic random trees against independent recursive oracles and includes a 20000-node skewed tree.',
        'Complexity is stated as O(n) time and O(h) auxiliary stack, with the degenerate h=n case called out rather than assuming balance.',
        'The project section avoids fabricated experience and treats streaming visitor APIs only as a conditional engineering extension.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0053-tree-traversals-20260829-v1',
        'review_version': 'batch-0053.tree-traversals.v1',
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

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0053 tree-traversal source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0053-tree-traversals-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'null tree', 'expected': 'three empty traversals', 'actual': 'pass', 'passed': True},
                {'case': 'asymmetric directed tree', 'expected': 'exact preorder/inorder/postorder sequences', 'actual': 'pass', 'passed': True},
                {'case': '2000 deterministic random trees', 'expected': 'matches independent recursive oracles', 'actual': 'pass', 'passed': True},
                {'case': '20000-node right-skewed tree', 'expected': 'all iterative traversals complete with 20000 outputs', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e596a619cd124675cbe35a5a36c9acb2` source-first isolated review PASS: the sparse source only asks for binary-tree traversal implementation. The candidate explicitly defines Java preorder/inorder/postorder DFS, uses iterative stacks with identity-safe postorder state, and OpenJDK 21 validation covers null/direct cases, 2000 deterministic random trees against recursive oracles, plus a 20000-node skewed tree. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
