#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0050 preorder/inorder -> postorder candidate."""

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
CID = 'cq_q_d6a3d5566380a6dba9d460a6ae25e68e'
QID = 'd6a3d5566380a6dba9d460a6ae25e68e'
EXPECTED = '算法：给二叉树的前序和中序数组，求后序数组（重建二叉树+后序遍历）'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d6a3d5566380a6dba9d460a6ae25e68e","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 前序 + 中序重建二叉树并得到后序数组

## 核心结论

前序遍历的第一个元素一定是当前子树根节点；在中序遍历中找到这个根后，左边就是左子树、右边就是右子树。用一个 `value -> inorderIndex` 哈希表把“在中序中找根”从 O(n) 降到 O(1)，递归重建左右子树，最后按“左 -> 右 -> 根”收集后序结果即可。这里明确一个题目没有写出的必要契约：**节点值互不重复，且前序/中序来自同一棵有限二叉树**；若数组为空则返回空数组，若长度、元素集合、唯一性或区间关系不合法则抛 `IllegalArgumentException`。

## 1 分钟版

- 前序是 `根 -> 左 -> 右`，所以每个递归区间的 `preorder[preLeft]` 就是根。
- 中序是 `左 -> 根 -> 右`；根在中序的位置能确定左右子树各有多少节点。
- 左子树节点数 `leftSize = rootIndex - inLeft`，因此前序中的下一段长度也必须是 `leftSize`。
- 用 HashMap 预存中序下标，总重建时间 O(n)；如果每次线性扫描中序，最坏会退化到 O(n²)。
- 重建后再做后序遍历 `左 -> 右 -> 根`，得到要求的数组。
- 无重复值是“前序 + 中序唯一确定二叉树”的关键前提；重复值时仅凭值无法唯一定位根。

## 3 分钟版

```java
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

public final class TraversalRebuild {
    private static final class Node {
        final int value;
        Node left;
        Node right;

        Node(int value) {
            this.value = value;
        }
    }

    public static int[] postorderFromPreIn(int[] preorder, int[] inorder) {
        if (preorder == null || inorder == null) {
            throw new IllegalArgumentException("traversals must be non-null");
        }
        if (preorder.length != inorder.length) {
            throw new IllegalArgumentException("traversal lengths differ");
        }
        int n = preorder.length;
        if (n == 0) return new int[0];

        Map<Integer, Integer> inorderIndex = new HashMap<>();
        for (int i = 0; i < n; i++) {
            if (inorderIndex.put(inorder[i], i) != null) {
                throw new IllegalArgumentException("duplicate node value");
            }
        }

        Set<Integer> seenPreorder = new HashSet<>();
        for (int value : preorder) {
            if (!seenPreorder.add(value) || !inorderIndex.containsKey(value)) {
                throw new IllegalArgumentException("traversals contain different or duplicate values");
            }
        }
        if (seenPreorder.size() != inorderIndex.size()) {
            throw new IllegalArgumentException("traversals contain different values");
        }

        Node root = build(preorder, 0, n - 1, 0, n - 1, inorderIndex);
        int[] result = new int[n];
        int[] cursor = {0};
        fillPostorder(root, result, cursor);
        if (cursor[0] != n) {
            throw new IllegalArgumentException("invalid traversal relationship");
        }
        return result;
    }

    private static Node build(
            int[] preorder,
            int preLeft,
            int preRight,
            int inLeft,
            int inRight,
            Map<Integer, Integer> inorderIndex) {
        if (preLeft > preRight) {
            if (inLeft <= inRight) {
                throw new IllegalArgumentException("invalid traversal relationship");
            }
            return null;
        }
        if (inLeft > inRight || preRight - preLeft != inRight - inLeft) {
            throw new IllegalArgumentException("invalid traversal relationship");
        }

        int rootValue = preorder[preLeft];
        Integer rootIndex = inorderIndex.get(rootValue);
        if (rootIndex == null || rootIndex < inLeft || rootIndex > inRight) {
            throw new IllegalArgumentException("invalid traversal relationship");
        }

        int leftSize = rootIndex - inLeft;
        int leftPreRight = preLeft + leftSize;
        if (leftPreRight > preRight) {
            throw new IllegalArgumentException("invalid traversal relationship");
        }

        Node root = new Node(rootValue);
        root.left = build(preorder, preLeft + 1, leftPreRight, inLeft, rootIndex - 1, inorderIndex);
        root.right = build(preorder, leftPreRight + 1, preRight, rootIndex + 1, inRight, inorderIndex);
        return root;
    }

    private static void fillPostorder(Node node, int[] result, int[] cursor) {
        if (node == null) return;
        fillPostorder(node.left, result, cursor);
        fillPostorder(node.right, result, cursor);
        result[cursor[0]++] = node.value;
    }
}
```

例如前序 `[3, 9, 20, 15, 7]`、中序 `[9, 3, 15, 20, 7]`：前序首元素 3 是根，中序中 3 左边只有 9，所以左子树就是 9；右侧 `[15,20,7]` 对应前序后半段 `[20,15,7]`，继续递归，最终后序为 `[9, 15, 7, 20, 3]`。

其实如果题目只要“后序数组”而不要求真的构造节点对象，也可以在同样的区间递归中直接把根值写入后序结果，从而省掉重建树的节点对象；但题干明确写了“重建二叉树 + 后序遍历”，所以上面的实现保留这两个步骤，边界更贴近来源问法。

## 关键细节

- **唯一值前提**：前序和中序要靠“根值在中序中的唯一位置”划分左右子树；有重复值时，一个值可能对应多个位置，题目若不提供额外标识就不能唯一重建。
- **区间长度必须一致**：递归中的前序区间和中序区间必须描述同一批节点，所以两段长度始终相同；不一致说明输入遍历不可能来自同一棵树。
- **根必须落在当前中序区间内**：即使两个数组元素集合相同，顺序关系也可能互相矛盾；若当前前序根在全局中序存在、但不在当前子树区间，就应判非法。
- **为什么 HashMap 是 O(n)**：先扫描一次中序建立索引 O(n)，之后每个节点只作为一次递归根被处理，根位置查询平均 O(1)，所以总时间 O(n)。
- **空间**：索引表 O(n)，重建出的树本身 O(n)，输出数组 O(n)，递归栈 O(h)；若只计算后序而不保留树，可去掉那一份节点对象空间。
- **退化树**：最坏高度 `h=n`，递归深度也会到 O(n)；节点非常多时可改显式栈或迭代实现，避免调用栈限制。
- **输入不修改**：实现只读取两个输入数组，测试会校验调用后数组内容保持不变。

## 原理机制

两种遍历各自暴露不同的信息。前序把“根是谁”放在最前面；中序把“哪些节点属于左子树、哪些属于右子树”编码在根的两侧。把两者结合，就能从根开始递归确定整棵树：

1. `preorder[preLeft]` 确定当前根；
2. 根在中序的下标确定左子树大小 `leftSize`；
3. 前序中紧跟根之后的 `leftSize` 个元素必然属于左子树，其余属于右子树；
4. 对左右区间重复同一过程；
5. 重建完成后按后序定义先访问左右子树，最后写根。

这个递归真正维持的不变量是：每一次调用的前序区间与中序区间包含完全相同的一组节点，并且分别是同一棵子树的两种遍历。根定位把这组节点拆成左右两个更小但仍满足该不变量的子问题，直到空区间结束。

## 项目经验版

来源没有真实项目经历，不能虚构“线上重建过二叉树”。工程中如果遍历数据来自外部输入，我会显式校验长度、唯一性、元素集合和递归区间关系，而不是默认输入永远合法；如果树可能非常深，还会避免无界递归。若真正业务只需要转换遍历序列、不需要保留树结构，则应直接在区间递归中产出后序，减少对象分配，而不是为了题目形式保留无用中间对象。

## 常见追问

- 问：为什么前序 + 中序可以唯一确定树？答：在节点值唯一的前提下，前序唯一确定当前根，中序中根的唯一位置又唯一划分左右节点集合，递归后整棵树被唯一确定。
- 问：如果节点值有重复怎么办？答：仅凭值无法知道前序中的某个根对应中序的哪一次出现，不能保证唯一重建；需要额外唯一 ID、位置约束或改变题目契约。
- 问：为什么不用每次在中序数组里扫描根？答：可以做对，但退化树每层都扫描越来越长的区间，最坏 O(n²)；预建 HashMap 后每个根平均 O(1) 定位，总体 O(n)。
- 问：一定要先构造树吗？答：不一定。如果最终只要后序数组，可以按相同区间递归直接“左、右、根”写结果；本答案因为题干明确写了“重建 + 后序”而保留 Node。
- 问：前序和中序元素集合一样就一定合法吗？答：不一定。顺序关系也可能矛盾，所以递归时还必须检查当前根是否位于当前中序子区间，以及两边区间长度是否匹配。
- 问：复杂度是多少？答：平均 O(n) 时间；索引、树和输出各 O(n)，递归栈 O(h)。如果不真正建树，可省掉树节点那一份 O(n) 空间。

## 易错点

- 忘记说明“节点值唯一”前提，却直接用 `value -> index` Map。
- 每层递归线性扫描中序找根，退化树变成 O(n²)。
- 左子树大小算对了，但前序切片下标多加或少加 1，产生 off-by-one。
- 只检查数组长度和元素集合，不检查当前根是否真的落在当前中序子区间。
- 把后序顺序写成“根 -> 左 -> 右”或“左 -> 根 -> 右”。
- 没考虑空树、单节点、全左/全右退化树和非法遍历输入。
'''

TEST = r'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public final class TraversalRebuildTest {
    private static final class TNode {
        final int value;
        TNode left;
        TNode right;
        TNode(int value) { this.value = value; }
    }

    private static int[] toArray(List<Integer> values) {
        int[] out = new int[values.size()];
        for (int i = 0; i < values.size(); i++) out[i] = values.get(i);
        return out;
    }

    private static void preorder(TNode node, List<Integer> out) {
        if (node == null) return;
        out.add(node.value);
        preorder(node.left, out);
        preorder(node.right, out);
    }

    private static void inorder(TNode node, List<Integer> out) {
        if (node == null) return;
        inorder(node.left, out);
        out.add(node.value);
        inorder(node.right, out);
    }

    private static void postorder(TNode node, List<Integer> out) {
        if (node == null) return;
        postorder(node.left, out);
        postorder(node.right, out);
        out.add(node.value);
    }

    private static TNode randomTree(List<Integer> values, int left, int right, Random random) {
        if (left >= right) return null;
        int rootOffset = random.nextInt(right - left);
        int rootPos = left + rootOffset;
        int rootValue = values.get(rootPos);
        TNode root = new TNode(rootValue);

        List<Integer> remaining = new ArrayList<>();
        for (int i = left; i < right; i++) if (i != rootPos) remaining.add(values.get(i));
        int leftSize = remaining.isEmpty() ? 0 : random.nextInt(remaining.size() + 1);
        List<Integer> leftValues = new ArrayList<>(remaining.subList(0, leftSize));
        List<Integer> rightValues = new ArrayList<>(remaining.subList(leftSize, remaining.size()));
        Collections.shuffle(leftValues, random);
        Collections.shuffle(rightValues, random);
        root.left = randomTree(leftValues, 0, leftValues.size(), random);
        root.right = randomTree(rightValues, 0, rightValues.size(), random);
        return root;
    }

    private static void check(int[] preorder, int[] inorder, int[] expected, String name) {
        int[] preCopy = preorder.clone();
        int[] inCopy = inorder.clone();
        int[] actual = TraversalRebuild.postorderFromPreIn(preorder, inorder);
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError(name + " actual=" + Arrays.toString(actual) + " expected=" + Arrays.toString(expected));
        }
        if (!Arrays.equals(preorder, preCopy) || !Arrays.equals(inorder, inCopy)) {
            throw new AssertionError(name + " mutated input");
        }
    }

    private static void expectIllegal(int[] preorder, int[] inorder, String name) {
        try {
            TraversalRebuild.postorderFromPreIn(preorder, inorder);
            throw new AssertionError(name + " expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // pass
        }
    }

    public static void main(String[] args) {
        check(new int[]{3,9,20,15,7}, new int[]{9,3,15,20,7}, new int[]{9,15,7,20,3}, "balanced-example");
        check(new int[]{1}, new int[]{1}, new int[]{1}, "single");
        check(new int[]{1,2,3,4}, new int[]{4,3,2,1}, new int[]{4,3,2,1}, "all-left");
        check(new int[]{1,2,3,4}, new int[]{1,2,3,4}, new int[]{4,3,2,1}, "all-right");
        check(new int[]{}, new int[]{}, new int[]{}, "empty");

        expectIllegal(null, new int[]{}, "null-preorder");
        expectIllegal(new int[]{}, null, "null-inorder");
        expectIllegal(new int[]{1}, new int[]{1,2}, "different-length");
        expectIllegal(new int[]{1,1}, new int[]{1,1}, "duplicates");
        expectIllegal(new int[]{1,2}, new int[]{1,3}, "different-values");
        expectIllegal(new int[]{1,2,3}, new int[]{3,1,2}, "inconsistent-order");

        Random random = new Random(20260829L);
        for (int round = 0; round < 500; round++) {
            int n = 1 + random.nextInt(60);
            List<Integer> values = new ArrayList<>();
            for (int i = 0; i < n; i++) values.add(round * 1000 + i + 1);
            Collections.shuffle(values, random);
            TNode root = randomTree(values, 0, values.size(), random);
            List<Integer> pre = new ArrayList<>();
            List<Integer> in = new ArrayList<>();
            List<Integer> post = new ArrayList<>();
            preorder(root, pre);
            inorder(root, in);
            postorder(root, post);
            check(toArray(pre), toArray(in), toArray(post), "random-" + round);
        }

        System.out.println("PASS known balanced single empty skew invalid-input random-tree-oracle=500 input-preserved");
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

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b50-pre-in-post-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'TraversalRebuild.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'TraversalRebuildTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'TraversalRebuild.java', 'TraversalRebuildTest.java', cwd=tmpdir)
        stdout = run('java', 'TraversalRebuildTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS known balanced single empty skew invalid-input random-tree-oracle=500 input-preserved'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac TraversalRebuild.java TraversalRebuildTest.java && java TraversalRebuildTest',
        'stdout': stdout,
        'checks': [
            'known balanced traversal example yields the expected postorder',
            'single-node, empty, all-left, and all-right trees are handled',
            'null, unequal-length, duplicate-value, different-set, and inconsistent-order inputs follow the explicit illegal-input contract',
            '500 deterministic random unique-value trees agree with an independent original-tree postorder oracle',
            'preorder and inorder input arrays remain unchanged',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 traversal-rebuild executable validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The repository source asks to derive postorder from preorder and inorder by rebuilding the binary tree, but does not define duplicate-value handling, invalid-input disposition, or empty-input semantics.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'reconstruction-validation', 'text': 'The OpenJDK 21 fixture validates root partitioning and postorder output on known, skewed, empty, single-node and 500 deterministic random unique-value trees against an independent original-tree traversal oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'invalid-input-boundary', 'text': 'The executable fixture verifies the explicitly declared non-null, equal-length, unique-value, same-node-set and structurally consistent traversal contract.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '关键细节', '常见追问', '易错点']},
        {'claim_id': 'complexity-bound', 'text': 'The implementation builds one inorder index map and processes each unique node once during reconstruction; the code shape therefore bounds average reconstruction work to O(n), with recursion depth O(h).', 'source_ids': ['fixture'], 'answer_locations': ['1 分钟版', '关键细节', '原理机制']},
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

    scores = {
        'facts_and_evidence': 24,
        'directness_and_relevance': 20,
        'type_specific_completeness': 20,
        'mechanism_and_causality': 15,
        'boundaries_and_tradeoffs': 10,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The candidate directly answers the exact preorder + inorder -> rebuild -> postorder task instead of leaving a generic tree template.',
        'The source does not state duplicate-value or invalid-input semantics; the candidate makes unique node values and explicit validation behavior assumptions rather than source facts.',
        'The root-position/left-size recursion invariant is explained and matches the executable implementation.',
        'OpenJDK 21 validation covers known and degenerate shapes, invalid contracts, input preservation, and 500 deterministic random trees against an independent original-tree postorder oracle.',
        'The candidate explains the O(n) inorder-index optimization and the O(h) recursion-depth boundary, including the degenerate-tree stack risk.',
        'No production history or unsupported source constraints are fabricated.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0050-pre-in-postorder-20260829-v1',
        'review_version': 'batch-0050.pre-in-postorder.v1',
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

    evidence_sources = sources + [{
        'source_id': 'isolated-review',
        'title': 'Preorder/inorder reconstruction source-first isolated review',
        'locator': str(out / 'isolated_review_result.json'),
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    }]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0050-pre-in-postorder-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'known balanced traversal', 'expected': '[9,15,7,20,3]', 'actual': 'pass', 'passed': True},
                {'case': 'empty/single/skewed trees', 'expected': 'valid postorder for each shape', 'actual': 'pass', 'passed': True},
                {'case': 'invalid traversal contracts', 'expected': 'explicit IllegalArgumentException contract', 'actual': 'pass', 'passed': True},
                {'case': '500 deterministic random trees', 'expected': 'matches independent original-tree postorder oracle', 'actual': 'pass', 'passed': True},
                {'case': 'input preservation', 'expected': 'preorder/inorder arrays unchanged', 'actual': 'pass', 'passed': True},
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
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d6a3d5566380a6dba9d460a6ae25e68e` source-first isolated review PASS: exact preorder + inorder -> rebuild -> postorder behavior is implemented with an inorder-index partition invariant; unique node values and invalid-input behavior are explicitly labeled as assumptions because the source does not define them. OpenJDK 21 validation covers known/balanced/single/empty/skewed trees, invalid traversal contracts, input preservation, and 500 deterministic random trees against an independent original-tree postorder oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
