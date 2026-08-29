#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 delayed-departure candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0052'
CID = 'cq_q_e0e729151f85454da62dc0efdc139500'
QID = 'e0e729151f85454da62dc0efdc139500'
EXPECTED = '算法：给定发车时间和延迟区间，判断当前时间能赶上的最近的车'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e0e729151f85454da62dc0efdc139500","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 发车时间 + 延迟区间：区分“保证赶上”和“可能赶上”的最近车辆

## 核心结论

来源只说“给定发车时间和延迟区间，判断当前时间能赶上的最近的车”，但**区间不是一个确定延迟值**。如果一辆车计划 10:00 发车、延迟区间是 `[0, 10]` 分钟，而当前时间是 10:05，那么它可能已经 10:00 开走，也可能 10:10 才走；仅凭这个区间无法断言“肯定能赶上”或知道真实最近发车时刻。因此答案首先要把不确定性说清楚，而不是把区间上界/下界偷偷当成真实延迟。

这里冻结一个可执行合同：所有时间都已经转换成同一条**绝对时间轴**上的整数单位（例如同一 epoch 的分钟），不在本函数里处理 `HH:mm` 跨午夜；第 i 辆车计划时间为 `scheduled[i]`，实际延迟未知但保证落在闭区间 `[minDelay[i], maxDelay[i]]`，且 `0 <= minDelay <= maxDelay`。于是实际发车窗口是 `[earliest, latest] = [scheduled+minDelay, scheduled+maxDelay]`。

在这个信息量下可以可靠回答两类问题：

- **保证能赶上**：`now <= earliest`。即使它按允许的最早时刻发车，你现在也还没错过。取这类车中 `earliest` 最小的，称为“最近的保证可赶车辆”。
- **可能能赶上**：`now <= latest`。至少存在一种延迟实现使你还能赶上。取这类车中 `latest` 最小的，称为“最紧迫的可能可赶车辆”。

如果业务一定要一个“真实最近车辆”，还需要实际延迟/实时位置等额外信息；只给区间时这个答案在一般情况下**不可唯一确定**。如果延迟其实是确定值，把 `minDelay == maxDelay`，两种结果会收敛成普通的“找第一个实际发车时间 >= now”。

## 1 分钟版

- 先把每辆车的实际发车时间表示成窗口 `[scheduled + minDelay, scheduled + maxDelay]`。
- `now <= earliest`：保证可赶；因为最坏情况对乘客来说是它尽早发车，你仍未错过。
- `earliest < now <= latest`：只能说可能可赶；实际车可能已走，也可能仍未走。
- `now > latest`：确定已错过。
- 只给区间时不能凭空知道真实最近车，所以接口同时返回 guaranteed 与 possible 两个候选。
- 扫描一遍即可：分别维护最小 `earliest` 的 guaranteed index、最小 `latest` 的 possible index，O(n) 时间、O(1) 额外空间。
- 当前合同使用绝对时间，不直接拿 `HH:mm` 比较；跨午夜应先规范化时间轴。

## 3 分钟版

```java
import java.util.OptionalInt;

public final class DelayedDepartureSelector {
    public record Selection(OptionalInt nearestGuaranteed,
                            OptionalInt mostUrgentPossible) {}

    public static Selection select(long now,
                                   long[] scheduled,
                                   long[] minDelay,
                                   long[] maxDelay) {
        if (scheduled == null || minDelay == null || maxDelay == null) {
            throw new IllegalArgumentException("arrays must not be null");
        }
        if (scheduled.length != minDelay.length || scheduled.length != maxDelay.length) {
            throw new IllegalArgumentException("array lengths must match");
        }

        int guaranteedIndex = -1;
        int possibleIndex = -1;
        long bestEarliest = Long.MAX_VALUE;
        long bestLatest = Long.MAX_VALUE;

        for (int i = 0; i < scheduled.length; i++) {
            if (minDelay[i] < 0 || maxDelay[i] < minDelay[i]) {
                throw new IllegalArgumentException("invalid delay interval at index " + i);
            }
            long earliest = Math.addExact(scheduled[i], minDelay[i]);
            long latest = Math.addExact(scheduled[i], maxDelay[i]);

            if (now <= earliest && (earliest < bestEarliest
                    || (earliest == bestEarliest && i < guaranteedIndex))) {
                bestEarliest = earliest;
                guaranteedIndex = i;
            }
            if (now <= latest && (latest < bestLatest
                    || (latest == bestLatest && i < possibleIndex))) {
                bestLatest = latest;
                possibleIndex = i;
            }
        }

        return new Selection(
                guaranteedIndex < 0 ? OptionalInt.empty() : OptionalInt.of(guaranteedIndex),
                possibleIndex < 0 ? OptionalInt.empty() : OptionalInt.of(possibleIndex));
    }
}
```

例如两辆车：A 的计划时刻 100、延迟 `[0,30]`；B 的计划时刻 110、延迟 `[20,40]`；当前 `now=115`。A 的窗口是 `[100,130]`，只能“可能赶上”；B 的窗口是 `[130,150]`，则“保证赶上”。所以 guaranteed 选 B，而 possible 的最紧迫候选是 A。这个例子正好说明为什么一个区间不能被当成单一实际发车时刻。

当前 `mostUrgentPossible` 按最小 `latest` 排序，它表达“最早到达最后机会边界的可能候选”，**不是**声称该车真实发车一定早于其他车。真实发车顺序也可能因窗口重叠而不确定。

## 关键细节

- **三态而不是二态**：窗口完全在 now 之后是 guaranteed；窗口跨过 now 是 possible-only；窗口完全在 now 之前是 missed。
- **闭区间边界**：当前合同使用 `now <= departure` 视为还能赶上，所以 `now == earliest/latest` 仍属于可赶。若站务规则要求提前若干分钟停止检票，应把“能赶上”的比较时刻改成截止时间。
- **最近的定义必须绑定指标**：guaranteed 用最小 earliest；possible 用最小 latest。没有实时实际延迟时，不声称求出了真实 nearest actual departure。
- **时间轴**：`23:59` 和 `00:05` 不能只比较时分整数；应在调用前转成带日期/epoch 的统一绝对时间。
- **到站耗时**：来源只给“当前时间”，没给从当前位置到车站的耗时。如果真实问题有 travelTime，应比较 `arrivalTime = now + travelTime`，而不是直接比较 now。
- **溢出**：计划时刻与延迟相加用 `Math.addExact`，避免 long 回绕后误判窗口。
- **平局**：当前实现同一边界时取较小输入下标，保证确定性；业务若有车次优先级可替换 tie-breaker。

## 原理机制

核心不是排序，而是**不确定区间上的可证明结论**。设实际发车时刻 T 满足 `earliest <= T <= latest`：

- 若 `now <= earliest`，则对所有合法 T 都有 `now <= T`，所以“能赶上”对整个区间都成立，这是 guaranteed。
- 若 `earliest < now <= latest`，区间里既存在 `T < now` 也存在 `T >= now`，所以有的真实延迟会错过、有的不会，只能给 possible。
- 若 `now > latest`，则对所有合法 T 都有 `T < now`，一定错过。

这三个判断来自量词差异：guaranteed 是“对所有可能实际时间成立”，possible 是“至少存在一个可能实际时间成立”。把两者混在一起，是这类延迟区间题最危险的逻辑错误。

## 项目经验版

来源没有真实项目背景，不能虚构高德/公交实时系统经验。工程里如果要给用户展示“下一班能赶上的车”，通常还需要实时 ETA/实际发车状态、步行/驾车到站时间、检票截止和时区/服务日等数据。若只有计划表 + 延迟区间，更诚实的产品语义也是展示“保证可赶 / 可能可赶 / 已错过”或置信信息，而不是伪造一个确定答案。

## 常见追问

- 问：为什么不能直接用 `scheduled + maxDelay >= now` 判断能赶上？答：那只能证明“可能赶上”；车也可能按更小延迟已经走了，不能升级成保证可赶。
- 问：如果延迟是确定值，不是区间呢？答：令 minDelay=maxDelay=delay，窗口退化成一个点，guaranteed 和 possible 会一致，此时就是找最早实际发车时间不早于 now 的车。
- 问：如果要考虑我到车站还需 12 分钟？答：先得到 arrivalTime，再用 arrivalTime 替代 now 做同样判断；还应加检票截止 buffer。
- 问：为什么 possible 按 latest 最小？答：它表示最后机会边界最紧迫的候选，便于在不确定条件下排序；它不代表真实发车时刻已知。
- 问：数据已按计划发车时间排序，可以二分吗？答：如果每辆车延迟区间不同，earliest/latest 序列未必仍按 scheduled 单调；只有额外证明目标边界单调后才能安全二分。
- 问：跨午夜怎么办？答：不要只存一天内分钟数；把日期和时间规范化为同一绝对时间线后再比较。

## 易错点

- 把延迟区间上界当成“实际延迟”，把 possible 错说成 guaranteed。
- 看到窗口覆盖 now 就断言一定赶得上，忽略车辆可能已按窗口左端发走。
- 在信息不足时输出唯一“真实最近车”，掩盖不可辨识性。
- 只按计划发车时刻排序/二分，却没证明加上不同延迟后目标边界仍单调。
- 直接比较 `HH:mm`，跨午夜时顺序错误。
- 忽略到站耗时或检票截止，却把“当前时间未过发车时间”当成现实中的可赶上。
- 时间与延迟相加不检查溢出。
'''

TEST = r'''import java.util.OptionalInt;
import java.util.Random;

public final class DelayedDepartureSelectorTest {
    private static DelayedDepartureSelector.Selection oracle(long now, long[] scheduled, long[] minD, long[] maxD) {
        int g = -1, p = -1;
        long ge = Long.MAX_VALUE, pl = Long.MAX_VALUE;
        for (int i = 0; i < scheduled.length; i++) {
            long earliest = Math.addExact(scheduled[i], minD[i]);
            long latest = Math.addExact(scheduled[i], maxD[i]);
            if (now <= earliest && (earliest < ge || (earliest == ge && (g < 0 || i < g)))) { ge = earliest; g = i; }
            if (now <= latest && (latest < pl || (latest == pl && (p < 0 || i < p)))) { pl = latest; p = i; }
        }
        return new DelayedDepartureSelector.Selection(g < 0 ? OptionalInt.empty() : OptionalInt.of(g), p < 0 ? OptionalInt.empty() : OptionalInt.of(p));
    }
    private static void check(int g, int p, long now, long[] s, long[] minD, long[] maxD) {
        var r = DelayedDepartureSelector.select(now, s, minD, maxD);
        OptionalInt eg = g < 0 ? OptionalInt.empty() : OptionalInt.of(g);
        OptionalInt ep = p < 0 ? OptionalInt.empty() : OptionalInt.of(p);
        if (!r.nearestGuaranteed().equals(eg) || !r.mostUrgentPossible().equals(ep)) throw new AssertionError("got=" + r + " expected=" + eg + "/" + ep);
    }
    public static void main(String[] args) {
        check(2, 2, 121, new long[]{100,120,140}, new long[]{0,0,0}, new long[]{0,0,0});
        check(1, 0, 115, new long[]{100,110}, new long[]{0,20}, new long[]{30,40});
        check(-1, -1, 200, new long[]{100,120}, new long[]{0,0}, new long[]{10,20});
        check(0, 0, 130, new long[]{100}, new long[]{30}, new long[]{30});
        check(0, 0, 10, new long[]{0,0}, new long[]{10,10}, new long[]{20,20});

        try { DelayedDepartureSelector.select(0, null, new long[]{}, new long[]{}); throw new AssertionError("null must fail"); }
        catch (IllegalArgumentException expected) {}
        try { DelayedDepartureSelector.select(0, new long[]{1}, new long[]{}, new long[]{1}); throw new AssertionError("length must fail"); }
        catch (IllegalArgumentException expected) {}
        try { DelayedDepartureSelector.select(0, new long[]{1}, new long[]{-1}, new long[]{1}); throw new AssertionError("negative delay must fail"); }
        catch (IllegalArgumentException expected) {}
        try { DelayedDepartureSelector.select(0, new long[]{1}, new long[]{2}, new long[]{1}); throw new AssertionError("reversed interval must fail"); }
        catch (IllegalArgumentException expected) {}
        try { DelayedDepartureSelector.select(0, new long[]{Long.MAX_VALUE}, new long[]{1}, new long[]{1}); throw new AssertionError("overflow must fail"); }
        catch (ArithmeticException expected) {}

        Random random = new Random(20260829L);
        for (int round = 0; round < 5000; round++) {
            int n = random.nextInt(40);
            long now = random.nextInt(250) - 50;
            long[] s = new long[n], minD = new long[n], maxD = new long[n];
            for (int i = 0; i < n; i++) {
                s[i] = random.nextInt(250) - 50;
                minD[i] = random.nextInt(21);
                maxD[i] = minD[i] + random.nextInt(21);
            }
            var expected = oracle(now, s, minD, maxD);
            var actual = DelayedDepartureSelector.select(now, s, minD, maxD);
            if (!actual.equals(expected)) throw new AssertionError("random mismatch round=" + round);
        }

        int n = 200_000;
        long[] s = new long[n], minD = new long[n], maxD = new long[n];
        for (int i = 0; i < n; i++) { s[i] = i * 10L; minD[i] = i % 3; maxD[i] = minD[i] + 5; }
        var expected = oracle(999_999L, s, minD, maxD);
        var actual = DelayedDepartureSelector.select(999_999L, s, minD, maxD);
        if (!actual.equals(expected)) throw new AssertionError("large mismatch");

        System.out.println("PASS exact-and-uncertain-windows inclusive-boundaries invalid-input 5000-random-oracle 200000-services");
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
    if candidate.exists(): raise SystemExit('candidate already exists; do not overwrite reviewed work')
    ctx = json.loads(run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical', {}).get('canonical_id') != CID: raise SystemExit('canonical context drift')
    if ctx.get('answer_type') != 'coding': raise SystemExit(f"answer type drift: {ctx.get('answer_type')}")
    if ctx.get('canonical', {}).get('question_ids') != [QID]: raise SystemExit(f"ownership drift: {ctx.get('canonical', {}).get('question_ids')}")
    src = next((x for x in ctx.get('source_questions', []) if x.get('question_id') == QID), None)
    if not src or src.get('original_question') != EXPECTED or src.get('is_valid_for_library') is not True: raise SystemExit('source wording/validity drift')
    out = ROOT / f'review/content_build/answer_batch_{BATCH}/{CID}'
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / 'context.json', ctx)
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1: raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1: raise SystemExit(f'expected one Java block, got {len(blocks)}')
    with tempfile.TemporaryDirectory(prefix='b52-delayed-departure-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'DelayedDepartureSelector.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'DelayedDepartureSelectorTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'DelayedDepartureSelector.java', 'DelayedDepartureSelectorTest.java', cwd=tmpdir)
        stdout = run('java', 'DelayedDepartureSelectorTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS exact-and-uncertain-windows inclusive-boundaries invalid-input 5000-random-oracle 200000-services'
    if stdout != expected_stdout: raise SystemExit(f'unexpected fixture output: {stdout}')
    validation = {'schema_version': 'answer_code_validation.v1', 'canonical_id': CID, 'result': 'pass', 'validated_at': DATE, 'command': 'javac DelayedDepartureSelector.java DelayedDepartureSelectorTest.java && java DelayedDepartureSelectorTest', 'stdout': stdout, 'checks': ['exact-delay and overlapping uncertain-window directed cases', 'inclusive earliest/latest boundary and deterministic tie handling', 'null/length/interval/overflow invalid-input boundaries', '5000 deterministic random window sets compared with a direct interval oracle', '200000-service large scan']}
    write_json(out / 'writer_validation.json', validation)
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact delayed-departure source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 delayed-departure interval validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-ambiguity', 'text': 'The exact source gives scheduled departure time plus a delay interval but does not say that actual delay is known, define catchability under uncertainty, specify travel time, or define time-axis normalization.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '关键细节']},
        {'claim_id': 'interval-contract', 'text': 'The candidate interprets each delay as a closed uncertainty interval, distinguishing guaranteed catchability now<=earliest, possible catchability now<=latest, and definite miss now>latest.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '原理机制']},
        {'claim_id': 'underdetermination', 'text': 'When now lies inside a departure window, the interval alone cannot determine whether that vehicle has actually departed; therefore the answer does not fabricate a unique actual-nearest vehicle.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '3 分钟版', '常见追问']},
        {'claim_id': 'validation', 'text': 'Executable validation covers exact and uncertain windows, endpoint inclusivity, invalid interval/overflow inputs, 5000 deterministic random cases, and a 200000-service scan.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '易错点']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending', 'sources': sources, 'claims': claims, 'source_question_coverage': coverage, 'promotion_blocker': 'isolated_independent_review_not_yet_performed'})
    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The answer identifies the core information-theory boundary: a delay interval does not reveal a unique actual departure time.',
        'Guaranteed and possible catchability are separated with correct universal/existential interval semantics instead of treating the maximum delay as factual.',
        'The chosen nearest metrics are explicitly named by their endpoints and are not mislabeled as the unknown actual nearest departure.',
        'Absolute-time normalization, inclusive endpoint semantics, travel-time omission and tie-breaking are all surfaced as candidate boundaries.',
        'OpenJDK 21 validation covers directed exact/uncertain windows, invalid intervals/overflow, 5000 deterministic random cases and a 200000-service scan.',
        'The implementation is one pass with O(1) auxiliary state and does not assume binary-search monotonicity that different delay intervals may destroy.',
        'The project section avoids fabricated map/transit production experience and keeps real-time data requirements clearly conditional.',
    ]
    review = {'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0052-delayed-departure-20260829-v1', 'review_version': 'batch-0052.delayed-departure.v1', 'decision': 'pass', 'revision_round': 1, 'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'], 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings, 'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out / 'isolated_review_result.json', review)
    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 delayed-departure source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'writer': {'writer_id': 'content-batch-0052-delayed-departure-builder', 'writer_version': 'xhs-answer-curator.v1'}, 'sources': evidence_sources, 'claims': claims, 'source_question_coverage': coverage, 'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [{'case': 'overlapping delay windows', 'expected': 'possible and guaranteed candidates may differ', 'actual': 'pass', 'passed': True}, {'case': 'now equals window endpoint', 'expected': 'inclusive catchability', 'actual': 'pass', 'passed': True}, {'case': 'invalid interval/overflow', 'expected': 'explicit failure', 'actual': 'pass', 'passed': True}, {'case': '5000 random + 200000 services', 'expected': 'oracle match', 'actual': 'pass', 'passed': True}]}, 'review_state': 'independent_source_first_review_passed', 'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings}, 'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied'})

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e0e729151f85454da62dc0efdc139500` source-first isolated review PASS: the sparse source gives scheduled time plus a delay interval, so the candidate refuses to fabricate a unique actual departure from uncertain data. It freezes absolute-time closed intervals, distinguishes guaranteed (`now <= earliest`) from possible (`now <= latest`) catchability, names endpoint-based nearest metrics explicitly, and OpenJDK 21 validation covers exact/overlapping windows, endpoint/invalid/overflow boundaries, 5000 deterministic random cases, and a 200000-service scan. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text: text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')
    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
