#!/usr/bin/env python3
"""Source-first isolated review for Batch 0062 Two Sum."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_ffe5f2da4a3ce9f56c51bce699ab1b13'
QID = 'ffe5f2da4a3ce9f56c51bce699ab1b13'
EXPECTED_QUESTION = '算法：两数之和'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
EXPECTED_REVIEW_STDOUT = 'PASS reviewer fixed=10 exhaustive=35154 random=35000 oracle=earliest-right-bruteforce overflow=pass input_unchanged=pass'


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run_reviewer_validation(out: Path) -> str:
    harness = out / 'TwoSumReviewerTest.java'
    harness.write_text(r'''import java.util.*;

public final class TwoSumReviewerTest {
    private static final Random RNG = new Random(0x62FFE5F3L);
    private static int exhaustiveCases = 0;

    private static void fail(String m) { throw new AssertionError(m); }

    private static int[] oracle(int[] nums, int target) {
        if (nums == null || nums.length < 2) return new int[0];
        for (int j=0; j<nums.length; j++) {
            for (int i=0; i<j; i++) {
                if ((long)nums[i] + nums[j] == target) return new int[]{i,j};
            }
        }
        return new int[0];
    }

    private static void check(int[] nums, int target, String label) {
        int[] before = nums == null ? null : nums.clone();
        int[] expected = oracle(nums,target);
        int[] actual = TwoSum.twoSum(nums,target);
        if (!Arrays.equals(actual,expected)) fail(label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
        if (actual.length != 0) {
            if (actual.length != 2 || actual[0] < 0 || actual[0] >= actual[1] || actual[1] >= nums.length) fail(label + " invalid indices");
            if ((long)nums[actual[0]] + nums[actual[1]] != target) fail(label + " wrong sum");
        }
        if (nums != null && !Arrays.equals(nums,before)) fail(label + " mutated input");
    }

    private static void enumerate(int[] a, int pos) {
        if (pos == a.length) {
            for (int target=-4; target<=4; target++) {
                exhaustiveCases++;
                check(a.clone(),target,"exhaustive-"+exhaustiveCases);
            }
            return;
        }
        for (int v=-2; v<=2; v++) { a[pos]=v; enumerate(a,pos+1); }
    }

    private static int randomValue() {
        int m=RNG.nextInt(24);
        if(m==0) return Integer.MIN_VALUE;
        if(m==1) return Integer.MAX_VALUE;
        return RNG.nextInt(121)-60;
    }

    public static void main(String[] args) {
        check(new int[]{2,7,11,15},9,"classic");
        check(new int[]{3,2,4},6,"middle-pair");
        check(new int[]{3,3},6,"duplicates");
        check(new int[]{1,2,3,4},100,"none");
        check(new int[]{1,4,2,3},5,"multiple");
        check(new int[]{1,1,4},5,"earliest-left");
        check(new int[]{Integer.MIN_VALUE,0,Integer.MAX_VALUE},-1,"extreme-valid");
        check(new int[]{Integer.MAX_VALUE,-1,0},Integer.MIN_VALUE,"overflow-no-false-hit");
        check(new int[]{7},14,"single");
        check(null,0,"null");

        for(int n=0;n<=5;n++) enumerate(new int[n],0);
        if(exhaustiveCases!=35154) fail("exhaustive count drift: "+exhaustiveCases);

        for(int t=0;t<35000;t++) {
            int n=RNG.nextInt(20); int[] a=new int[n];
            for(int i=0;i<n;i++) a[i]=randomValue();
            int m=RNG.nextInt(20); int target=m==0?Integer.MIN_VALUE:m==1?Integer.MAX_VALUE:RNG.nextInt(241)-120;
            check(a,target,"random-"+t);
        }
        System.out.println("PASS reviewer fixed=10 exhaustive=35154 random=35000 oracle=earliest-right-bruteforce overflow=pass input_unchanged=pass");
    }
}
''', encoding='utf-8')
    proc=subprocess.run(['bash','-lc','javac TwoSum.java TwoSumReviewerTest.java && java TwoSumReviewerTest'],cwd=out,text=True,capture_output=True,check=False)
    if proc.returncode != 0: raise SystemExit(f'{CID}: independent reviewer validation failed: {proc.stderr or proc.stdout}')
    stdout=proc.stdout.strip()
    if stdout != EXPECTED_REVIEW_STDOUT: raise SystemExit(f'{CID}: reviewer stdout drift: {stdout!r}')
    for f in out.glob('*.class'): f.unlink()
    return stdout


def main() -> int:
    inventory_path=ROOT/f'review/content_build/answer_batch_{BATCH}/source_inventory.json'
    inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result')!='pass': raise SystemExit('batch 0062 source inventory is not passing')
    item=next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id')==CID),None)
    if not item or item.get('answer_type')!='coding': raise SystemExit(f'{CID}: missing/non-coding inventory item')
    if item.get('question_ids') != [QID] or item.get('source_question_count') != 1 or item.get('source_occurrence_count') != 2: raise SystemExit(f'{CID}: inventory ownership/occurrence drift')
    if {x.get('original_question') for x in item.get('source_questions',[])} != {EXPECTED_QUESTION}: raise SystemExit(f'{CID}: source wording drift')

    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}'
    context_path=out/'context.json'; context=json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type')!='coding': raise SystemExit(f'{CID}: context/type drift')
    canonical=context.get('canonical') or {}
    if canonical.get('canonical_id')!=CID or canonical.get('question_ids')!=[QID]: raise SystemExit(f'{CID}: context ownership drift')
    rows=list(context.get('source_questions') or [])
    if len(rows)!=2 or {x.get('original_question') for x in rows}!={EXPECTED_QUESTION}: raise SystemExit(f'{CID}: source occurrence drift')
    if len({(x.get('question_id'),x.get('source_note_id'),x.get('source_question_index')) for x in rows})!=2: raise SystemExit(f'{CID}: source occurrences collapsed')

    candidate_path=ROOT/f'review/candidates/answers/{CID}.md'; candidate=candidate_path.read_text(encoding='utf-8'); digest=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    for h in HEADINGS:
        if candidate.count(h)!=1: raise SystemExit(f'{CID}: candidate section drift: {h}')
    if candidate.count('- 问：')<5: raise SystemExit(f'{CID}: follow-up coverage too small')
    required=['HashMap','putIfAbsent','needLong','Integer.MIN_VALUE','Integer.MAX_VALUE','先查后放','O(n)','O(n^2)','不同下标','不修改','无解','重复值']
    missing=[x for x in required if x not in candidate]
    if missing: raise SystemExit(f'{CID}: required algorithm/boundary coverage missing: {missing}')
    one=candidate.split('## 1 分钟版',1)[1].split('## 3 分钟版',1)[0]
    points=sum(1 for line in one.splitlines() if line.startswith('- '))
    if not (4<=points<=6): raise SystemExit(f'{CID}: one-minute point count must be 4..6, got {points}')

    stdout=run_reviewer_validation(out)
    reviewer_validation_path=out/'reviewer_validation.json'
    write_json(reviewer_validation_path,{'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'validator':'independent_source_first_reviewer','command':'javac TwoSum.java TwoSumReviewerTest.java && java TwoSumReviewerTest','stdout':stdout,'checks':['fixed duplicate/multi-solution/no-solution/null/extreme boundaries match deterministic brute-force oracle','all 35,154 combinations of arrays through length five over -2..2 and targets -4..4 match the oracle','35,000 independently seeded random arrays/targets match the oracle','returned indices are ordered, distinct, in range and sum to target','input arrays remain unchanged and overflow cannot synthesize a false complement']})

    reviewer_id='source-first-isolated-reviewer-batch-0062-two-sum-20260831-v1'; review_version='batch-0062.two-sum.v1'
    findings=['Both preserved primary-source occurrences ask the same Two Sum question and remain occurrence-distinct while sharing one normalized Question ID.','The candidate clearly labels API, deterministic multi-solution selection, no-solution behavior and index-return semantics as its executable contract rather than source facts.','The prefix-hash invariant is correct: lookup occurs before insertion, so a returned pair always uses two distinct positions; putIfAbsent preserves the earliest historical complement index.','Independent validation matches an earliest-right brute-force oracle on fixed cases, 35,154 exhaustive short array/target combinations and 35,000 separately seeded random cases.','Long complement arithmetic plus int-range checking is independently exercised on integer extremes, preventing overflow-induced false hits.','Expected O(n) hash time/O(n) space, the O(n^2) brute-force tradeoff, duplicate values, null/no-solution boundaries and non-mutating input behavior are explicit without fabricated production experience.']
    review_result_path=out/'isolated_review_result.json'
    write_json(review_result_path,{'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer_id,'review_version':review_version,'decision':'pass','revision_round':1,'source_packet':[str(context_path),str(inventory_path),str(candidate_path),str(out/'TwoSum.java'),str(out/'TwoSumReviewerTest.java'),str(reviewer_validation_path),'config/answer_quality.json','docs/refactor/09_answer_content_standard.md'],'forbidden_inputs_not_used':[str(out/'writer_research.json'),str(out/'writer_validation.json'),'writer self score','writer expected decision'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':[PROMOTION_BLOCKER]})

    sources=[{'source_id':'repository-source','title':'Batch 0062 frozen repository context for Two Sum','locator':str(context_path),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'source-inventory','title':'Batch 0062 occurrence-aware frozen source inventory','locator':str(inventory_path),'source_type':'repository_structured_source','checked_at':DATE},{'source_id':'reviewer-validation','title':'Independent Java Two Sum differential validation against deterministic brute-force oracle','locator':str(reviewer_validation_path),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},{'source_id':'isolated-review','title':'Batch 0062 Two Sum source-first isolated review','locator':str(review_result_path),'source_type':'repository_structured_source','checked_at':DATE}]
    claims=[{'claim_id':'source-boundary','text':'The two preserved source occurrences ask only for Two Sum; API, target guarantees, no-solution behavior, return form and multi-answer selection are not source constraints.','source_ids':['repository-source','source-inventory'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节']},{'claim_id':'hash-prefix-contract','text':'Under the declared Java contract, lookup-before-insert with first-occurrence preservation returns the deterministic earliest-right valid index pair and never reuses the current element.','source_ids':['reviewer-validation'],'answer_locations':['3 分钟版','关键细节','原理机制','常见追问']},{'claim_id':'overflow-boundary','text':'Independent review covers duplicate values, multiple/no solutions, null/short inputs, integer-extreme complement arithmetic and input immutability.','source_ids':['reviewer-validation','isolated-review'],'answer_locations':['1 分钟版','关键细节','常见追问','易错点']}]
    evidence_path=ROOT/f'review/evidence/{CID}.json'
    write_json(evidence_path,{'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0062-two-sum-writer','writer_version':'xhs-answer-curator.v1'},'sources':sources,'claims':claims,'source_question_coverage':[{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}],'source_occurrence_count':2,'validation':{'validator':'independent_source_first_reviewer','result':'pass','artifact':str(reviewer_validation_path),'boundary_tests':[{'case':'null/short/no-solution','expected':'empty result','passed':True},{'case':'duplicates and multiple solutions','expected':'deterministic earliest-right/earliest-complement valid pair','passed':True},{'case':'integer extremes','expected':'same pair as long-arithmetic brute-force oracle without false complement','passed':True},{'case':'35,154 exhaustive plus 35,000 random cases','expected':'exact index-array equality with independent deterministic oracle and unchanged input','passed':True}]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer_id,'review_version':review_version,'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},'promotion_blocker':PROMOTION_BLOCKER})

    task_path=ROOT/'tasks/answer-batches/TASK-20260711-0313-answer-batch-0062.md'; task=task_path.read_text(encoding='utf-8')
    writer_line='- [x] `cq_q_ffe5f2da4a3ce9f56c51bce699ab1b13` writer stage complete: both frozen primary-source occurrences of the Two Sum question are preserved; the candidate declares a deterministic Java index-pair/no-solution/non-mutating contract, uses a prefix HashMap with overflow-safe complement arithmetic, and validates fixed duplicate/multi-solution/extreme boundaries plus 30,000 seeded random arrays against an earliest-right brute-force oracle. Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    review_line=f'- [x] `cq_q_ffe5f2da4a3ce9f56c51bce699ab1b13` source-first isolated review PASS: candidate digest `{digest}`; both frozen primary-source occurrences remain visible and covered; the declared deterministic Java index-pair contract was independently revalidated against an earliest-right brute-force oracle over fixed overflow/duplicate/multi-solution boundaries, 35,154 exhaustive short array/target combinations, and 35,000 separately seeded random cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if review_line not in task:
        if writer_line not in task: raise SystemExit(f'{CID}: task writer progress line drifted')
        task=task.replace(writer_line,writer_line+'\n'+review_line,1); task_path.write_text(task,encoding='utf-8')
    print(f'PASS {CID} digest={digest} reviewer=independent evidence={evidence_path}')
    return 0

if __name__=='__main__': raise SystemExit(main())
