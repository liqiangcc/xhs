#!/usr/bin/env python3
"""Build the source-bounded Batch 0062 binary-tree level-order candidate and executable evidence."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path('.')
BATCH = '0062'
DATE = '2026-08-31'
CID = 'cq_q_61d48051e02806afb811f793afd4a269'
QIDS = ['61d48051e02806afb811f793afd4a269', '94d7a2ec2a34272114ec07d269f5d497']
EXPECTED_WORDING = {
    '算法 1：手写实现二叉树的层序遍历',
    '算法：二叉树的层序遍历',
}
EXPECTED_STDOUT = 'PASS fixed=7 random=30000 oracle=dfs-depth null=empty duplicates=preserved levels=preserved'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_61d48051e02806afb811f793afd4a269","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 二叉树层序遍历：用队列按层冻结本轮节点数

## 核心结论

冻结来源只要求“手写二叉树的层序遍历/二叉树的层序遍历”，没有规定语言、节点结构、空树返回值或输出形状。这里声明一个可执行 Java 合同：节点值是 `int`，输入 `TreeNode root`，`null` 返回空列表，结果按“每层一个 `List<Integer>`”返回。核心做法是 BFS：根节点入队；每一轮先记录当前 `queue.size()`，这个大小就是本层尚未处理的节点数，只处理这批节点并把它们的非空子节点追加到队尾。这样下一轮队列中恰好是下一层节点。时间 O(n)，除返回结果外队列额外空间 O(w)，`w` 是树的最大宽度。

## 1 分钟版

- 层序遍历天然是 BFS：用 FIFO 队列保证先访问浅层节点，再访问深层节点。
- 根不为空就先入队；每轮开始保存 `levelSize = queue.size()`，它固定了这一层要消费多少个节点。
- 连续弹出 `levelSize` 个节点，把值写进当前层，并把非空 `left/right` 追加到队尾。
- 当前层处理完后再把这一层结果加入答案；队列里剩下的就是下一层，所以层边界不会混在一起。
- 每个节点入队、出队各一次，时间 O(n)；队列峰值 O(w)。

## 3 分钟版

下面代码对应“`null` 返回空列表、每层单独返回”的参考合同：

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public final class LevelOrderTraversal {
    public static final class TreeNode {
        public final int val;
        public TreeNode left;
        public TreeNode right;

        public TreeNode(int val) {
            this.val = val;
        }
    }

    private LevelOrderTraversal() {}

    public static List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) {
            return result;
        }

        Deque<TreeNode> queue = new ArrayDeque<>();
        queue.addLast(root);

        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            List<Integer> level = new ArrayList<>(levelSize);

            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.removeFirst();
                level.add(node.val);
                if (node.left != null) {
                    queue.addLast(node.left);
                }
                if (node.right != null) {
                    queue.addLast(node.right);
                }
            }
            result.add(level);
        }
        return result;
    }
}
```

例如树 `1 / \\ 2 3`，其中 `2` 的右子节点是 `4`，结果是 `[[1], [2, 3], [4]]`。关键点不是“用了队列”本身，而是**每轮先冻结旧队列大小**：本轮新增的孩子不能在同一轮继续消费，否则会把下一层混进当前层。

## 关键细节

- **输出合同**：来源没说只要扁平序列还是要保留层边界。本答案选择 `List<List<Integer>>`，因为这样能直接证明“按层”语义；如果只要 `[1,2,3,4]`，可以省掉 `levelSize` 分组，只按 FIFO 出队即可。
- **空树**：这里返回空列表，不返回 `null`；这是参考合同，不冒充原题约束。
- **为什么 `levelSize` 必须在 for 循环前保存**：循环过程中会不断把孩子加入队列，若每次都拿新的 `queue.size()` 当边界，当前层的消费上限会变化，层边界可能被破坏。
- **左右顺序**：代码先 `left` 后 `right` 入队，因此同一层保持从左到右。如果题目定义别的顺序，需要改变入队顺序。
- **重复值**：遍历的是节点，不是不同的值；两个节点值相同也必须分别输出，不能用 `Set` 去重。
- **`ArrayDeque` 与空节点**：这里只把非空子节点入队，因为 `ArrayDeque` 不允许 `null` 元素；空孩子不影响普通层序输出。
- **复杂度**：每个非空节点只入队/出队一次，因此时间 O(n)。队列最多同时保存某一层附近的节点，峰值 O(w)；返回结果本身需要 O(n) 空间。

## 原理机制

把树看成无权图，根节点深度为 0，每条父子边让深度加 1。FIFO 队列的性质是：当某一层开始处理时，队列前部正好是此前发现但尚未处理的最浅节点。冻结 `levelSize` 后，本轮只消费这些深度相同的节点；它们产生的孩子深度都多 1，并被追加在队尾，因此不会插到本层剩余节点之前。等本轮结束，原来的本层节点全部被移除，队列中就只剩下一层节点。这就是“按层”的不变量。

如果不用队列，也可以 DFS 时携带 `depth`，首次到达某个深度就创建对应列表，再把节点值放入该深度列表。DFS 能得到相同分层结果，但 BFS 与题目的“层序”访问顺序更直接，而且队列状态本身就表达了待处理层。

## 项目经验版

来源没有真实项目背景，不能虚构线上使用经历。面试手撕时我会先确认输出是否要保留层边界、节点定义是否已经给出、空树返回什么、同层是否要求从左到右；写完后用一个独立的“DFS + depth”实现做随机差分测试，并覆盖空树、单节点、只有左链/右链、稀疏树、重复值和宽树。这样验证的是遍历语义，而不是只拿一个样例对答案。

## 常见追问

- 问：为什么 BFS 一定按层？答：父节点先出队时只把孩子追加到队尾；同一深度中尚未处理的节点仍排在这些孩子前面，因此所有深度 d 的节点都会先于深度 d+1 的节点被消费。
- 问：为什么要先保存 `queue.size()`？答：这个值是“本轮开始时属于当前层的节点数”。处理过程中队列会增长，冻结大小才能阻止新加入的下一层节点被本轮消费。
- 问：如果只要求输出一个一维数组呢？答：仍然用 FIFO 队列，但不需要按 `levelSize` 分组；每次出队直接追加值即可。
- 问：可以递归做吗？答：可以 DFS 并传 `depth`，在 `result[depth]` 追加值；它的时间也是 O(n)，但额外有 O(h) 调用栈，极深树还要考虑递归栈风险。
- 问：最大空间为什么是 O(w)？答：BFS 在最宽层附近可能同时保存这一层未处理节点和下一层已发现节点，量级由最大宽度控制；若把返回结果算入则总空间至少 O(n)。
- 问：需要把 `null` 子节点也入队吗？答：普通层序遍历不需要；只有序列化/还原树形位置等任务才可能需要显式空占位符，那是另一个输出合同。

## 易错点

- 在 `for` 条件里动态读取不断变化的 `queue.size()`，把下一层节点提前消费。
- 处理节点后忘记把左右孩子入队，导致只输出根或部分节点。
- 为了“避免重复”使用 `Set`，错误丢掉值相同但身份不同的节点。
- 把 `null` 孩子直接塞进不接受 `null` 的 `ArrayDeque`。
- 没问清输出是一维 BFS 序列还是按层二维结构，就把某一种格式说成原题唯一要求。
- 只测完全二叉树，不测空树、单链、稀疏结构和重复节点值。
'''

JAVA = r'''import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public final class LevelOrderTraversal {
    public static final class TreeNode {
        public final int val;
        public TreeNode left;
        public TreeNode right;
        public TreeNode(int val) { this.val = val; }
    }
    private LevelOrderTraversal() {}
    public static List<List<Integer>> levelOrder(TreeNode root) {
        List<List<Integer>> result = new ArrayList<>();
        if (root == null) return result;
        Deque<TreeNode> queue = new ArrayDeque<>();
        queue.addLast(root);
        while (!queue.isEmpty()) {
            int levelSize = queue.size();
            List<Integer> level = new ArrayList<>(levelSize);
            for (int i = 0; i < levelSize; i++) {
                TreeNode node = queue.removeFirst();
                level.add(node.val);
                if (node.left != null) queue.addLast(node.left);
                if (node.right != null) queue.addLast(node.right);
            }
            result.add(level);
        }
        return result;
    }
}
'''

TEST = r'''import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class LevelOrderTraversalTest {
    private static final Random RNG = new Random(0x620061L);

    private static void assertEquals(Object expected, Object actual, String label) {
        if (!expected.equals(actual)) throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
    }

    private static List<List<Integer>> oracle(LevelOrderTraversal.TreeNode root) {
        List<List<Integer>> out = new ArrayList<>();
        dfs(root, 0, out);
        return out;
    }

    private static void dfs(LevelOrderTraversal.TreeNode node, int depth, List<List<Integer>> out) {
        if (node == null) return;
        if (out.size() == depth) out.add(new ArrayList<>());
        out.get(depth).add(node.val);
        dfs(node.left, depth + 1, out);
        dfs(node.right, depth + 1, out);
    }

    private static LevelOrderTraversal.TreeNode n(int value) { return new LevelOrderTraversal.TreeNode(value); }

    private static LevelOrderTraversal.TreeNode randomTree(int depth) {
        if (depth > 8 || (depth > 0 && RNG.nextInt(100) < 28)) return null;
        LevelOrderTraversal.TreeNode node = n(RNG.nextInt(11) - 5);
        node.left = randomTree(depth + 1);
        node.right = randomTree(depth + 1);
        return node;
    }

    public static void main(String[] args) {
        assertEquals(List.of(), LevelOrderTraversal.levelOrder(null), "null");
        assertEquals(List.of(List.of(7)), LevelOrderTraversal.levelOrder(n(7)), "single");

        LevelOrderTraversal.TreeNode balanced = n(1);
        balanced.left = n(2); balanced.right = n(3);
        balanced.left.left = n(4); balanced.left.right = n(5); balanced.right.right = n(6);
        assertEquals(List.of(List.of(1), List.of(2, 3), List.of(4, 5, 6)), LevelOrderTraversal.levelOrder(balanced), "balanced");

        LevelOrderTraversal.TreeNode left = n(1); left.left = n(2); left.left.left = n(3);
        assertEquals(List.of(List.of(1), List.of(2), List.of(3)), LevelOrderTraversal.levelOrder(left), "left-chain");

        LevelOrderTraversal.TreeNode right = n(1); right.right = n(2); right.right.right = n(3);
        assertEquals(List.of(List.of(1), List.of(2), List.of(3)), LevelOrderTraversal.levelOrder(right), "right-chain");

        LevelOrderTraversal.TreeNode sparse = n(9); sparse.left = n(8); sparse.right = n(7); sparse.left.right = n(6); sparse.right.left = n(5);
        assertEquals(List.of(List.of(9), List.of(8, 7), List.of(6, 5)), LevelOrderTraversal.levelOrder(sparse), "sparse-order");

        LevelOrderTraversal.TreeNode dup = n(1); dup.left = n(1); dup.right = n(1);
        assertEquals(List.of(List.of(1), List.of(1, 1)), LevelOrderTraversal.levelOrder(dup), "duplicates");

        for (int i = 0; i < 30000; i++) {
            LevelOrderTraversal.TreeNode root = randomTree(0);
            assertEquals(oracle(root), LevelOrderTraversal.levelOrder(root), "random-" + i);
        }
        System.out.println("PASS fixed=7 random=30000 oracle=dfs-depth null=empty duplicates=preserved levels=preserved");
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
        raise SystemExit('Batch 0062 source inventory is not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if item is None or item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: missing coding source packet')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: source ownership drift')
    if item.get('source_question_count') != 2 or item.get('source_occurrence_count') != 2:
        raise SystemExit(f'{CID}: expected 2 Questions / 2 occurrences')
    if {x.get('original_question') for x in item.get('source_questions', [])} != EXPECTED_WORDING:
        raise SystemExit(f'{CID}: source wording drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    context_path = out / 'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: frozen context drift')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate_path.parent.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(CANDIDATE, encoding='utf-8')
    (out / 'LevelOrderTraversal.java').write_text(JAVA, encoding='utf-8')
    (out / 'LevelOrderTraversalTest.java').write_text(TEST, encoding='utf-8')

    proc = subprocess.run(
        ['bash', '-lc', 'javac LevelOrderTraversal.java LevelOrderTraversalTest.java && java LevelOrderTraversalTest'],
        cwd=out,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout = proc.stdout.strip()
    if proc.returncode != 0 or stdout != EXPECTED_STDOUT:
        raise SystemExit(f'{CID}: executable validation failed rc={proc.returncode} stdout={stdout!r}')
    for class_file in out.glob('*.class'):
        class_file.unlink()

    checks = [
        'null tree returns an empty level list',
        'single-node tree preserves one level',
        'balanced and sparse trees preserve left-to-right level boundaries',
        'left-only and right-only chains preserve depth as separate levels',
        'duplicate values remain separate nodes rather than being deduplicated',
        '30,000 seeded random trees match an independent DFS-by-depth oracle',
    ]
    write_json(out / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac LevelOrderTraversal.java LevelOrderTraversalTest.java && java LevelOrderTraversalTest',
        'stdout': stdout,
        'checks': checks,
    })
    write_json(out / 'writer_research.json', {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': [
            {
                'source_id': 'repository-source',
                'title': 'Batch 0062 frozen repository source context for binary-tree level-order traversal',
                'locator': str(context_path),
                'source_type': 'repository_source_record',
                'checked_at': DATE,
            },
            {
                'source_id': 'source-inventory',
                'title': 'Batch 0062 occurrence-aware frozen source inventory',
                'locator': str(inventory_path),
                'source_type': 'repository_structured_source',
                'checked_at': DATE,
            },
            {
                'source_id': 'fixture',
                'title': 'Deterministic and differential OpenJDK validation for level-order traversal',
                'locator': str(out / 'writer_validation.json'),
                'source_type': 'executable_test_or_reproducible_experiment',
                'checked_at': DATE,
            },
        ],
        'claims': [
            {
                'claim_id': 'source-boundary',
                'text': 'The two preserved source Questions ask for binary-tree level-order traversal but do not preserve a language, node schema, null policy or required output shape; those are declared as reference-contract choices.',
                'source_ids': ['repository-source', 'source-inventory'],
                'answer_locations': ['核心结论', '关键细节', '项目经验版'],
            },
            {
                'claim_id': 'reference-behavior',
                'text': 'Under the declared Java TreeNode/List<List<Integer>> contract, the queue implementation preserves level boundaries and left-to-right order and matches an independently implemented DFS-by-depth oracle across fixed boundaries and 30,000 seeded random trees.',
                'source_ids': ['fixture'],
                'answer_locations': ['1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
            },
        ],
        'source_question_coverage': [
            {'question_id': qid, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}
            for qid in QIDS
        ],
        'source_occurrence_count': 2,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8').rstrip()
    marker = (
        f'- [x] `{CID}` writer stage complete: both frozen level-order source Questions are covered by an explicit Java BFS contract; '
        'the executable fixture validates null/single/balanced/sparse/chain/duplicate-value boundaries and 30,000 seeded random trees against an independent DFS-by-depth oracle. '
        'Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    )
    if marker not in text:
        text += '\n\n## Progress\n\n' + marker if '## Progress' not in text else '\n' + marker
        task.write_text(text + '\n', encoding='utf-8')

    print(stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
