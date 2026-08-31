#!/usr/bin/env python3
"""Source-first isolated review for Batch 0062 longest valid parentheses."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_6c5a986936f3d831fd8dc544ccd71910'
QIDS = ['6c5a986936f3d831fd8dc544ccd71910', '7c79cd047d29e5f6cafd84e396f0de8f']
EXPECTED_VARIANTS = {
    '算法手撕：最长有效括号（Longest Valid Parentheses）。',
    '算法手撕：最长有效括号（Longest Valid Parentheses）- 动态规划/栈 Hard。',
}
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
EXPECTED_STDOUT = 'PASS reviewer fixed=14 exhaustive=8191 random=20000 oracle=quadratic-balance-scan null=throws invalid=throws'


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run_reviewer_validation(out: Path) -> str:
    harness = out / 'LongestValidParenthesesReviewerTest.java'
    harness.write_text(r'''import java.util.Random;

public final class LongestValidParenthesesReviewerTest {
  private static final Random RNG = new Random(0x62006C5AL ^ 0x51A7E2L);
  private static int oracle(String s) {
    int best = 0;
    for (int start = 0; start < s.length(); start++) {
      int balance = 0;
      for (int end = start; end < s.length(); end++) {
        char ch = s.charAt(end);
        if (ch == '(') balance++;
        else if (ch == ')') balance--;
        else throw new IllegalArgumentException("oracle expects parentheses only");
        if (balance < 0) break;
        if (balance == 0) best = Math.max(best, end - start + 1);
      }
    }
    return best;
  }
  private static void check(String s, int expected, String label) {
    int actual = LongestValidParentheses.longestValidParentheses(s);
    if (actual != expected) throw new AssertionError(label + " expected=" + expected + " actual=" + actual + " s=" + s);
  }
  private static String fromMask(int len, int mask) {
    StringBuilder sb = new StringBuilder(len);
    for (int i = 0; i < len; i++) sb.append(((mask >>> i) & 1) == 0 ? '(' : ')');
    return sb.toString();
  }
  private static String randomString(int maxLen) {
    int len = RNG.nextInt(maxLen + 1);
    StringBuilder sb = new StringBuilder(len);
    for (int i = 0; i < len; i++) sb.append(RNG.nextBoolean() ? '(' : ')');
    return sb.toString();
  }
  public static void main(String[] args) {
    String[] fixed = {"", "(", ")", "()", "(()", ")()())", "()(())", "((()))", "()(()", "())()", "(()())", "())(())", "()()()", "((())())"};
    for (int i = 0; i < fixed.length; i++) check(fixed[i], oracle(fixed[i]), "fixed-" + i);
    int exhaustive = 0;
    for (int len = 0; len <= 12; len++) {
      int count = 1 << len;
      for (int mask = 0; mask < count; mask++) {
        String s = fromMask(len, mask);
        check(s, oracle(s), "exhaustive-" + exhaustive);
        exhaustive++;
      }
    }
    if (exhaustive != 8191) throw new AssertionError("unexpected exhaustive count=" + exhaustive);
    for (int i = 0; i < 20000; i++) {
      String s = randomString(50);
      check(s, oracle(s), "random-" + i);
    }
    boolean nullThrew = false, invalidThrew = false;
    try { LongestValidParentheses.longestValidParentheses(null); } catch (IllegalArgumentException expected) { nullThrew = true; }
    try { LongestValidParentheses.longestValidParentheses("()a()"); } catch (IllegalArgumentException expected) { invalidThrew = true; }
    if (!nullThrew || !invalidThrew) throw new AssertionError("declared input contract not enforced");
    System.out.println("PASS reviewer fixed=14 exhaustive=8191 random=20000 oracle=quadratic-balance-scan null=throws invalid=throws");
  }
}
''', encoding='utf-8')
    proc = subprocess.run(['bash','-lc','javac LongestValidParentheses.java LongestValidParenthesesReviewerTest.java && java LongestValidParenthesesReviewerTest'], cwd=out, text=True, capture_output=True, check=False)
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
    if not item or item.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: missing or non-coding source inventory row')
    if sorted(item.get('question_ids') or []) != sorted(QIDS):
        raise SystemExit(f'{CID}: frozen ownership drift')
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
    occurrence_ids = {(x.get('question_id'), x.get('source_note_id'), x.get('source_question_index'), x.get('original_question')) for x in source_rows}
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
    required = ['最长连续有效括号子串','下标栈','哨兵 `-1`','i - stack.peek()','dp[i]','i - previous - 1','O(n)','非法右括号','子序列','public final class LongestValidParentheses']
    missing = [token for token in required if token not in candidate]
    if missing:
        raise SystemExit(f'{CID}: stack/DP/invariant/boundary coverage missing: {missing}')
    one_minute = candidate.split('## 1 分钟版', 1)[1].split('## 3 分钟版', 1)[0]
    points = sum(1 for line in one_minute.splitlines() if line.startswith('- '))
    if not (3 <= points <= 5):
        raise SystemExit(f'{CID}: one-minute point count must be 3..5, got {points}')

    stdout = run_reviewer_validation(out)
    reviewer_validation_path = out / 'reviewer_validation.json'
    write_json(reviewer_validation_path, {
        'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,
        'validator':'independent_source_first_reviewer',
        'command':'javac LongestValidParentheses.java LongestValidParenthesesReviewerTest.java && java LongestValidParenthesesReviewerTest',
        'stdout':stdout,
        'checks':['14 fixed empty/single/pair/nested/reset/concatenated boundary strings','all 8,191 parenthesis strings of length at most twelve match an independent quadratic balance-scan oracle','20,000 independently seeded random parenthesis strings up to length fifty match the independent oracle','null input rejects according to the declared candidate contract','non-parenthesis characters reject according to the declared candidate contract']
    })

    reviewer_id = 'source-first-isolated-reviewer-batch-0062-longest-valid-parentheses-20260831-v1'
    review_version = 'batch-0062.longest-valid-parentheses.v1'
    findings = [
        'Both frozen source variants ask for Longest Valid Parentheses, and one explicitly names dynamic programming/stack; both are directly covered.',
        'The candidate declares a Java contract for the longest continuous valid-parentheses substring and keeps null/invalid-character behavior as an explicit answer assumption rather than a source fact.',
        'The stack invariant is explained around the -1/reset boundary and the post-pop stack top, which justifies computing the current valid suffix length as i - stack.peek().',
        'The DP alternative defines dp[i] as the longest valid suffix ending at i and covers both the immediate-pair and wrapped-previous-suffix transitions, including the dp[j-1] connection.',
        'The executable stack implementation is independently revalidated with a quadratic balance-scan oracle rather than the writer DP oracle, including all 8,191 strings up to length twelve and 20,000 random strings.',
        'The answer distinguishes substring from subsequence, covers reset/nesting/concatenation boundaries, states O(n) time and O(n) worst-case stack space, and identifies an O(1)-space two-scan variant without changing the main contract.'
    ]
    review_result_path = out / 'isolated_review_result.json'
    write_json(review_result_path, {
        'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,
        'review_mode':'source_first_isolated','reviewer_id':reviewer_id,'review_version':review_version,'decision':'pass','revision_round':1,
        'source_packet':[str(context_path),str(inventory_path),str(candidate_path),str(out/'LongestValidParentheses.java'),str(out/'LongestValidParenthesesReviewerTest.java'),str(reviewer_validation_path),'config/answer_quality.json','docs/refactor/09_answer_content_standard.md'],
        'forbidden_inputs_not_used':[str(out/'writer_research.json'),str(out/'writer_validation.json'),'writer self score','writer expected decision'],
        'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':[PROMOTION_BLOCKER]
    })

    sources = [
        {'source_id':'repository-source','title':'Batch 0062 frozen repository context for longest valid parentheses','locator':str(context_path),'source_type':'repository_source_record','checked_at':DATE},
        {'source_id':'source-inventory','title':'Batch 0062 occurrence-aware frozen source inventory','locator':str(inventory_path),'source_type':'repository_structured_source','checked_at':DATE},
        {'source_id':'reviewer-validation','title':'Independent longest-valid-parentheses balance-scan differential validation','locator':str(reviewer_validation_path),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
        {'source_id':'isolated-review','title':'Batch 0062 longest-valid-parentheses source-first isolated review','locator':str(review_result_path),'source_type':'repository_structured_source','checked_at':DATE}
    ]
    claims = [
        {'claim_id':'source-boundary','text':'The two frozen source occurrences ask for Longest Valid Parentheses, with one explicitly naming dynamic programming/stack, and do not prescribe Java, null handling or invalid-character semantics.','source_ids':['repository-source','source-inventory'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节']},
        {'claim_id':'stack-contract','text':'Under the declared Java continuous-substring contract, the stack implementation matches an independent quadratic balance-scan oracle on fixed cases, every parenthesis string through length twelve and 20,000 random strings.','source_ids':['reviewer-validation'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制']},
        {'claim_id':'boundaries','text':'The independently validated behavior covers empty, nested, concatenated and reset-after-unmatched-right-parenthesis cases while the answer explicitly distinguishes substring from subsequence and states input-error boundaries.','source_ids':['reviewer-validation','isolated-review'],'answer_locations':['关键细节','原理机制','常见追问','易错点']}
    ]
    locations = ['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']
    coverage = [{'question_id':qid,'covered':True,'answer_locations':locations} for qid in QIDS]
    boundary_tests = [
        {'case':'empty, single-character, pair, nested and concatenated inputs','expected':'exact match with independent balance-scan oracle','passed':True},
        {'case':'unmatched right parenthesis followed by a later valid region','expected':'reset boundary prevents illegal prefix from inflating length','passed':True},
        {'case':'all 8,191 parenthesis strings of length at most twelve','expected':'exact match with independent quadratic balance-scan oracle','passed':True},
        {'case':'20,000 seeded random parenthesis strings up to length fifty','expected':'exact match with independent quadratic balance-scan oracle','passed':True},
        {'case':'null and non-parenthesis input','expected':'IllegalArgumentException according to the explicit candidate contract','passed':True}
    ]
    write_json(ROOT/f'review/evidence/{CID}.json', {
        'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,
        'writer':{'writer_id':'content-batch-0062-longest-valid-parentheses-writer','writer_version':'xhs-answer-curator.v1'},
        'sources':sources,'claims':claims,'source_question_coverage':coverage,'source_occurrence_count':2,
        'validation':{'validator':'independent_source_first_reviewer','result':'pass','artifact':str(reviewer_validation_path),'boundary_tests':boundary_tests},
        'review_state':'independent_source_first_review_passed',
        'review':{'reviewer_id':reviewer_id,'review_version':review_version,'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},
        'promotion_blocker':PROMOTION_BLOCKER
    })

    task_path = ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    line = f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; both frozen Longest Valid Parentheses source variants are covered; the declared continuous-substring Java stack contract was independently revalidated against a quadratic balance-scan oracle over all 8,191 parenthesis strings through length twelve plus 20,000 seeded random strings. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in task:
        task_path.write_text(task + '\n' + line + '\n', encoding='utf-8')
    print(EXPECTED_STDOUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
