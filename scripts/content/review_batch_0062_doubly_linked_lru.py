#!/usr/bin/env python3
"""Source-first isolated review for Batch 0062 doubly-linked-list LRU candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-31'
BATCH = '0062'
CID = 'cq_q_ad98fcd2a28e860ad42d11065af2caea'
QIDS = ['ad98fcd2a28e860ad42d11065af2caea']
EXPECTED_VARIANT = '手撕代码：实现一个双向链表版 LRU 缓存？'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
EXPECTED_STDOUT = 'PASS reviewer random_ops=45000 oracle=list-map-model capacity1=pass read_refresh=pass update_refresh=pass miss=null'


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def run_reviewer_validation(out: Path) -> str:
    harness = out / 'DoublyLinkedLRUReviewerTest.java'
    harness.write_text(r'''import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

public final class DoublyLinkedLRUReviewerTest {
    private static final Random RNG = new Random(0x62AD98FCL ^ 0x7E11A9L);

    private static final class Oracle {
        private final int capacity;
        private final Map<Integer, Integer> values = new HashMap<>();
        private final List<Integer> recency = new ArrayList<>(); // MRU -> LRU
        Oracle(int capacity) { this.capacity = capacity; }
        Integer get(int key) {
            if (!values.containsKey(key)) return null;
            Integer value = values.get(key);
            recency.remove(Integer.valueOf(key));
            recency.add(0, key);
            return value;
        }
        void put(int key, int value) {
            if (values.containsKey(key)) {
                values.put(key, value);
                recency.remove(Integer.valueOf(key));
                recency.add(0, key);
                return;
            }
            if (values.size() == capacity) {
                int victim = recency.remove(recency.size() - 1);
                values.remove(victim);
            }
            values.put(key, value);
            recency.add(0, key);
        }
        int size() { return values.size(); }
    }

    private static void eq(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        boolean zero = false, negative = false;
        try { new LRUCache(0); } catch (IllegalArgumentException expected) { zero = true; }
        try { new LRUCache(-3); } catch (IllegalArgumentException expected) { negative = true; }
        if (!zero || !negative) throw new AssertionError("non-positive capacity contract not enforced");

        LRUCache c = new LRUCache(2);
        eq(null, c.get(99), "initial-miss");
        c.put(1, 10); c.put(2, 20); eq(2, c.size(), "size-two");
        eq(10, c.get(1), "read-refreshes-one");
        c.put(3, 30); eq(null, c.get(2), "two-is-lru-after-read");
        eq(10, c.get(1), "one-survives"); eq(30, c.get(3), "three-present");
        c.put(1, 11); eq(11, c.get(1), "update-value");
        c.put(4, 40); eq(null, c.get(3), "update-refreshes-one");
        eq(11, c.get(1), "updated-one-survives"); eq(40, c.get(4), "four-present");
        eq(2, c.size(), "size-stays-capacity");

        LRUCache one = new LRUCache(1);
        one.put(7, 70); eq(70, one.get(7), "capacity1-hit");
        one.put(8, 80); eq(null, one.get(7), "capacity1-evict"); eq(80, one.get(8), "capacity1-new");

        int operations = 0;
        for (int scenario = 0; scenario < 90; scenario++) {
            int capacity = 1 + RNG.nextInt(9);
            LRUCache actual = new LRUCache(capacity);
            Oracle oracle = new Oracle(capacity);
            for (int step = 0; step < 500; step++) {
                int key = RNG.nextInt(23);
                if (RNG.nextInt(100) < 56) {
                    int value = RNG.nextInt();
                    actual.put(key, value);
                    oracle.put(key, value);
                } else {
                    eq(oracle.get(key), actual.get(key), "random-get-" + scenario + '-' + step);
                }
                if (actual.size() != oracle.size()) throw new AssertionError("size drift scenario=" + scenario + " step=" + step);
                operations++;
            }
            for (int key = 0; key < 23; key++) {
                eq(oracle.get(key), actual.get(key), "final-key-" + scenario + '-' + key);
            }
        }
        if (operations != 45000) throw new AssertionError("unexpected operation count " + operations);
        System.out.println("PASS reviewer random_ops=45000 oracle=list-map-model capacity1=pass read_refresh=pass update_refresh=pass miss=null");
    }
}
''', encoding='utf-8')
    proc = subprocess.run(['bash','-lc','javac LRUCache.java DoublyLinkedLRUReviewerTest.java && java DoublyLinkedLRUReviewerTest'], cwd=out, text=True, capture_output=True, check=False)
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
    if item.get('question_ids') != QIDS:
        raise SystemExit(f'{CID}: frozen ownership drift')
    source_rows = list(item.get('source_questions') or [])
    if item.get('source_question_count') != 1 or item.get('source_occurrence_count') != 2 or len(source_rows) != 2:
        raise SystemExit(f'{CID}: occurrence-aware inventory drift')
    if any(x.get('question_id') != QIDS[0] or x.get('original_question') != EXPECTED_VARIANT for x in source_rows):
        raise SystemExit(f'{CID}: source wording/identity drift')
    occurrence_ids = {(x.get('source_note_id'), x.get('source_question_index')) for x in source_rows}
    if len(occurrence_ids) != 2:
        raise SystemExit(f'{CID}: duplicate primary-source occurrences collapsed')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    context_path = out / 'context.json'
    context = json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type') != 'coding':
        raise SystemExit(f'{CID}: frozen context/type drift')
    canonical = context.get('canonical') or {}
    if canonical.get('canonical_id') != CID or canonical.get('question_ids') != QIDS:
        raise SystemExit(f'{CID}: context ownership drift')
    context_rows = list(context.get('source_questions') or [])
    if len(context_rows) != 2 or any(x.get('question_id') != QIDS[0] or x.get('original_question') != EXPECTED_VARIANT for x in context_rows):
        raise SystemExit(f'{CID}: context source occurrence drift')
    context_occurrences = {(x.get('source_note_id'), x.get('source_question_index')) for x in context_rows}
    if len(context_occurrences) != 2:
        raise SystemExit(f'{CID}: context occurrence identity collapsed')

    candidate_path = ROOT / f'review/candidates/answers/{CID}.md'
    candidate = candidate_path.read_text(encoding='utf-8')
    digest = hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    for heading in HEADINGS:
        if candidate.count(heading) != 1:
            raise SystemExit(f'{CID}: candidate section drift: {heading}')
    if candidate.count('- 问：') < 5:
        raise SystemExit(f'{CID}: question-specific follow-up coverage too small')
    required = ['HashMap', '双向链表', 'MRU', 'LRU', 'linkAfterHead', 'unlink', 'tail.prev', 'capacity <= 0', 'null', '期望 `O(1)`', 'public final class LRUCache']
    missing = [token for token in required if token not in candidate]
    if missing:
        raise SystemExit(f'{CID}: doubly-linked LRU invariant/boundary coverage missing: {missing}')
    one_minute = candidate.split('## 1 分钟版', 1)[1].split('## 3 分钟版', 1)[0]
    points = sum(1 for line in one_minute.splitlines() if line.startswith('- '))
    if not (4 <= points <= 6):
        raise SystemExit(f'{CID}: one-minute point count must be 4..6, got {points}')

    stdout = run_reviewer_validation(out)
    reviewer_validation_path = out / 'reviewer_validation.json'
    write_json(reviewer_validation_path, {
        'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,
        'validator':'independent_source_first_reviewer',
        'command':'javac LRUCache.java DoublyLinkedLRUReviewerTest.java && java DoublyLinkedLRUReviewerTest',
        'stdout':stdout,
        'checks':['fixed miss/read-refresh/update-refresh/eviction/size boundaries distinguish LRU from FIFO','capacity one plus zero/negative capacity behavior matches the declared contract','45,000 independently seeded random get/put operations match an independent HashMap plus explicit recency-list model']
    })

    reviewer_id = 'source-first-isolated-reviewer-batch-0062-doubly-linked-lru-20260831-v1'
    review_version = 'batch-0062.doubly-linked-lru.v1'
    findings = [
        'Both frozen primary-source occurrences carry the same question asking specifically for a doubly-linked-list LRU implementation; the duplicate occurrence is preserved rather than collapsed, while the source does not prescribe language, API, miss value, invalid-capacity behavior or concurrency semantics.',
        'The candidate directly addresses the requested data structure by pairing a HashMap index with a sentinel-based doubly linked list ordered MRU to LRU, instead of answering only with a generic cache abstraction.',
        'The positive-capacity, single-threaded Java API and null-on-miss behavior are explicitly labeled as answer-level contract choices rather than source facts.',
        'Read hits and updates both refresh recency, overflow removes tail.prev, and eviction removes the same key from the map, preserving the one-map-entry/one-list-node invariant.',
        'The executable implementation is independently revalidated against a simple HashMap plus explicit recency-list oracle rather than the writer LinkedHashMap oracle, including capacity-one boundaries and 45,000 random operations.',
        'Complexity wording correctly distinguishes strict O(1) pointer relinking from expected O(1) HashMap operations, avoiding an unsupported worst-case claim.'
    ]
    review_result_path = out / 'isolated_review_result.json'
    write_json(review_result_path, {
        'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,
        'review_mode':'source_first_isolated','reviewer_id':reviewer_id,'review_version':review_version,'decision':'pass','revision_round':1,
        'source_packet':[str(context_path),str(inventory_path),str(candidate_path),str(out/'LRUCache.java'),str(out/'DoublyLinkedLRUReviewerTest.java'),str(reviewer_validation_path),'config/answer_quality.json','docs/refactor/09_answer_content_standard.md'],
        'forbidden_inputs_not_used':[str(out/'writer_research.json'),str(out/'writer_validation.json'),'writer self score','writer expected decision','historical review/remediation records'],
        'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':[PROMOTION_BLOCKER]
    })

    sources = [
        {'source_id':'repository-source','title':'Batch 0062 frozen repository context for doubly-linked-list LRU','locator':str(context_path),'source_type':'repository_source_record','checked_at':DATE},
        {'source_id':'source-inventory','title':'Batch 0062 occurrence-aware frozen source inventory','locator':str(inventory_path),'source_type':'repository_structured_source','checked_at':DATE},
        {'source_id':'reviewer-validation','title':'Independent doubly-linked LRU list-map differential validation','locator':str(reviewer_validation_path),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
        {'source_id':'isolated-review','title':'Batch 0062 doubly-linked LRU source-first isolated review','locator':str(review_result_path),'source_type':'repository_structured_source','checked_at':DATE},
    ]
    claims = [
        {'claim_id':'source-boundary','text':'The two preserved primary-source occurrences ask for a doubly-linked-list LRU implementation and do not prescribe Java, miss semantics, invalid capacity handling or concurrency behavior.','source_ids':['repository-source','source-inventory'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节']},
        {'claim_id':'lru-contract','text':'Under the declared positive-capacity single-threaded Java contract, the HashMap plus sentinel doubly-linked-list implementation matches an independent list-map LRU model on fixed boundaries and 45,000 random operations.','source_ids':['reviewer-validation'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制']},
        {'claim_id':'boundaries','text':'Independent validation covers miss behavior, read refresh, update refresh, capacity-one eviction and non-positive-capacity rejection while the answer keeps concurrency and richer cache policies outside the source contract.','source_ids':['reviewer-validation','isolated-review'],'answer_locations':['关键细节','项目经验版','常见追问','易错点']},
    ]
    locations = ['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']
    coverage = [{'question_id':QIDS[0],'covered':True,'answer_locations':locations}]
    boundary_tests = [
        {'case':'two preserved source occurrences','expected':'both remain visible and map to the same canonical without pretending they are distinct question meanings','passed':True},
        {'case':'get miss before insertion','expected':'null according to explicit candidate contract','passed':True},
        {'case':'get refresh followed by overflow','expected':'recently read key survives while older key is evicted','passed':True},
        {'case':'put update followed by overflow','expected':'updated key refreshes to MRU and does not increase size','passed':True},
        {'case':'capacity one','expected':'each distinct new key evicts the previous key','passed':True},
        {'case':'zero or negative capacity','expected':'IllegalArgumentException according to explicit candidate contract','passed':True},
        {'case':'45,000 seeded random operations','expected':'exact agreement with independent list-map LRU model','passed':True},
    ]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,
        'writer':{'writer_id':'content-batch-0062-doubly-linked-lru-writer','writer_version':'xhs-answer-curator.v1'},
        'sources':sources,'claims':claims,'source_question_coverage':coverage,'source_occurrence_count':2,
        'validation':{'validator':'independent_source_first_reviewer','result':'pass','artifact':str(reviewer_validation_path),'boundary_tests':boundary_tests},
        'review_state':'independent_source_first_review_passed',
        'review':{'reviewer_id':reviewer_id,'review_version':review_version,'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},
        'promotion_blocker':PROMOTION_BLOCKER,
    })

    task_path = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task = task_path.read_text(encoding='utf-8').rstrip()
    line = f'- [x] `{CID}` source-first isolated review PASS: candidate digest `{digest}`; both frozen duplicate primary-source occurrences of the doubly-linked-list LRU question remain visible and are covered; the declared positive-capacity single-threaded Java contract was independently revalidated against a list-map LRU model over fixed recency/eviction boundaries plus 45,000 seeded random operations. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in task:
        task_path.write_text(task + '\n' + line + '\n', encoding='utf-8')
    print(EXPECTED_STDOUT)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
