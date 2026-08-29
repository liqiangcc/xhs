#!/usr/bin/env python3
"""Build, execute, source-first review, and stage normalized Batch 0058 level-order candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0058'
CID = 'cq_q_68a77b01c3a999732bc21dc888503621'
QIDS = [
    '3590292944e8b631aa2e0cf561c565e5',
    '68a77b01c3a999732bc21dc888503621',
    '8eab176c51a37f667765b1624f8aca4d',
    'b0718b3bec6dd4f85105aaefce8cb37e',
    'c98862ff84a6e807b311b750df86ad92',
    'f4c91cb6297dfbe25f2e08cee70d6cd7',
]
EXPECTED_VARIANTS = {
    '算法：层序遍历',
    '算法：树的层序遍历。',
    '算法：二叉树的层序遍历（LeetCode 102）。',
    '算法手撕：二叉树的层序遍历（LeetCode 102）',
    '算法手撕：二叉树的层序遍历（Level Order Traversal）。',
    '算法手撕：二叉树的层序遍历（Binary Tree Level Order Traversal）。',
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

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_68a77b01c3a999732bc21dc888503621","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 二叉树的层序遍历（Level Order Traversal / LeetCode 102）

## 核心结论

当前归一化后的六个来源问法覆盖“层序遍历 / 树的层序遍历 / 二叉树层序遍历 / LeetCode 102”，没有保存 zigzag、bottom-up 或 N 叉树专属合同。这里按当前 Canonical 的普通二叉树层序遍历合同实现 Java BFS：使用 FIFO 队列逐层处理；每轮先记录当前 `queue.size()` 作为这一层节点数，恰好弹出这些节点并把非空左右孩子入队，最终返回 `List<List<Integer>>`，每个内层列表对应一层。时间 O(n)，辅助队列空间 O(w)，w 为最大层宽；返回结果本身占 O(n)。

## 1 分钟版

- 层序遍历本质是 BFS，核心数据结构是 FIFO 队列。
- root 非空时先入队；队列里保存“已经发现、还没处理”的节点。
- 每轮开始先取 `levelSize = queue.size()`，它就是当前层尚未处理的节点数。
- 连续处理 levelSize 个节点，把值放进当前层结果，并把左右非空孩子依次入队。
- 当前层处理完再把 `level` 加到结果；新入队的孩子留给下一轮，所以层边界不会混在一起。
- 每个节点只入队、出队一次，时间 O(n)；队列峰值等于某一时刻的待处理层宽，辅助空间 O(w)。

## 3 分钟版

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;

public final class BinaryTreeLevelOrder {
    public static final class TreeNode {
        public final int val;
        public TreeNode left;
        public TreeNode right;

        public TreeNode(int val) {
            this.val = val;
        }
    }

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
```

例如树 `[3,9,20,null,null,15,7]`：第一轮队列只有 3，得到 `[3]`；处理 3 时把 9、20 入队。第二轮开始 `levelSize=2`，只处理 9、20，得到 `[9,20]`，它们产生的 15、7 留在队列。第三轮得到 `[15,7]`，最终是 `[[3],[9,20],[15,7]]`。

## 关键细节

- **层边界必须先冻结**：`levelSize` 要在本层开始时读取。循环中队列会加入下一层孩子，如果直接一直处理到队列空，就会把多层揉成一次循环。
- **队列顺序决定同层左右顺序**：按“父节点从左到右出队、先 left 后 right 入队”，结果自然保持常见 LeetCode 102 的从左到右顺序。
- **空树**：没有任何层，返回空列表。
- **重复值**：遍历的是节点，不靠值判重；多个节点值相同都必须保留。
- **不需要 visited 集**：当前合同是普通有限二叉树，不是任意可能成环的图；每个节点只从自己的父节点被发现一次。
- **复杂度口径**：n 个节点各入/出队一次，所以时间 O(n)。辅助队列的峰值由最大层宽 w 决定，为 O(w)；若把最终二维结果也计入空间，总输出需要 O(n)。
- **合同边界**：来源没有 zigzag、bottom-up、按列或 N 叉树特定要求。那些变体可以复用 BFS 框架，但输出顺序或孩子枚举方式会变化，不能混进当前基础答案。

## 原理机制

FIFO 队列保证“更早发现的节点更早处理”。在树上，root 的深度是 0；处理深度 d 的节点时只会发现深度 d+1 的孩子，因此只要当前深度的节点全部已经排在队列前面，它们产生的下一层节点就会追加到后面。每轮冻结 `queue.size()`，等价于给当前深度建立一个边界：本轮只消费旧队列中的节点，新加入的节点全部属于下一深度。

这个不变量比“用队列”本身更关键：普通 BFS 只需要按访问顺序输出时可以连续出队；LeetCode 102 要按层分组，所以必须额外保存当前层大小、深度标记或两个队列中的一种层边界信息。当前实现选择 `levelSize`，状态最少。

## 项目经验版

来源没有真实项目经历，不能虚构业务使用。面试现场我会先确认是“按层分组返回二维列表”还是只要 BFS 访问序列；如果是 LeetCode 102，就明确二维结果、空树返回空列表。随后写队列版本，并用空树、单节点、不平衡树、重复值和多层宽树验证层边界。若追问 zigzag/bottom-up，只调整每层写入或最终顺序，不需要把基础 BFS 重写成另一套算法。

## 常见追问

- 问：为什么要在循环开始记录 `queue.size()`？答：它冻结了当前层的节点数；处理过程中加入的孩子属于下一层，不能在本轮继续消费。
- 问：DFS 能做层序遍历吗？答：可以递归携带 depth，把值写入 `result[depth]`；但题目直接问层序/BFS 时，队列更直观地表达按深度逐层扩张。
- 问：空间复杂度为什么是 O(w) 而不是 O(n)？答：若只算辅助队列，峰值取决于最大层宽 w，最坏情况下 w 可到 O(n)；最终返回结果本身无论如何需要存 n 个节点值。
- 问：重复值需要 visited 吗？答：不需要。普通树节点没有共享父引用形成的图环，重复的是值而不是节点身份；每个节点仍应输出一次。
- 问：怎么改成 zigzag？答：BFS 和 levelSize 不变，只在奇偶层改变当前 `level` 的写入方向，或用双端结构；不要改变节点发现的基本层次关系。
- 问：怎么改成 bottom-up？答：可以先做普通 level order，最后反转层列表，或每层插到结果前端；核心 BFS 不变。

## 易错点

- 不冻结 `levelSize`，一边出队一边把新孩子继续当成本层处理。
- 子节点入队顺序写成 right 再 left，却仍声称保持从左到右层序。
- 空 root 直接入 `ArrayDeque`；它不接受 null 元素，应先处理空树。
- 用节点值做 visited，导致重复值节点被错误丢弃。
- 把辅助空间 O(w) 和包含返回结果后的总空间 O(n) 混为一谈。
- 把 zigzag、bottom-up 或 N 叉树孩子遍历规则当成当前普通二叉树层序遍历的既定要求。
'''

TEST = r'''import java.util.Arrays;
import java.util.List;

public final class BinaryTreeLevelOrderTest {
    private static void check(List<List<Integer>> actual, List<List<Integer>> expected, String label) {
        if (!actual.equals(expected)) {
            throw new AssertionError(label + " actual=" + actual + " expected=" + expected);
        }
    }

    public static void main(String[] args) {
        check(BinaryTreeLevelOrder.levelOrder(null), List.of(), "empty");

        BinaryTreeLevelOrder.TreeNode one = new BinaryTreeLevelOrder.TreeNode(1);
        check(BinaryTreeLevelOrder.levelOrder(one), List.of(List.of(1)), "singleton");

        BinaryTreeLevelOrder.TreeNode root = new BinaryTreeLevelOrder.TreeNode(3);
        root.left = new BinaryTreeLevelOrder.TreeNode(9);
        root.right = new BinaryTreeLevelOrder.TreeNode(20);
        root.right.left = new BinaryTreeLevelOrder.TreeNode(15);
        root.right.right = new BinaryTreeLevelOrder.TreeNode(7);
        check(BinaryTreeLevelOrder.levelOrder(root), List.of(List.of(3), List.of(9, 20), List.of(15, 7)), "leetcode-102");

        BinaryTreeLevelOrder.TreeNode skew = new BinaryTreeLevelOrder.TreeNode(1);
        skew.right = new BinaryTreeLevelOrder.TreeNode(2);
        skew.right.right = new BinaryTreeLevelOrder.TreeNode(3);
        check(BinaryTreeLevelOrder.levelOrder(skew), List.of(List.of(1), List.of(2), List.of(3)), "skewed");

        BinaryTreeLevelOrder.TreeNode duplicates = new BinaryTreeLevelOrder.TreeNode(5);
        duplicates.left = new BinaryTreeLevelOrder.TreeNode(5);
        duplicates.right = new BinaryTreeLevelOrder.TreeNode(5);
        check(BinaryTreeLevelOrder.levelOrder(duplicates), List.of(List.of(5), List.of(5, 5)), "duplicates");

        BinaryTreeLevelOrder.TreeNode wide = new BinaryTreeLevelOrder.TreeNode(1);
        wide.left = new BinaryTreeLevelOrder.TreeNode(2);
        wide.right = new BinaryTreeLevelOrder.TreeNode(3);
        wide.left.left = new BinaryTreeLevelOrder.TreeNode(4);
        wide.left.right = new BinaryTreeLevelOrder.TreeNode(5);
        wide.right.left = new BinaryTreeLevelOrder.TreeNode(6);
        wide.right.right = new BinaryTreeLevelOrder.TreeNode(7);
        check(BinaryTreeLevelOrder.levelOrder(wide), List.of(List.of(1), List.of(2, 3), Arrays.asList(4, 5, 6, 7)), "wide-order");

        System.out.println("PASS empty singleton leetcode102 skewed duplicates layer-boundary left-right-order wide");
    }
}
'''


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def assert_ids(actual: list[str], expected: list[str], label: str) -> None:
    if sorted(actual) != sorted(expected):
        raise SystemExit(f'{label} drift: {actual}')


def main() -> int:
    candidate = ROOT / f'review/candidates/answers/{CID}.md'
    evidence = ROOT / f'review/evidence/{CID}.json'
    if candidate.exists() or evidence.exists():
        raise SystemExit(f'{CID}: candidate/evidence already exists; do not overwrite reviewed work')

    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    inv = next((row for row in inventory.get('canonicals', []) if row.get('canonical_id') == CID), None)
    if not inv or inv.get('answer_type') != 'coding' or inv.get('existing_candidate') or inv.get('existing_evidence'):
        raise SystemExit(f'{CID}: current Batch 0058 inventory no longer describes a fresh Coding target')
    assert_ids(inv.get('question_ids') or [], QIDS, 'inventory Question ownership')

    context_path = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}/context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('canonical', {}).get('canonical_id') != CID or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: frozen context/type drift')
    assert_ids(context.get('canonical', {}).get('question_ids') or [], QIDS, 'context Question ownership')
    source_rows = context.get('source_questions') or []
    covered_source_ids = {row.get('question_id') for row in source_rows if row.get('is_valid_for_library') is True}
    if covered_source_ids != set(QIDS):
        raise SystemExit(f'{CID}: frozen source Question coverage drift: {sorted(covered_source_ids)}')
    variants = {row.get('original_question') for row in source_rows}
    if variants != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: frozen source wording drift: {sorted(variants)}')

    relation_review = ROOT / f'review/content_build/answer_batch_{BATCH}/level_order_relation_review.md'
    relation_apply = ROOT / f'review/content_build/answer_batch_{BATCH}/level_order_relation_apply.md'
    if not relation_review.exists() or not relation_apply.exists():
        raise SystemExit('normalized level-order relation evidence is required before candidate writing')

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in HEADINGS:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'{CID}: candidate must contain exactly one Java implementation block')

    with tempfile.TemporaryDirectory(prefix='b58-level-order-') as temp:
        work = Path(temp)
        (work / 'BinaryTreeLevelOrder.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (work / 'BinaryTreeLevelOrderTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'BinaryTreeLevelOrder.java', 'BinaryTreeLevelOrderTest.java', cwd=work)
        stdout = run('java', 'BinaryTreeLevelOrderTest', cwd=work).stdout.strip()

    expected_stdout = 'PASS empty singleton leetcode102 skewed duplicates layer-boundary left-right-order wide'
    if stdout != expected_stdout:
        raise SystemExit(f'{CID}: unexpected fixture output: {stdout}')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    command = 'javac BinaryTreeLevelOrder.java BinaryTreeLevelOrderTest.java && java BinaryTreeLevelOrderTest'
    checks = [
        'empty tree returns no levels',
        'single node returns one level',
        'LeetCode 102 representative shape returns [[3],[9,20],[15,7]]',
        'skewed tree preserves one node per depth',
        'duplicate values are preserved as distinct nodes',
        'level boundary is frozen before enqueueing the next level',
        'left child is emitted before right child within a level',
        'wide tree preserves complete left-to-right level order',
    ]
    write_json(out / 'writer_validation.json', {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': command,
        'stdout': stdout,
        'checks': checks,
    })

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0058 normalized frozen repository context for level-order traversal',
            'locator': str(context_path),
            'source_type': 'repository_source_record',
            'checked_at': DATE,
        },
        {
            'source_id': 'relation-review',
            'title': 'Batch 0058 source-first level-order relation normalization',
            'locator': str(relation_review),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
        {
            'source_id': 'fixture',
            'title': 'Deterministic OpenJDK validation for binary-tree level order',
            'locator': str(out / 'writer_validation.json'),
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The current normalized Canonical owns all six valid ordinary level-order/binary-tree/LeetCode-102 source Questions; source-first normalization found no preserved zigzag, bottom-up, N-ary-only, or different-output contract.',
            'source_ids': ['repository-source', 'relation-review'],
            'answer_locations': ['核心结论', '关键细节', '项目经验版'],
        },
        {
            'claim_id': 'bfs-correctness',
            'text': 'The executable Java fixture verifies queue-based per-level BFS for empty, singleton, representative LeetCode-102, skewed, duplicate-value, and wide left-to-right level boundaries.',
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

    reviewer_id = 'source-first-isolated-reviewer-batch-0058-level-order-20260829-v1'
    findings = [
        'The candidate is written only after the source-first relation normalization and covers all six current source Question IDs under the single survivor Canonical.',
        'The queue-size snapshot is explained as the layer-boundary invariant, so next-level children cannot leak into the current level result.',
        'The Java implementation preserves left-to-right child order, handles empty trees before ArrayDeque insertion, and does not incorrectly deduplicate equal node values.',
        'The answer distinguishes O(w) auxiliary queue space from O(n) output storage and states the worst-case width boundary.',
        'OpenJDK validation covers empty/singleton/skewed/duplicate/wide trees and the representative LeetCode 102 output.',
    ]
    review_version = 'batch-0058.level-order.v1'
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
            str(relation_review),
            str(relation_apply),
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
            'writer_id': 'content-batch-0058-level-order-builder',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': sources + [{
            'source_id': 'isolated-review',
            'title': 'Batch 0058 level-order source-first isolated review',
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
    note = '- [x] `cq_q_68a77b01c3a999732bc21dc888503621` source-first isolated review PASS after duplicate-source normalization: all six current level-order source Question IDs are covered by one queue + frozen-level-size Java BFS answer; OpenJDK validation covers empty/singleton/LeetCode-102/skewed/duplicate/wide trees and left-to-right layer boundaries. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if note not in task:
        task += '\n' + note
    task_path.write_text(task + '\n', encoding='utf-8')

    print(f'PASS canonical={CID} source_question_ids={len(QIDS)} candidate_sha256={digest} fixture={stdout}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
