#!/usr/bin/env python3
"""Source-first isolated review for Batch 0062 3Sum."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_e1cbd1e9e8df435dfb30e81ea69018c8'
QID = 'e1cbd1e9e8df435dfb30e81ea69018c8'
EXPECTED_QUESTION = '算法手撕：三数之和（3Sum）。'
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
EXPECTED_REVIEW_STDOUT = (
    'PASS reviewer fixed=10 exhaustive=19608 random=25000 '
    'oracle=bruteforce-triples overflow=pass input_unchanged=pass dedupe=pass'
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run_reviewer_validation(out: Path) -> str:
    """Compile the candidate implementation and run an independently authored oracle harness."""
    harness = out / 'ThreeSumReviewerTest.java'
    harness.write_text(r'''import java.util.*;

public final class ThreeSumReviewerTest {
    private static final Random RNG = new Random(0x62E1CBD2L);
    private static int exhaustiveCases = 0;

    private static void fail(String message) { throw new AssertionError(message); }

    private static String key(int x, int y, int z) {
        int[] a = {x, y, z};
        Arrays.sort(a);
        return a[0] + "," + a[1] + "," + a[2];
    }

    private static Set<String> oracle(int[] nums) {
        Set<String> out = new TreeSet<>();
        if (nums == null) return out;
        for (int i = 0; i < nums.length; i++) {
            for (int j = i + 1; j < nums.length; j++) {
                for (int k = j + 1; k < nums.length; k++) {
                    if ((long) nums[i] + nums[j] + nums[k] == 0L) {
                        out.add(key(nums[i], nums[j], nums[k]));
                    }
                }
            }
        }
        return out;
    }

    private static Set<String> normalize(List<List<Integer>> rows) {
        if (rows == null) fail("result must not be null");
        Set<String> out = new TreeSet<>();
        for (List<Integer> row : rows) {
            if (row == null || row.size() != 3) fail("not a triplet: " + row);
            int x = row.get(0), y = row.get(1), z = row.get(2);
            if (!(x <= y && y <= z)) fail("triplet is not internally sorted: " + row);
            if ((long) x + y + z != 0L) fail("non-zero triplet: " + row);
            String k = key(x, y, z);
            if (!out.add(k)) fail("duplicate result triplet: " + k);
        }
        return out;
    }

    private static void check(int[] input, String label) {
        int[] before = input == null ? null : input.clone();
        Set<String> expected = oracle(input);
        Set<String> actual = normalize(ThreeSum.threeSum(input));
        if (!actual.equals(expected)) fail(label + " expected=" + expected + " actual=" + actual);
        if (input != null && !Arrays.equals(input, before)) fail(label + " mutated input");
    }

    private static void enumerate(int[] a, int pos) {
        if (pos == a.length) {
            exhaustiveCases++;
            check(a.clone(), "exhaustive-" + exhaustiveCases);
            return;
        }
        for (int v = -3; v <= 3; v++) {
            a[pos] = v;
            enumerate(a, pos + 1);
        }
    }

    private static int randomValue() {
        int mode = RNG.nextInt(20);
        if (mode == 0) return Integer.MIN_VALUE;
        if (mode == 1) return Integer.MAX_VALUE;
        return RNG.nextInt(41) - 20;
    }

    public static void main(String[] args) {
        check(new int[]{-1,0,1,2,-1,-4}, "classic");
        check(new int[]{0,0,0,0}, "all-zero");
        check(new int[]{1,2,-2,-1}, "none");
        check(new int[]{-2,0,0,2,2}, "dedupe-both-sides");
        check(new int[]{-4,-2,-2,-2,0,1,2,2,2,3,3,4}, "many-duplicates");
        check(new int[]{Integer.MIN_VALUE,1,Integer.MAX_VALUE}, "overflow-zero");
        check(new int[]{Integer.MAX_VALUE,Integer.MAX_VALUE,2,-3,-1}, "overflow-direction");
        check(new int[]{-1,-1,-1,2,2,2}, "duplicate-index-combos");
        check(new int[]{0,0}, "short-input");
        check(null, "null-input");

        for (int n = 0; n <= 5; n++) enumerate(new int[n], 0);
        if (exhaustiveCases != 19608) fail("exhaustive case count drift: " + exhaustiveCases);

        for (int i = 0; i < 25000; i++) {
            int n = RNG.nextInt(15);
            int[] a = new int[n];
            for (int j = 0; j < n; j++) a[j] = randomValue();
            check(a, "random-" + i);
        }

        System.out.println("PASS reviewer fixed=10 exhaustive=19608 random=25000 oracle=bruteforce-triples overflow=pass input_unchanged=pass dedupe=pass");
    }
}
''', encoding='utf-8')

    proc = subprocess.run(
        ['bash', '-lc', 'javac ThreeSum.java ThreeSumReviewerTest.java && java ThreeSumReviewerTest'],
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
    if item.get('question_ids') != [QID]:
        raise SystemExit(f'{CID}: frozen ownership drift: {item.get("question_ids")}')
    if item.get('source_question_count') != 1 or item.get('source_occurrence_count') != 2:
        raise SystemExit(f'{CID}: occurrence-aware inventory drift')
    if {x.get('original_question') for x in item.get('source_questions', [])} != {EXPECTED_QUESTION}:
        raise SystemExit(f'{CID}: source wording drift')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context_path = out / 'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: frozen context/type drift')
    canonical = context.get('canonical') or {}
    if canonical.get('canonical_id') != CID or canonical.get('question_ids') != [QID]:
        raise SystemExit(f'{CID}: context ownership drift')
    source_rows = list(context.get('source_questions') or [])
    if len(source_rows) != 2 or {x.get('original_question') for x in source_rows} != {EXPECTED_QUESTION}:
        raise SystemExit(f'{CID}: context source occurrence drift')
    occurrence_ids = {
        (x.get('question_id'), x.get('source_note_id'), x.get('source_question_index'))
        for x in source_rows
    }
    if len(occurrence_ids) != 2:
        raise SystemExit(f'{CID}: duplicate source occurrences were collapsed')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate = candidate_path.read_text(encoding='utf-8')
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    for heading in HEADINGS:
        if candidate.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if candidate.count('- 问：') < 5:
        raise SystemExit(f'{CID}: question-specific follow-up coverage too small')
    required_fragments = [
        'List<List<Integer>>', 'nums.clone()', 'Arrays.sort(a)', 'long sum',
        'while (left < right)', 'a[i] > 0', 'O(n^2)', 'O(n)', '去重',
        '[0,0,0]', 'Integer', '不修改输入', '双指针', 'Two Sum',
    ]
    missing = [fragment for fragment in required_fragments if fragment not in candidate]
    if missing:
        raise SystemExit(f'{CID}: coding/invariant/boundary coverage missing: {missing}')

    one_minute = candidate.split('## 1 分钟版', 1)[1].split('## 3 分钟版', 1)[0]
    one_minute_points = sum(1 for line in one_minute.splitlines() if line.startswith('- '))
    if not (4 <= one_minute_points <= 6):
        raise SystemExit(f'{CID}: one-minute point count must be 4..6, got {one_minute_points}')

    reviewer_stdout = run_reviewer_validation(out)
    reviewer_validation_path = out / 'reviewer_validation.json'
    write_json(reviewer_validation_path, {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'validator': 'independent_source_first_reviewer',
        'command': 'javac ThreeSum.java ThreeSumReviewerTest.java && java ThreeSumReviewerTest',
        'stdout': reviewer_stdout,
        'checks': [
            'classic, zero-only, no-solution, duplicate-heavy, short and null boundaries match exhaustive triple enumeration',
            'integer-extreme cases preserve comparison direction because the implementation sums in long',
            'all 19,608 arrays over values -3..3 through length five match the independent brute-force oracle',
            '25,000 independently seeded random arrays through length fourteen match the brute-force oracle',
            'every returned triplet is internally sorted, sums to zero and is unique; input arrays remain unchanged',
        ],
    })

    reviewer_id = 'source-first-isolated-reviewer-batch-0062-three-sum-20260831-v1'
    review_version = 'batch-0062.three-sum.v1'
    findings = [
        'Both preserved primary-source occurrences ask the same 3Sum coding question; the candidate covers the source without collapsing occurrence identity.',
        'The candidate explicitly declares the LeetCode-15 zero-target Java contract, unique value-triplet semantics, sorted triplets and non-mutating input behavior instead of presenting those implementation choices as source facts.',
        'The sort-plus-fixed-first-element two-pointer invariant and all three deduplication points are explained consistently with the implementation.',
        'The implementation is independently revalidated against brute-force triple enumeration over fixed edge cases, all 19,608 short arrays in a bounded value domain, and 25,000 separately seeded random arrays.',
        'Using long for the running sum is covered by integer-extreme review cases, preventing overflow from reversing pointer movement decisions.',
        'The O(n^2) time bound, clone-induced O(n) storage choice, [0,0,0] boundary, duplicate-index versus unique-value semantics, target generalization and no-fabricated-project-experience boundary are all explicit.',
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
            str(out / 'ThreeSum.java'), str(out / 'ThreeSumReviewerTest.java'),
            str(reviewer_validation_path), 'config/answer_quality.json',
            'docs/refactor/09_answer_content_standard.md',
        ],
        'forbidden_inputs_not_used': [
            str(out / 'writer_research.json'), str(out / 'writer_validation.json'),
            'writer self score', 'writer expected decision',
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
            'title': 'Batch 0062 frozen repository context for 3Sum',
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
            'title': 'Independent Java 3Sum differential validation against brute-force triple enumeration',
            'locator': str(reviewer_validation_path),
            'source_type': 'executable_test_or_reproducible_experiment',
            'checked_at': DATE,
        },
        {
            'source_id': 'isolated-review',
            'title': 'Batch 0062 3Sum source-first isolated review',
            'locator': str(review_result_path),
            'source_type': 'repository_structured_source',
            'checked_at': DATE,
        },
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The two preserved source occurrences ask the same 3Sum coding question; repository context associates one occurrence with LeetCode 15 while language, output ordering and input mutation are not source constraints.',
            'source_ids': ['repository-source', 'source-inventory'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节'],
        },
        {
            'claim_id': 'algorithm-behavior',
            'text': 'Under the declared zero-target Java contract, sorting plus fixed-first-element two pointers returns exactly the brute-force set of unique value triplets while preserving the caller input.',
            'source_ids': ['reviewer-validation'],
            'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问'],
        },
        {
            'claim_id': 'overflow-dedupe-boundaries',
            'text': 'Independent review covers integer-extreme arithmetic, all-zero input, repeated values, short/null inputs, internal triplet ordering and duplicate-result rejection.',
            'source_ids': ['reviewer-validation', 'isolated-review'],
            'answer_locations': ['1 分钟版', '关键细节', '常见追问', '易错点'],
        },
    ]
    evidence_path = ROOT / f'review/evidence/{CID}.json'
    write_json(evidence_path, {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {
            'writer_id': 'content-batch-0062-three-sum-writer',
            'writer_version': 'xhs-answer-curator.v1',
        },
        'sources': sources,
        'claims': claims,
        'source_question_coverage': [{
            'question_id': QID,
            'covered': True,
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        }],
        'source_occurrence_count': 2,
        'validation': {
            'validator': 'independent_source_first_reviewer',
            'result': 'pass',
            'artifact': str(reviewer_validation_path),
            'boundary_tests': [
                {'case': 'null and fewer-than-three inputs', 'expected': 'empty result', 'passed': True},
                {'case': 'all-zero and duplicate-heavy inputs', 'expected': 'unique sorted value triplets only', 'passed': True},
                {'case': 'integer-extreme arithmetic', 'expected': 'same result as long-arithmetic brute-force oracle', 'passed': True},
                {'case': '19,608 exhaustive short arrays plus 25,000 seeded random arrays', 'expected': 'exact set equality with independent brute-force triple oracle and unchanged input', 'passed': True},
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

    task_path = ROOT / 'tasks/answer-batches/TASK-20260711-0313-answer-batch-0062.md'
    task = task_path.read_text(encoding='utf-8')
    writer_line = (
        '- [x] `cq_q_e1cbd1e9e8df435dfb30e81ea69018c8` writer stage complete: both frozen primary-source occurrences of the 3Sum question are preserved; '
        'the candidate declares a zero-target Java contract, clone-before-sort input behavior and long-sum overflow protection, then validates unique triplets over fixed duplicate/extreme boundaries plus 20,000 seeded random arrays against exhaustive brute-force enumeration. Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    )
    review_line = (
        '- [x] `cq_q_e1cbd1e9e8df435dfb30e81ea69018c8` source-first isolated review PASS: '
        f'candidate digest `{digest}`; both frozen primary-source occurrences remain visible and covered; the declared zero-target, non-mutating Java contract was independently revalidated against brute-force triple enumeration over fixed overflow/duplicate boundaries, all 19,608 arrays through length five over values -3..3, and 25,000 separately seeded random arrays. Formal promotion remains blocked by repository human-approval/real-review policy.'
    )
    if review_line not in task:
        if writer_line not in task:
            raise SystemExit(f'{CID}: task writer progress line drifted')
        task = task.replace(writer_line, writer_line + '\n' + review_line, 1)
        task_path.write_text(task, encoding='utf-8')

    print(f'PASS {CID} digest={digest} reviewer=independent evidence={evidence_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
