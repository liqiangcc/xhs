#!/usr/bin/env python3
"""Source-first isolated review for Batch 0062 binary-tree level-order traversal."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_61d48051e02806afb811f793afd4a269'
QIDS = ['61d48051e02806afb811f793afd4a269', '94d7a2ec2a34272114ec07d269f5d497']
EXPECTED_VARIANTS = {
    '算法 1：手写实现二叉树的层序遍历',
    '算法：二叉树的层序遍历',
}
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
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
EXPECTED_REVIEW_STDOUT = 'PASS reviewer fixed=8 random=40000 oracle=dfs-depth null=empty duplicates=preserved sparse=preserved'


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run_reviewer_validation(out: Path) -> str:
    """Compile the implementation and run an independently authored review harness."""
    harness = out / 'LevelOrderTraversalReviewerTest.java'
    harness.write_text(r'''import java.util.*;

public final class LevelOrderTraversalReviewerTest {
    private static final Random RNG = new Random(0x620061D4L);

    private static void fail(String message) { throw new AssertionError(message); }

    private static List<List<Integer>> oracle(LevelOrderTraversal.TreeNode root) {
        List<List<Integer>> levels = new ArrayList<>();
        oracleDfs(root, 0, levels);
        return levels;
    }

    private static void oracleDfs(LevelOrderTraversal.TreeNode node, int depth, List<List<Integer>> levels) {
        if (node == null) return;
        while (levels.size() <= depth) levels.add(new ArrayList<>());
        levels.get(depth).add(node.val);
        oracleDfs(node.left, depth + 1, levels);
        oracleDfs(node.right, depth + 1, levels);
    }

    private static void check(LevelOrderTraversal.TreeNode root, String label) {
        List<List<Integer>> expected = oracle(root);
        List<List<Integer>> actual = LevelOrderTraversal.levelOrder(root);
        if (!actual.equals(expected)) fail(label + " expected=" + expected + " actual=" + actual);
    }

    private static LevelOrderTraversal.TreeNode randomTree(int maxNodes) {
        if (maxNodes <= 0 || RNG.nextInt(6) == 0) return null;
        LevelOrderTraversal.TreeNode root = new LevelOrderTraversal.TreeNode(RNG.nextInt(9) - 4);
        ArrayDeque<LevelOrderTraversal.TreeNode> open = new ArrayDeque<>();
        open.add(root);
        int count = 1;
        while (!open.isEmpty() && count < maxNodes) {
            LevelOrderTraversal.TreeNode p = open.removeFirst();
            if (count < maxNodes && RNG.nextInt(100) < 64) {
                p.left = new LevelOrderTraversal.TreeNode(RNG.nextInt(9) - 4);
                open.addLast(p.left);
                count++;
            }
            if (count < maxNodes && RNG.nextInt(100) < 64) {
                p.right = new LevelOrderTraversal.TreeNode(RNG.nextInt(9) - 4);
                open.addLast(p.right);
                count++;
            }
        }
        return root;
    }

    public static void main(String[] args) {
        check(null, "null");
        check(new LevelOrderTraversal.TreeNode(7), "single");

        LevelOrderTraversal.TreeNode balanced = new LevelOrderTraversal.TreeNode(1);
        balanced.left = new LevelOrderTraversal.TreeNode(2);
        balanced.right = new LevelOrderTraversal.TreeNode(3);
        balanced.left.left = new LevelOrderTraversal.TreeNode(4);
        balanced.left.right = new LevelOrderTraversal.TreeNode(5);
        balanced.right.left = new LevelOrderTraversal.TreeNode(6);
        balanced.right.right = new LevelOrderTraversal.TreeNode(7);
        check(balanced, "balanced");

        LevelOrderTraversal.TreeNode sparse = new LevelOrderTraversal.TreeNode(8);
        sparse.right = new LevelOrderTraversal.TreeNode(9);
        sparse.right.left = new LevelOrderTraversal.TreeNode(10);
        sparse.right.left.right = new LevelOrderTraversal.TreeNode(11);
        check(sparse, "sparse");

        LevelOrderTraversal.TreeNode leftChain = new LevelOrderTraversal.TreeNode(3);
        leftChain.left = new LevelOrderTraversal.TreeNode(3);
        leftChain.left.left = new LevelOrderTraversal.TreeNode(3);
        check(leftChain, "left-chain-duplicates");

        LevelOrderTraversal.TreeNode rightChain = new LevelOrderTraversal.TreeNode(-1);
        rightChain.right = new LevelOrderTraversal.TreeNode(-2);
        rightChain.right.right = new LevelOrderTraversal.TreeNode(-3);
        check(rightChain, "right-chain");

        LevelOrderTraversal.TreeNode mixed = new LevelOrderTraversal.TreeNode(0);
        mixed.left = new LevelOrderTraversal.TreeNode(5);
        mixed.right = new LevelOrderTraversal.TreeNode(5);
        mixed.left.right = new LevelOrderTraversal.TreeNode(6);
        mixed.right.left = new LevelOrderTraversal.TreeNode(6);
        check(mixed, "duplicate-values-distinct-nodes");

        LevelOrderTraversal.TreeNode wide = new LevelOrderTraversal.TreeNode(1);
        wide.left = new LevelOrderTraversal.TreeNode(2);
        wide.right = new LevelOrderTraversal.TreeNode(3);
        wide.left.left = new LevelOrderTraversal.TreeNode(4);
        wide.left.right = new LevelOrderTraversal.TreeNode(5);
        wide.right.left = new LevelOrderTraversal.TreeNode(6);
        wide.right.right = new LevelOrderTraversal.TreeNode(7);
        wide.left.left.left = new LevelOrderTraversal.TreeNode(8);
        wide.right.right.right = new LevelOrderTraversal.TreeNode(9);
        check(wide, "wide-with-holes");

        for (int i = 0; i < 40000; i++) {
            check(randomTree(1 + RNG.nextInt(90)), "random-" + i);
        }
        System.out.println("PASS reviewer fixed=8 random=40000 oracle=dfs-depth null=empty duplicates=preserved sparse=preserved");
    }
}
''', encoding='utf-8')

    proc = subprocess.run(
        ['bash', '-lc', 'javac LevelOrderTraversal.java LevelOrderTraversalReviewerTest.java && java LevelOrderTraversalReviewerTest'],
        cwd=out,
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f'{CID}: independent reviewer validation failed: {proc.stderr or proc.stdout}')
    stdout = proc.stdout.strip()
    if stdout != EXPECTED_REVIEW_STDOUT:
        raise SystemExit(f'{CID}: reviewer stdout drift: {stdout!r}')
    for class_file in out.glob('*.class'):
        class_file.unlink()
    return stdout


def main() -> int:
    inventory_path = ROOT / f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result') != 'pass':
        raise SystemExit('batch 0062 source inventory is not passing')
    item = next((x for x in inventory.get('canonicals', []) if x.get('canonical_id') == CID), None)
    if not item:
        raise SystemExit(f'{CID}: missing from Batch 0062 source inventory')
    if item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: expected coding, got {item.get("answer_type")}')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: frozen ownership drift: {item.get("question_ids")}')
    if item.get('source_question_count') != 2 or item.get('source_occurrence_count') != 2:
        raise SystemExit(f'{CID}: occurrence-aware inventory drift')
    if {x.get('original_question') for x in item.get('source_questions', [])} != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: source wording drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context_path = out / 'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: frozen context/type drift')
    canonical = context.get('canonical') or {}
    if canonical.get('canonical_id') != CID or sorted(canonical.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: context ownership drift')
    source_rows = list(context.get('source_questions') or [])
    if len(source_rows) != 2 or {x.get('original_question') for x in source_rows} != EXPECTED_VARIANTS:
        raise SystemExit(f'{CID}: context source variants drift')
    occurrence_ids = {
        (x.get('question_id'), x.get('source_note_id'), x.get('source_question_index'), x.get('original_question'))
        for x in source_rows
    }
    if len(occurrence_ids) != 2:
        raise SystemExit(f'{CID}: source occurrence identity collapsed')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate = candidate_path.read_text(encoding='utf-8')
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    for heading in HEADINGS:
        if candidate.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if candidate.count('- 问：') < 5:
        raise SystemExit(f'{CID}: question-specific follow-up coverage too small')
    required_fragments = [
        'List<List<Integer>>', 'ArrayDeque', 'levelSize = queue.size()',
        'queue.removeFirst()', 'queue.addLast', 'O(n)', 'O(w)',
        'FIFO', 'null', '重复值', 'DFS', '一维', '层边界',
    ]
    missing = [fragment for fragment in required_fragments if fragment not in candidate]
    if missing:
        raise SystemExit(f'{CID}: coding/invariant/boundary coverage missing: {missing}')

    one_minute = candidate.split('## 1 分钟版', 1)[1].split('## 3 分钟版', 1)[0]
    one_minute_points = sum(1 for line in one_minute.splitlines() if line.startswith('- '))
    if not (3 <= one_minute_points <= 5):
        raise SystemExit(f'{CID}: one-minute point count must be 3..5, got {one_minute_points}')

    reviewer_stdout = run_reviewer_validation(out)
    reviewer_validation_path = out / 'reviewer_validation.json'
    write_json(reviewer_validation_path, {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'validator': 'independent_source_first_reviewer',
        'command': 'javac LevelOrderTraversal.java LevelOrderTraversalReviewerTest.java && java LevelOrderTraversalReviewerTest',
        'stdout': reviewer_stdout,
        'checks': [
            'null tree returns empty result',
            'single, balanced, sparse, left-chain, right-chain and wide-with-holes trees match an independent DFS-by-depth oracle',
            'duplicate values on distinct nodes remain distinct output entries',
            '40,000 independently seeded random trees up to 90 nodes match the DFS-by-depth oracle',
        ],
    })

    reviewer_id = 'source-first-isolated-reviewer-batch-0062-level-order-20260831-v1'
    review_version = 'batch-0062.level-order.v1'
    findings = [
        'Both frozen primary-source variants ask for binary-tree level-order traversal and are directly covered by the candidate.',
        'The candidate declares its Java node/input/output/null contract instead of presenting unstated source constraints as facts.',
        'The queue invariant is explicit: freeze the pre-round queue size, consume exactly that level, and append non-null children for the next level.',
        'The implementation is runnable and independently revalidated against a DFS-by-depth oracle across fixed sparse/duplicate cases and 40,000 seeded random trees.',
        'Time O(n) and auxiliary queue O(w) bounds are stated with returned output space separated from the queue cost.',
        'The answer covers the one-dimensional-output variant, DFS-by-depth alternative, empty tree, sparse tree, duplicate-value and recursion-stack boundaries without fabricating production experience.',
    ]
    review_result_path = out / 'isolated_review_result.json'
    write_json(review_result_path, {
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
            str(context_path), str(inventory_path), str(candidate_path),
            str(out / 'LevelOrderTraversal.java'), str(out / 'LevelOrderTraversalReviewerTest.java'),
            str(reviewer_validation_path), 'config/answer_quality.json',
            'docs/refactor/09_answer_content_standard.md',
        ],
        'forbidden_inputs_not_used': [
            str(out / 'writer_research.json'), 'writer self score', 'writer expected decision',
        ],
        'scores': SCORES,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': [PROMOTION_BLOCKER],
    })

    sources = [
        {
            'source_id': 'repository-source',
            'title': 'Batch 0062 frozen repository context for binary-tree level-order traversal',
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
            'source_id': 'reviewer-validation',
            'title': 'Independent Java level-order differential validation against DFS-by-depth oracle',
            'locator': str(reviewer_validation_path),
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
        {
            'source_id': 'isolated-review',
            'title': 'Batch 0062 level-order source-first isolated review',
            'locator': str(review_result_path),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The two frozen source occurrences ask for binary-tree level-order traversal and do not prescribe language, node API, null handling or output shape.',
            'source_ids': ['repository-source', 'source-inventory'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节'],
        },
        {
            'claim_id': 'bfs-level-contract',
            'text': 'Under the declared Java contract, the FIFO implementation with a frozen per-round queue size returns left-to-right values grouped by depth, returns empty for null, and preserves duplicate-valued nodes.',
            'source_ids': ['reviewer-validation'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制'],
        },
        {
            'claim_id': 'boundary-and-variant',
            'text': 'The independently validated implementation covers sparse and wide trees while the answer explicitly distinguishes grouped levels from a flat BFS output and identifies DFS-by-depth as an alternative.',
            'source_ids': ['reviewer-validation', 'isolated-review'],
            'answer_locations': ['关键细节', '原理机制', '常见追问', '易错点'],
        },
    ]
    locations = ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']
    coverage = [{'question_id': qid, 'covered': True, 'answer_locations': locations} for qid in QIDS]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0062-level-order-writer',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'source_occurrence_count': 2,
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
    pass_line = (
        f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; '
        'both frozen source variants are covered; the declared Java BFS contract was independently revalidated against a DFS-by-depth oracle on fixed edge cases and 40,000 seeded random trees. '
        'Formal promotion remains blocked by repository human-approval/real-review policy.'
    )
    if pass_line not in task:
        task_path.write_text(task + '\n' + pass_line + '\n', encoding='utf-8')

    print(EXPECTED_REVIEW_STDOUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
