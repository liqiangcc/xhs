#!/usr/bin/env python3
"""Source-first isolated review for Batch 0062 longest common subsequence."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_6a7c7f58ad4a4828e2c984b668d7ba32'
QIDS = ['6a7c7f58ad4a4828e2c984b668d7ba32', 'b49c67887ac2b8fed060d5c61351f0c5']
EXPECTED_VARIANTS = {'算法：最长公共子序列（Dynamic Programming）？', '算法：最长公共子序列'}
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
EXPECTED_STDOUT = 'PASS reviewer fixed=8 exhaustive_binary_pairs=3969 random=12000 oracle=bruteforce-subsequence null=throws symmetry=preserved'


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run_reviewer_validation(out: Path) -> str:
    harness = out / 'LongestCommonSubsequenceReviewerTest.java'
    harness.write_text(r'''import java.util.*;
public final class LongestCommonSubsequenceReviewerTest {
  private static final Random RNG = new Random(0x62006A7CL ^ 0x5A5A5A5AL);
  private static final char[] ALPHABET = {'a','b','c'};
  private static boolean isSubsequence(String candidate, String target) {
    int i=0; for(int j=0;j<target.length()&&i<candidate.length();j++) if(candidate.charAt(i)==target.charAt(j)) i++; return i==candidate.length();
  }
  private static int bruteOracle(String a, String b) {
    String shorter=a.length()<=b.length()?a:b, other=a.length()<=b.length()?b:a; int n=shorter.length(), best=0, masks=1<<n;
    for(int mask=0;mask<masks;mask++){int bits=Integer.bitCount(mask); if(bits<=best) continue; StringBuilder sb=new StringBuilder(bits); for(int i=0;i<n;i++) if((mask&(1<<i))!=0) sb.append(shorter.charAt(i)); if(isSubsequence(sb.toString(),other)) best=bits;} return best;
  }
  private static void check(String a,String b,int expected,String label){int actual=LongestCommonSubsequence.lcsLength(a,b); if(actual!=expected) throw new AssertionError(label+" expected="+expected+" actual="+actual+" a="+a+" b="+b); int reverse=LongestCommonSubsequence.lcsLength(b,a); if(reverse!=expected) throw new AssertionError(label+" symmetry expected="+expected+" actual="+reverse);}
  private static List<String> allBinaryStringsUpToFive(){List<String> out=new ArrayList<>(); out.add(""); for(int len=1;len<=5;len++){int count=1<<len; for(int mask=0;mask<count;mask++){StringBuilder sb=new StringBuilder(len); for(int i=0;i<len;i++) sb.append(((mask>>i)&1)==0?'a':'b'); out.add(sb.toString());}} return out;}
  private static String randomString(int maxLen){int len=RNG.nextInt(maxLen+1); StringBuilder sb=new StringBuilder(len); for(int i=0;i<len;i++) sb.append(ALPHABET[RNG.nextInt(ALPHABET.length)]); return sb.toString();}
  public static void main(String[] args){
    check("","",0,"both-empty"); check("abc","",0,"one-empty"); check("abcde","ace",3,"classic"); check("abc","abc",3,"identical"); check("abc","def",0,"disjoint"); check("abc","bac",2,"cross-order"); check("aaaa","aa",2,"repeated"); check("XMJYAUZ","MZJAWXU",4,"nontrivial");
    boolean left=false,right=false; try{LongestCommonSubsequence.lcsLength(null,"x");}catch(IllegalArgumentException expected){left=true;} try{LongestCommonSubsequence.lcsLength("x",null);}catch(IllegalArgumentException expected){right=true;} if(!left||!right) throw new AssertionError("null contract must throw on either input");
    List<String> exhaustive=allBinaryStringsUpToFive(); int pairCount=0; for(String a:exhaustive) for(String b:exhaustive){int expected=bruteOracle(a,b); check(a,b,expected,"exhaustive-"+pairCount); pairCount++;} if(pairCount!=3969) throw new AssertionError("unexpected exhaustive pair count="+pairCount);
    for(int i=0;i<12000;i++){String a=randomString(10),b=randomString(10); check(a,b,bruteOracle(a,b),"random-"+i);} System.out.println("PASS reviewer fixed=8 exhaustive_binary_pairs=3969 random=12000 oracle=bruteforce-subsequence null=throws symmetry=preserved");
  }
}
''', encoding='utf-8')
    proc = subprocess.run(['bash','-lc','javac LongestCommonSubsequence.java LongestCommonSubsequenceReviewerTest.java && java LongestCommonSubsequenceReviewerTest'], cwd=out, text=True, capture_output=True, check=False)
    if proc.returncode != 0: raise SystemExit(f'{CID}: independent reviewer validation failed: {proc.stderr or proc.stdout}')
    stdout=proc.stdout.strip()
    if stdout != EXPECTED_STDOUT: raise SystemExit(f'{CID}: reviewer stdout drift: {stdout!r}')
    for class_file in out.glob('*.class'): class_file.unlink()
    return stdout


def main() -> int:
    inventory_path=ROOT/f'review/content_build/answer_batch_{BATCH}/source_inventory.json'; inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result')!='pass': raise SystemExit('batch 0062 source inventory is not passing')
    item=next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id')==CID),None)
    if not item or item.get('answer_type')!='coding': raise SystemExit(f'{CID}: missing or non-coding source inventory row')
    if sorted(item.get('question_ids') or [])!=sorted(QIDS): raise SystemExit(f'{CID}: frozen ownership drift')
    if item.get('source_question_count')!=2 or item.get('source_occurrence_count')!=2: raise SystemExit(f'{CID}: occurrence-aware inventory drift')
    if {x.get('original_question') for x in item.get('source_questions',[])}!=EXPECTED_VARIANTS: raise SystemExit(f'{CID}: source wording drift')
    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}'; context_path=out/'context.json'; context=json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type')!='coding': raise SystemExit(f'{CID}: frozen context/type drift')
    canonical=context.get('canonical') or {}
    if canonical.get('canonical_id')!=CID or sorted(canonical.get('question_ids') or [])!=sorted(QIDS): raise SystemExit(f'{CID}: context ownership drift')
    source_rows=list(context.get('source_questions') or [])
    if len(source_rows)!=2 or {x.get('original_question') for x in source_rows}!=EXPECTED_VARIANTS: raise SystemExit(f'{CID}: context source variants drift')
    occurrence_ids={(x.get('question_id'),x.get('source_note_id'),x.get('source_question_index'),x.get('original_question')) for x in source_rows}
    if len(occurrence_ids)!=2: raise SystemExit(f'{CID}: source occurrence identity collapsed')
    candidate_path=ROOT/f'review/candidates/answers/{CID}.md'; candidate=candidate_path.read_text(encoding='utf-8'); digest=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    for heading in HEADINGS:
        if candidate.count(heading)!=1: raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if candidate.count('- 问：')<5: raise SystemExit(f'{CID}: question-specific follow-up coverage too small')
    required=['最长公共子序列','子串','dp[i][j]','prevDiag','oldUp','O(m * n)','O(min(m, n))','重复字符','恢复序列','UTF-16','dp[j] = Math.max(dp[j], dp[j - 1])']
    missing=[x for x in required if x not in candidate]
    if missing: raise SystemExit(f'{CID}: DP/invariant/boundary coverage missing: {missing}')
    one_minute=candidate.split('## 1 分钟版',1)[1].split('## 3 分钟版',1)[0]; points=sum(1 for line in one_minute.splitlines() if line.startswith('- '))
    if not (3<=points<=5): raise SystemExit(f'{CID}: one-minute point count must be 3..5, got {points}')
    stdout=run_reviewer_validation(out); reviewer_validation_path=out/'reviewer_validation.json'
    write_json(reviewer_validation_path,{'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'validator':'independent_source_first_reviewer','command':'javac LongestCommonSubsequence.java LongestCommonSubsequenceReviewerTest.java && java LongestCommonSubsequenceReviewerTest','stdout':stdout,'checks':['eight fixed empty/identical/disjoint/cross-order/repeated/nontrivial cases','both null-input positions reject according to the declared candidate contract','all 3,969 pairs of binary strings of length at most five match a brute-force subsequence oracle','12,000 independently seeded random pairs up to length ten match the brute-force subsequence oracle','symmetry lcs(a,b) == lcs(b,a) is checked throughout']})
    reviewer_id='source-first-isolated-reviewer-batch-0062-lcs-20260831-v1'; review_version='batch-0062.lcs.v1'
    findings=['Both frozen primary-source variants ask for longest common subsequence, with one explicitly naming dynamic programming; both are directly covered.','The candidate explicitly declares a Java non-null, length-only contract rather than inventing language, null, reconstruction, size or Unicode requirements from the source.','The state meaning and both recurrence branches are explained, including why mismatch compares the upper and left prefix states.','The one-dimensional compression invariant is explicit: dp[j] is the old upper state before overwrite, dp[j-1] is the current-row left state, and prevDiag preserves the old diagonal.','The runnable implementation is independently revalidated using brute-force subsequence enumeration rather than the writer two-dimensional-DP oracle, including exhaustive short binary inputs and 12,000 random pairs.','The answer distinguishes subsequence from substring, preserves repeated-position semantics, states O(m*n) time/O(min(m,n)) DP space, and separates length-only output from reconstruction and Unicode code-point contracts.']
    review_result_path=out/'isolated_review_result.json'; write_json(review_result_path,{'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer_id,'review_version':review_version,'decision':'pass','revision_round':1,'source_packet':[str(context_path),str(inventory_path),str(candidate_path),str(out/'LongestCommonSubsequence.java'),str(out/'LongestCommonSubsequenceReviewerTest.java'),str(reviewer_validation_path),'config/answer_quality.json','docs/refactor/09_answer_content_standard.md'],'forbidden_inputs_not_used':[str(out/'writer_research.json'),str(out/'writer_validation.json'),'writer self score','writer expected decision'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':[PROMOTION_BLOCKER]})
    sources=[{'source_id':'repository-source','title':'Batch 0062 frozen repository context for longest common subsequence','locator':str(context_path),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'source-inventory','title':'Batch 0062 occurrence-aware frozen source inventory','locator':str(inventory_path),'source_type':'repository_structured_source','checked_at':DATE},{'source_id':'reviewer-validation','title':'Independent LCS brute-force subsequence differential validation','locator':str(reviewer_validation_path),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},{'source_id':'isolated-review','title':'Batch 0062 LCS source-first isolated review','locator':str(review_result_path),'source_type':'repository_structured_source','checked_at':DATE}]
    claims=[{'claim_id':'source-boundary','text':'The two frozen source occurrences ask for longest common subsequence, with one explicitly naming dynamic programming, and do not prescribe Java, null handling, sequence reconstruction, size or Unicode semantics.','source_ids':['repository-source','source-inventory'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节']},{'claim_id':'lcs-contract','text':'Under the declared Java length-only contract, the one-dimensional DP returns the same LCS length as independent brute-force subsequence enumeration across fixed, exhaustive short binary and 12,000 random cases, and rejects null inputs as declared.','source_ids':['reviewer-validation'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制']},{'claim_id':'boundaries','text':'The independently validated behavior covers empty, repeated and crossing-order inputs while the answer explicitly distinguishes substring, reconstruction and UTF-16/code-point boundaries.','source_ids':['reviewer-validation','isolated-review'],'answer_locations':['关键细节','原理机制','常见追问','易错点']}]
    locations=['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']; coverage=[{'question_id':qid,'covered':True,'answer_locations':locations} for qid in QIDS]
    boundary_tests=[{'case':'empty input on one or both sides','expected':'LCS length 0','passed':True},{'case':'repeated characters such as aaaa vs aa','expected':'position-preserving LCS length 2','passed':True},{'case':'cross-order and disjoint strings','expected':'match brute-force subsequence oracle','passed':True},{'case':'all 3,969 binary-string pairs up to length five plus 12,000 random pairs','expected':'exact match with independent brute-force oracle and symmetry','passed':True},{'case':'null on either argument','expected':'IllegalArgumentException according to explicit contract','passed':True}]
    write_json(ROOT/f'review/evidence/{CID}.json',{'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0062-lcs-writer','writer_version':'xhs-answer-curator.v1'},'sources':sources,'claims':claims,'source_question_coverage':coverage,'source_occurrence_count':2,'validation':{'validator':'independent_source_first_reviewer','result':'pass','artifact':str(reviewer_validation_path),'boundary_tests':boundary_tests},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer_id,'review_version':review_version,'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},'promotion_blocker':PROMOTION_BLOCKER})
    task_path=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'; task=task_path.read_text(encoding='utf-8').rstrip(); line=f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; both frozen LCS source variants are covered; the declared length-only Java DP contract was independently revalidated by brute-force subsequence enumeration over 3,969 exhaustive short binary pairs and 12,000 seeded random pairs. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in task: task_path.write_text(task+'\n'+line+'\n',encoding='utf-8')
    print(EXPECTED_STDOUT); return 0

if __name__=='__main__': raise SystemExit(main())
