#!/usr/bin/env python3
"""Source-first isolated review for Batch 0062 remove-nth-from-end candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_d0b70d126320ddd7e4a234f0f3c6066f'
QIDS = ['d0b70d126320ddd7e4a234f0f3c6066f']
EXPECTED_VARIANT = '算法手撕：删除链表倒数第 N 个元素。'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
EXPECTED_STDOUT = 'PASS reviewer fixed=12 random_cases=40000 oracle=two-pass-count invalid_n=pass head_delete=pass tail_delete=pass'


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run_reviewer_validation(out: Path) -> str:
    harness = out / 'RemoveNthReviewerTest.java'
    harness.write_text(r'''import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class RemoveNthReviewerTest {
    private static final Random RNG = new Random(0xD0B70D62L ^ 0x71A9E55L);

    static RemoveNthFromEnd.ListNode build(int[] values) {
        RemoveNthFromEnd.ListNode dummy = new RemoveNthFromEnd.ListNode(0), tail = dummy;
        for (int value : values) { tail.next = new RemoveNthFromEnd.ListNode(value); tail = tail.next; }
        return dummy.next;
    }

    static int[] values(RemoveNthFromEnd.ListNode head) {
        List<Integer> list = new ArrayList<>();
        for (RemoveNthFromEnd.ListNode p = head; p != null; p = p.next) list.add(p.val);
        int[] out = new int[list.size()];
        for (int i = 0; i < out.length; i++) out[i] = list.get(i);
        return out;
    }

    // Independent two-pass reference: first count length, then skip the 0-based target position.
    static int[] twoPassOracle(int[] input, int n) {
        int length = 0;
        for (int ignored : input) length++;
        int target = length - n;
        int[] out = new int[length - 1];
        int j = 0;
        for (int i = 0; i < length; i++) {
            if (i != target) out[j++] = input[i];
        }
        return out;
    }

    static void eq(int[] expected, int[] actual, String label) {
        if (!Arrays.equals(expected, actual)) {
            throw new AssertionError(label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
        }
    }

    static void fixed(int[] input, int n, int[] expected, String label) {
        eq(expected, values(RemoveNthFromEnd.removeNthFromEnd(build(input), n)), label);
    }

    public static void main(String[] args) {
        fixed(new int[]{1}, 1, new int[]{}, "single");
        fixed(new int[]{1,2}, 1, new int[]{1}, "tail-two");
        fixed(new int[]{1,2}, 2, new int[]{2}, "head-two");
        fixed(new int[]{1,2,3}, 2, new int[]{1,3}, "middle-three");
        fixed(new int[]{1,2,3,4,5}, 2, new int[]{1,2,3,5}, "example");
        fixed(new int[]{1,2,3,4,5}, 5, new int[]{2,3,4,5}, "head-five");
        fixed(new int[]{1,2,3,4,5}, 1, new int[]{1,2,3,4}, "tail-five");
        fixed(new int[]{7,7,7,7}, 3, new int[]{7,7,7}, "duplicates");
        fixed(new int[]{-3,-2,-1,0,1}, 4, new int[]{-3,-1,0,1}, "negative-values");
        fixed(new int[]{9,8,7,6}, 3, new int[]{9,7,6}, "middle-four");
        fixed(new int[]{42,5,42,5}, 4, new int[]{5,42,5}, "head-duplicate");
        fixed(new int[]{0,0,1,0,0}, 2, new int[]{0,0,1,0}, "zero-values");

        boolean bad0=false, badNeg=false, badLarge=false, badEmpty=false;
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1}), 0); } catch (IllegalArgumentException expected) { bad0=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1}), -7); } catch (IllegalArgumentException expected) { badNeg=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(build(new int[]{1,2}), 3); } catch (IllegalArgumentException expected) { badLarge=true; }
        try { RemoveNthFromEnd.removeNthFromEnd(null, 1); } catch (IllegalArgumentException expected) { badEmpty=true; }
        if (!bad0 || !badNeg || !badLarge || !badEmpty) throw new AssertionError("declared invalid-input contract not enforced");

        int cases = 0;
        for (int t = 0; t < 40000; t++) {
            int len = 1 + RNG.nextInt(55);
            int n = 1 + RNG.nextInt(len);
            int[] input = new int[len];
            for (int i = 0; i < len; i++) input[i] = RNG.nextInt(31) - 15;
            int[] expected = twoPassOracle(input, n);
            int[] actual = values(RemoveNthFromEnd.removeNthFromEnd(build(input), n));
            eq(expected, actual, "random-" + t);
            cases++;
        }
        if (cases != 40000) throw new AssertionError("unexpected random case count " + cases);
        System.out.println("PASS reviewer fixed=12 random_cases=40000 oracle=two-pass-count invalid_n=pass head_delete=pass tail_delete=pass");
    }
}
''', encoding='utf-8')
    proc = subprocess.run(['bash','-lc','javac RemoveNthFromEnd.java RemoveNthReviewerTest.java && java RemoveNthReviewerTest'], cwd=out, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise SystemExit(f'{CID}: independent reviewer validation failed: {proc.stderr or proc.stdout}')
    stdout = proc.stdout.strip()
    if stdout != EXPECTED_STDOUT:
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
    if not item or item.get('answer_type') != 'coding' or item.get('question_ids') != QIDS:
        raise SystemExit(f'{CID}: frozen inventory/type/ownership drift')
    source_rows = list(item.get('source_questions') or [])
    if item.get('source_question_count') != 1 or item.get('source_occurrence_count') != 2 or len(source_rows) != 2:
        raise SystemExit(f'{CID}: occurrence-aware source inventory drift')
    if any(x.get('question_id') != QIDS[0] or x.get('original_question') != EXPECTED_VARIANT for x in source_rows):
        raise SystemExit(f'{CID}: source wording/identity drift')
    if len({(x.get('source_note_id'), x.get('source_question_index')) for x in source_rows}) != 2:
        raise SystemExit(f'{CID}: duplicate primary-source occurrences collapsed')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context_path = out / 'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    canonical = context.get('canonical') or {}
    if not context.get('ok') or context.get('answer_type') != 'coding' or canonical.get('canonical_id') != CID or canonical.get('question_ids') != QIDS:
        raise SystemExit(f'{CID}: frozen context drift')
    context_rows = list(context.get('source_questions') or [])
    if len(context_rows) != 2 or any(x.get('question_id') != QIDS[0] or x.get('original_question') != EXPECTED_VARIANT for x in context_rows):
        raise SystemExit(f'{CID}: context source occurrence drift')
    if len({(x.get('source_note_id'), x.get('source_question_index')) for x in context_rows}) != 2:
        raise SystemExit(f'{CID}: context occurrence identity collapsed')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate = candidate_path.read_text(encoding='utf-8')
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    for heading in HEADINGS:
        if candidate.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if candidate.count('- 问：') < 5:
        raise SystemExit(f'{CID}: question-specific follow-up coverage too small')
    required = ['dummy', 'fast', 'slow', 'fast = dummy', 'slow.next = slow.next.next', 'n <= 0', 'n exceeds list length', 'IllegalArgumentException', '`O(L)`', '`O(1)`']
    missing = [token for token in required if token not in candidate]
    if missing:
        raise SystemExit(f'{CID}: algorithm invariant/boundary coverage missing: {missing}')
    one_minute = candidate.split('## 1 分钟版', 1)[1].split('## 3 分钟版', 1)[0]
    points = sum(1 for line in one_minute.splitlines() if line.startswith('- '))
    if not (4 <= points <= 6):
        raise SystemExit(f'{CID}: one-minute point count must be 4..6, got {points}')

    stdout = run_reviewer_validation(out)
    reviewer_validation_path = out / 'reviewer_validation.json'
    write_json(reviewer_validation_path, {
        'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,
        'validator':'independent_source_first_reviewer',
        'command':'javac RemoveNthFromEnd.java RemoveNthReviewerTest.java && java RemoveNthReviewerTest',
        'stdout':stdout,
        'checks':['fixed single/head/tail/middle/duplicate/value boundaries distinguish the intended predecessor-position logic','declared n<=0, n>length and empty-list behavior is enforced','40,000 independently seeded valid removals match an independent two-pass length-count oracle']
    })

    reviewer_id = 'source-first-isolated-reviewer-batch-0062-remove-nth-20260831-v1'
    review_version = 'batch-0062.remove-nth.v1'
    findings = [
        'Both frozen primary-source occurrences carry the same remove-Nth-from-end linked-list question and remain distinct occurrence records; the source does not prescribe language, node API or invalid-n behavior.',
        'The candidate directly answers the linked-list problem using a dummy predecessor and fixed-gap fast/slow pointers, including why slow must stop before the deleted node.',
        'The IllegalArgumentException behavior for non-positive n, empty input and n greater than list length is explicitly labeled as an answer-level contract rather than a source fact.',
        'Head deletion (n equals length), tail deletion (n equals one), middle deletion and single-node deletion all follow the same dummy-based pointer path without an unsupported special-case claim.',
        'The executable implementation is independently revalidated with a two-pass length-count oracle on 40,000 random lists using a reviewer-only seed, rather than reusing the writer oracle result.',
        'The stated O(L) time and O(1) extra-space bounds match the pointer implementation and do not depend on hidden length-sized auxiliary structures.'
    ]
    review_result_path = out / 'isolated_review_result.json'
    write_json(review_result_path, {
        'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,
        'review_mode':'source_first_isolated','reviewer_id':reviewer_id,'review_version':review_version,'decision':'pass','revision_round':1,
        'source_packet':[str(context_path),str(inventory_path),str(candidate_path),str(out/'RemoveNthFromEnd.java'),str(out/'RemoveNthReviewerTest.java'),str(reviewer_validation_path),'config/answer_quality.json','docs/refactor/09_answer_content_standard.md'],
        'forbidden_inputs_not_used':[str(out/'writer_research.json'),str(out/'writer_validation.json'),'writer self score','writer expected decision','historical review/remediation records'],
        'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':[PROMOTION_BLOCKER]
    })

    sources = [
        {'source_id':'repository-source','title':'Batch 0062 frozen repository context for remove-Nth-from-end','locator':str(context_path),'source_type':'repository_source_record','checked_at':DATE},
        {'source_id':'source-inventory','title':'Batch 0062 occurrence-aware frozen source inventory','locator':str(inventory_path),'source_type':'repository_structured_source','checked_at':DATE},
        {'source_id':'reviewer-validation','title':'Independent remove-Nth two-pass differential validation','locator':str(reviewer_validation_path),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
        {'source_id':'isolated-review','title':'Batch 0062 remove-Nth source-first isolated review','locator':str(review_result_path),'source_type':'repository_structured_source','checked_at':DATE},
    ]
    claims = [
        {'claim_id':'source-boundary','text':'The two preserved primary-source occurrences ask to remove the Nth element from the end of a linked list and do not prescribe Java, node API or invalid-n semantics.','source_ids':['repository-source','source-inventory'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节']},
        {'claim_id':'algorithm-contract','text':'Under the declared Java contract, dummy plus fixed-gap fast/slow pointers correctly delete head, tail, middle and single-node targets and match an independent two-pass oracle on 40,000 random cases.','source_ids':['reviewer-validation'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制']},
        {'claim_id':'boundaries','text':'Independent validation covers non-positive n, n exceeding length, empty input and valid extreme n values while the answer keeps ownership/concurrency concerns outside the source contract.','source_ids':['reviewer-validation','isolated-review'],'answer_locations':['关键细节','项目经验版','常见追问','易错点']},
    ]
    locations = ['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']
    coverage = [{'question_id':QIDS[0],'covered':True,'answer_locations':locations}]
    boundary_tests = [
        {'case':'two preserved source occurrences','expected':'both remain visible and map to the same canonical without collapsing occurrence provenance','passed':True},
        {'case':'n equals list length','expected':'original head is removed through dummy predecessor','passed':True},
        {'case':'n equals one','expected':'tail is removed','passed':True},
        {'case':'single-node list','expected':'result is empty list','passed':True},
        {'case':'n <= 0, n > length, empty input','expected':'IllegalArgumentException according to explicit candidate contract','passed':True},
        {'case':'40,000 seeded random valid removals','expected':'exact agreement with independent two-pass length-count oracle','passed':True},
    ]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,
        'writer':{'writer_id':'content-batch-0062-remove-nth-writer','writer_version':'xhs-answer-curator.v1'},
        'sources':sources,'claims':claims,'source_question_coverage':coverage,'source_occurrence_count':2,
        'validation':{'validator':'independent_source_first_reviewer','result':'pass','artifact':str(reviewer_validation_path),'boundary_tests':boundary_tests},
        'review_state':'independent_source_first_review_passed',
        'review':{'reviewer_id':reviewer_id,'review_version':review_version,'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},
        'promotion_blocker':PROMOTION_BLOCKER,
    })

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    line = f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; both frozen duplicate primary-source occurrences remain visible and are covered; dummy + fixed-gap fast/slow deletion was independently revalidated over head/tail/single/invalid-input boundaries plus 40,000 seeded random lists against a two-pass length-count oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in task:
        task_path.write_text(task + '\n' + line + '\n', encoding='utf-8')
    print(EXPECTED_STDOUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
