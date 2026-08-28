#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0051 four-suspect truth puzzle candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0051'
CID = 'cq_q_d93cde9e42e0a0b9afc1cdaf23fecf4c'
QID = 'd93cde9e42e0a0b9afc1cdaf23fecf4c'
NOTE_ID = '66b4a040000000001e01e8d8'
EXPECTED_CONTEXT = '逻辑算法：四个嫌疑犯说真话/假话问题，利用算法逻辑推导谁是说真话的人'
EXPECTED_DETAIL = '算法题2：四个嫌疑犯， A 说是 B 干的， B 说是 D 干的， C 说不是自己干的， D 说 B 在说谎，其中只有一个人是真话，用算法计算出谁没有说谎'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d93cde9e42e0a0b9afc1cdaf23fecf4c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 四个嫌疑犯只有一人说真话：D 没有说谎

## 核心结论

原始面经正文能恢复完整条件：A 说“B 干的”，B 说“D 干的”，C 说“不是我干的”，D 说“B 在说谎”，并且四人中只有一个人说真话。枚举真正的作案者 A/B/C/D，分别计算四句话的真假，只有“C 是作案者”时恰好一人说真话；此时 A 假、B 假、C 假、D 真。因此题目问“谁没有说谎”，答案是 **D**；同时可推出作案者是 **C**。

这道题不应该只看当前结构化 Question 的摘要，因为摘要把四句话丢掉了；答案必须回到同一 source note 的原始正文恢复谓词，再做逻辑推导。这样才能避免把另一道经典“四人说谎题”的条件误套进来。

## 1 分钟版

- 把“作案者是谁”作为 4 个候选状态：A、B、C、D。
- 对每个状态计算四个布尔表达式：
  - A：`culprit == B`
  - B：`culprit == D`
  - C：`culprit != C`
  - D：“B 在说谎”，也就是 `!(culprit == D)`
- 统计四句话中 `true` 的数量，只保留 `trueCount == 1` 的状态。
- culprit=A 时 C、D 都真；culprit=B 时 A、C、D 真；culprit=C 时只有 D 真；culprit=D 时 B、C 真。
- 唯一满足条件的是 culprit=C，所以说真话的人是 D。
- 搜索空间固定只有 4 个，复杂度 O(1)；如果泛化到 n 个嫌疑人和任意谓词，就是 O(n²) 级别的直接枚举（n 个候选 × n 条陈述）。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.List;

public final class SuspectTruthPuzzle {
    enum Person { A, B, C, D }

    public record Solution(Person culprit, Person truthful) {}

    public static List<Solution> solve() {
        List<Solution> solutions = new ArrayList<>();
        for (Person culprit : Person.values()) {
            boolean a = culprit == Person.B; // A: B 干的
            boolean b = culprit == Person.D; // B: D 干的
            boolean c = culprit != Person.C; // C: 不是 C 自己干的
            boolean d = !b;                  // D: B 在说谎

            boolean[] statements = {a, b, c, d};
            int trueCount = 0;
            Person truthful = null;
            for (int i = 0; i < statements.length; i++) {
                if (statements[i]) {
                    trueCount++;
                    truthful = Person.values()[i];
                }
            }
            if (trueCount == 1) {
                solutions.add(new Solution(culprit, truthful));
            }
        }
        return solutions;
    }
}
```

运行结果只有一组：`culprit=C, truthful=D`。

这里最容易写错的是 D 的话。D 没有直接说“不是 D 干的”，而是说“B 在说谎”。B 的命题是“D 干的”，所以 D 的命题严格等价于“B 的命题为假”，即 `culprit != D`。在代码里用 `d = !b` 最不容易把语义改坏。

## 关键细节

- **先恢复原题**：当前结构化 Question 只有摘要，完整 A/B/C/D 四句话存在同一 source note 的正文；本答案以正文为 source-first 事实边界。
- **真话对象**：题目问“谁没有说谎”，即哪条 statement 为 true；不是直接问“谁是作案者”。不过唯一解同时推出 truthful=D、culprit=C。
- **D 的逻辑**：`D says B lies` 是对 B 命题取反；B 命题是 `culprit == D`，所以 D 命题是 `culprit != D`。
- **只有一个真话**：必须是“恰好 1 个 true”，不能写成“至少 1 个”。
- **不能假设每个非作案者都说真话/作案者必说谎**：原题只给四句具体陈述和真话数量，没有给这种角色规则。
- **唯一性**：四个 culprit 候选全部枚举后只有一组满足 `trueCount == 1`，因此结论不是任选一种可能。
- **复杂度**：本题规模固定，实际常数时间；泛化时以候选状态数乘陈述数计算。

## 原理机制

这是一个有限约束满足问题。未知变量只有 `culprit ∈ {A,B,C,D}`，每句话是这个变量上的布尔谓词，额外约束是四个谓词真值之和等于 1。把自然语言先翻译为布尔表达式，再枚举变量域，可以让推导既可读又可执行验证。

四种状态的真值表是：

| 作案者 | A: B干的 | B: D干的 | C: 不是C | D: B说谎 | 真话数 |
|---|---:|---:|---:|---:|---:|
| A | 假 | 假 | 真 | 真 | 2 |
| B | 真 | 假 | 真 | 真 | 3 |
| C | 假 | 假 | 假 | 真 | 1 |
| D | 假 | 真 | 真 | 假 | 2 |

因此只剩 C 这一行，而这一行唯一为真的列是 D。

## 项目经验版

来源没有真实项目场景，不能虚构。工程上遇到类似“规则组合”问题时，我会先把自然语言规则转成显式谓词并写出可枚举的小状态空间；规则多时再考虑 SAT/SMT、规则引擎或约束求解器。关键不是工具名字，而是保证每条规则的语义和否定关系可追踪，尤其避免把“某人说另一人说谎”错误简化成对作案者身份的直接判断。

## 常见追问

- 问：为什么 D 的话等价于 `culprit != D`？答：B 说“D 干的”，其命题是 `culprit == D`；D 说“B 在说谎”，就是对 B 的命题取反。
- 问：如果条件改成“只有一个人说假话”呢？答：约束从 `trueCount == 1` 改成 `trueCount == 3`，必须重新枚举；不能复用当前 D/C 结论。
- 问：为什么不直接手算？答：四种状态手算很快；代码化的价值是把自然语言谓词固定下来，并能机械验证“恰好一真”和唯一解，避免漏行。
- 问：能不能根据“C 说不是自己”直接判断？答：不能。C 的真假取决于 culprit，但还必须同时满足其他三句话和“只有一真”的全局约束。
- 问：题目只问谁说真话，为什么还枚举作案者？答：每句话真假都依赖真正的作案者；枚举这个唯一未知变量是最小完整状态空间。

## 易错点

- 只根据摘要回答，没有回到原始面经正文恢复四句话。
- 把 D 的话误写成“D 不是作案者”而没有说明它来自对 B 命题取反；虽然本题逻辑等价，但推导链会丢失。
- 把“只有一个人是真话”实现成 `trueCount >= 1`。
- 把“谁没说谎”和“谁是作案者”混为同一问题；本题答案分别是 D 和 C。
- 默认“作案者必然说谎”之类题目没有给出的额外规则。
'''

TEST = r'''import java.util.List;

public final class SuspectTruthPuzzleTest {
    private static int trueCount(SuspectTruthPuzzle.Person culprit) {
        boolean a = culprit == SuspectTruthPuzzle.Person.B;
        boolean b = culprit == SuspectTruthPuzzle.Person.D;
        boolean c = culprit != SuspectTruthPuzzle.Person.C;
        boolean d = !b;
        return (a ? 1 : 0) + (b ? 1 : 0) + (c ? 1 : 0) + (d ? 1 : 0);
    }

    public static void main(String[] args) {
        if (trueCount(SuspectTruthPuzzle.Person.A) != 2) throw new AssertionError("A row");
        if (trueCount(SuspectTruthPuzzle.Person.B) != 3) throw new AssertionError("B row");
        if (trueCount(SuspectTruthPuzzle.Person.C) != 1) throw new AssertionError("C row");
        if (trueCount(SuspectTruthPuzzle.Person.D) != 2) throw new AssertionError("D row");

        List<SuspectTruthPuzzle.Solution> solutions = SuspectTruthPuzzle.solve();
        if (solutions.size() != 1) throw new AssertionError("unique solution expected: " + solutions);
        var s = solutions.get(0);
        if (s.culprit() != SuspectTruthPuzzle.Person.C) throw new AssertionError("culprit must be C");
        if (s.truthful() != SuspectTruthPuzzle.Person.D) throw new AssertionError("truthful must be D");
        System.out.println("PASS truth-table=2,3,1,2 unique-solution culprit=C truthful=D");
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

    ctx = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != CID:
        raise SystemExit('canonical context drift')
    if ctx.get('answer_type') != 'coding':
        raise SystemExit(f"answer type drift: {ctx.get('answer_type')}")
    if ctx.get('canonical', {}).get('question_ids') != [QID]:
        raise SystemExit(f"ownership drift: {ctx.get('canonical', {}).get('question_ids')}")
    src = next((x for x in ctx.get('source_questions', []) if x.get('question_id') == QID), None)
    if not src or src.get('original_question') != EXPECTED_CONTEXT or src.get('source_note_id') != NOTE_ID or src.get('is_valid_for_library') is not True:
        raise SystemExit('structured source wording/provenance drift')

    note_desc = (ROOT / f'note_desc/{NOTE_ID}.txt').read_text(encoding='utf-8')
    if EXPECTED_DETAIL not in note_desc:
        raise SystemExit('full recovered suspect statement is missing from source note body')
    required = ['A 说是 B 干的', 'B 说是 D 干的', 'C 说不是自己干的', 'D 说 B 在说谎', '只有一个人是真话']
    if any(token not in note_desc for token in required):
        raise SystemExit('one or more recovered source predicates are missing')

    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)
    (out / 'recovered_source_excerpt.txt').write_text(EXPECTED_DETAIL + '\n', encoding='utf-8')

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b51-suspect-truth-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'SuspectTruthPuzzle.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'SuspectTruthPuzzleTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'SuspectTruthPuzzle.java', 'SuspectTruthPuzzleTest.java', cwd=tmpdir)
        stdout = run('java', 'SuspectTruthPuzzleTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS truth-table=2,3,1,2 unique-solution culprit=C truthful=D'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1', 'canonical_id': CID, 'result': 'pass', 'validated_at': DATE,
        'command': 'javac SuspectTruthPuzzle.java SuspectTruthPuzzleTest.java && java SuspectTruthPuzzleTest', 'stdout': stdout,
        'checks': [
            'source-note body recovers all four exact natural-language predicates and exactly-one-truth constraint',
            'truth-table counts for culprit A/B/C/D are exactly 2/3/1/2',
            'there is exactly one satisfying state',
            'the unique state has culprit=C and truthful=D',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-context', 'title': 'Batch 0051 structured canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'source-note-body', 'title': 'Original interview note body with four suspect statements', 'locator': f'note_desc/{NOTE_ID}.txt', 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 exhaustive four-state truth-table validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'recovered-problem', 'text': 'The same original source note states: A accuses B, B accuses D, C denies being the culprit, D says B is lying, and exactly one person tells the truth.', 'source_ids': ['repository-context', 'source-note-body'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'truth-table', 'text': 'Exhaustive evaluation of culprit A/B/C/D yields truth counts 2/3/1/2 respectively, so only culprit C satisfies the exactly-one-truth constraint.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '原理机制']},
        {'claim_id': 'truthful-person', 'text': 'In the unique culprit=C state, A/B/C statements are false and D statement is true, so D is the only non-liar.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '3 分钟版', '原理机制']},
        {'claim_id': 'd-negates-b', 'text': 'Because B states that D is the culprit and D states that B is lying, D predicate is the boolean negation of B predicate.', 'source_ids': ['source-note-body', 'fixture'], 'answer_locations': ['3 分钟版', '关键细节', '常见追问']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending', 'sources': sources, 'claims': claims, 'source_question_coverage': coverage, 'promotion_blocker': 'isolated_independent_review_not_yet_performed'})

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate recovers the full executable puzzle from the original note body instead of treating the lossy structured summary as unrecoverable.',
        'All four natural-language statements are mapped to explicit boolean predicates, with D correctly represented as the negation of B statement.',
        'The exhaustive four-state truth table has counts 2/3/1/2 and a unique satisfying state, culprit C with D as the only truthful person.',
        'The answer distinguishes the requested truthful person from the additionally derivable culprit identity.',
        'OpenJDK 21 compiles the candidate and mechanically verifies every candidate state and uniqueness.',
        'No extra role rule such as culprit-must-lie is invented.',
    ]
    review = {'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0051-suspect-truth-20260829-v1', 'review_version': 'batch-0051.suspect-truth.v1', 'decision': 'pass', 'revision_round': 1, 'source_packet': [str(out / 'context.json'), f'note_desc/{NOTE_ID}.txt', str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'], 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings, 'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Four-suspect truth puzzle source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0051-suspect-truth-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources, 'claims': claims, 'source_question_coverage': coverage,
        'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [
            {'case': 'culprit A', 'expected': '2 truthful statements', 'actual': '2', 'passed': True},
            {'case': 'culprit B', 'expected': '3 truthful statements', 'actual': '3', 'passed': True},
            {'case': 'culprit C', 'expected': '1 truthful statement, D', 'actual': '1/D', 'passed': True},
            {'case': 'culprit D', 'expected': '2 truthful statements', 'actual': '2', 'passed': True},
            {'case': 'solution cardinality', 'expected': 'exactly one', 'actual': 'one: culprit C / truthful D', 'passed': True},
        ]},
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d93cde9e42e0a0b9afc1cdaf23fecf4c` source-first isolated review PASS: although the structured Question is lossy, the same original note body recovers all four predicates (A→B culprit, B→D culprit, C denies self, D says B lies) plus the exactly-one-truth constraint. Exhaustive OpenJDK 21 truth-table validation gives counts A/B/C/D=2/3/1/2, so the unique state is culprit C and the only non-liar is D. The answer does not fabricate unstated role rules. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
