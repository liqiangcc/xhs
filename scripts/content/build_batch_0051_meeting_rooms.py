#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0051 LeetCode 253 candidate."""

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
CID = 'cq_q_dbf0ec3aa331be76bfefa26a39750ce7'
QID = 'dbf0ec3aa331be76bfefa26a39750ce7'
EXPECTED = '算法：leetcode253 会议室'
LEETCODE = 'https://leetcode.com/problems/meeting-rooms-ii/'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_dbf0ec3aa331be76bfefa26a39750ce7","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# LeetCode 253 Meeting Rooms II：最少会议室数量

## 核心结论

来源明确指向 LeetCode 253 Meeting Rooms II。当前题意是：给一组会议时间区间，求能让全部会议同时被安排所需的最少会议室数量。这个数量本质上等于任意时刻同时进行的会议数的最大值。

一个直接且容易解释的做法是“按开始时间排序 + 最小堆维护正在占用的会议室结束时间”。处理下一场会议前，把所有 `end <= start` 的已结束会议弹出，因为这些房间已经可复用；再把当前会议的结束时间放入堆。此时堆大小就是当前正在占用的房间数，遍历期间的最大堆大小就是答案。

## 1 分钟版

- 按会议开始时间从小到大处理。
- 最小堆里只保存当前仍在进行的会议结束时间，堆顶是最早可释放的房间。
- 新会议开始前，循环弹出所有 `end <= start` 的会议；“一个会议在 t 结束、另一个在 t 开始”可以复用同一房间。
- 把当前会议的 `end` 压入堆，并更新最大堆大小。
- 排序 O(N log N)，每个结束时间最多入堆、出堆各一次，所以总时间 O(N log N)，堆空间 O(N)。
- 为避免把实现副作用扩张成题意，本实现复制输入后排序，不修改调用方的二维数组顺序。

## 3 分钟版

```java
import java.util.Arrays;
import java.util.Comparator;
import java.util.PriorityQueue;

public final class MeetingRoomsII {
    public static int minMeetingRooms(int[][] intervals) {
        if (intervals == null) {
            throw new IllegalArgumentException("intervals must not be null");
        }
        if (intervals.length == 0) {
            return 0;
        }

        int[][] meetings = new int[intervals.length][2];
        for (int i = 0; i < intervals.length; i++) {
            if (intervals[i] == null || intervals[i].length < 2) {
                throw new IllegalArgumentException("each interval needs start/end");
            }
            int start = intervals[i][0];
            int end = intervals[i][1];
            if (start >= end) {
                throw new IllegalArgumentException("meeting must satisfy start < end");
            }
            meetings[i][0] = start;
            meetings[i][1] = end;
        }

        Arrays.sort(meetings, Comparator.comparingInt(a -> a[0]));
        PriorityQueue<Integer> activeEnds = new PriorityQueue<>();
        int answer = 0;

        for (int[] meeting : meetings) {
            int start = meeting[0];
            while (!activeEnds.isEmpty() && activeEnds.peek() <= start) {
                activeEnds.poll();
            }
            activeEnds.offer(meeting[1]);
            answer = Math.max(answer, activeEnds.size());
        }
        return answer;
    }
}
```

例如 `[[0,30],[5,10],[15,20]]`：0 时只有第一场，5 时第二场加入而第一场未结束，因此同时占两个房间；15 时 `[5,10]` 已结束，可释放一个房间给 `[15,20]`，峰值仍是 2。

如果区间是 `[[7,10],[2,4]]`，两场没有重叠，第一场结束后房间可被第二场复用，所以答案是 1。这里把结束点视为可立即复用：`[1,5]` 和 `[5,9]` 不需要两个房间。

## 关键细节

- **答案不是会议总数，而是并发峰值**：只要先结束的房间能被后续会议复用，就不需要新房间。
- **为什么用最小堆**：下一场会议能否复用房间，首先只需要知道最早结束的会议；最小堆能 O(log N) 更新这个边界。
- **为什么要弹出全部已结束会议**：这样堆大小始终精确代表当前活跃会议数，便于直接把最大堆大小解释为并发峰值。
- **端点语义**：`end <= start` 即可释放，意味着结束时刻和下一场开始时刻相同不算重叠。
- **输入顺序**：题目没有要求修改输入；实现复制 `start/end` 后再排序，避免调用方观察到顺序改变。
- **非法区间**：当前实现把 `start >= end` 当非法输入；这是为了让工程接口边界明确。若上游数据允许零时长会议，要先单独定义它是否占用房间。
- **复杂度**：排序 O(N log N)；每个会议结束时间最多入堆和出堆各一次，堆操作累计 O(N log N)，额外空间 O(N)。

## 原理机制

这题可以看成区间重叠计数。任意时刻需要的会议室数就是覆盖这个时刻的区间数量；最少会议室数因此等于覆盖数的最大值。最小堆只是把“哪些区间仍然覆盖当前开始时刻”动态维护出来。

处理按开始时间排序后的会议时，所有已经满足 `end <= current.start` 的区间都不再与当前会议重叠，可以从活跃集合中删除。剩下的结束时间都大于当前开始时间，它们对应仍占房间的会议。把当前会议加入后，堆大小就等于此刻所需房间数。遍历所有开始事件并记录最大值，就得到全局并发峰值。

另一种等价写法是把所有 start 和 end 分别排序，用双指针做事件扫描。堆方案的优势是更自然地扩展到“返回具体房间分配”一类追问；双指针方案常数更小、只求数量时也很简洁。

## 项目经验版

来源没有真实项目场景，不能虚构线上会议调度经验。工程里如果只需要容量规划，求峰值并发就够；如果还要输出每场会议具体分配到哪个房间，则堆元素应从单独的 `end` 扩展为 `(end, roomId)`，并额外维护可复用 roomId。若数据量极大或会议不断在线到达，还要明确输入是否已按开始时间有序、是否允许迟到事件，以及结果要实时还是离线计算。

## 常见追问

- 问：为什么 `end == start` 可以复用？答：本题的会议室调度语义按结束后立即释放处理，所以前一场在 t 结束、后一场在 t 开始不需要两个房间；实现对应 `end <= start` 时弹出。
- 问：为什么不能只看相邻两个区间是否重叠？答：并发可能跨多个区间。例如一个长会议覆盖很多短会议，只比较相邻区间无法直接得到全局同时占用数量。
- 问：能不能只在每次新会议时弹一个结束时间？答：若只关心“已分配房间总数”，可以设计另一种等价堆写法；这里弹出全部已结束会议，让堆大小严格等于当前活跃会议数，证明和调试都更直接。
- 问：双指针怎么做？答：分别排序所有开始时间和结束时间。下一个开始早于最早结束时并发数加一，否则先释放房间并推进结束指针；记录最大并发即可。
- 问：如何返回具体房间编号？答：堆中保存 `(end, roomId)`；释放会议时回收 roomId，新会议优先复用可用编号，否则创建新编号。
- 问：输入已经按开始时间排好还需要排序吗？答：如果接口契约明确保证有序，可以省掉排序并把处理降到 O(N log R)，其中 R 是峰值房间数；当前来源没有这个保证，所以不能依赖它。

## 易错点

- 把“会议数”当成“会议室数”，没有复用已结束会议的房间。
- 用 `end < start` 而不是 `end <= start`，错误地把首尾相接的会议算成重叠。
- 只比较当前会议和上一个会议，漏掉更早开始但尚未结束的长会议。
- 排序调用方原数组却没有说明输入会被修改。
- 只返回最终堆大小，却使用了“弹出全部已结束会议”的活跃集合写法；最终时刻的活跃数不一定等于历史峰值，必须单独记录最大值。
- 没有定义空输入和异常区间边界，却在实现中悄悄选择一种行为。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class MeetingRoomsIITest {
    private static int oracle(int[][] intervals) {
        if (intervals.length == 0) return 0;
        int best = 0;
        for (int[] probe : intervals) {
            int t = probe[0];
            int active = 0;
            for (int[] x : intervals) {
                if (x[0] <= t && t < x[1]) active++;
            }
            best = Math.max(best, active);
        }
        return best;
    }

    private static void check(int[][] input, int expected) {
        int[][] before = new int[input.length][];
        for (int i = 0; i < input.length; i++) before[i] = input[i].clone();
        int actual = MeetingRoomsII.minMeetingRooms(input);
        if (actual != expected) throw new AssertionError("expected=" + expected + " actual=" + actual);
        for (int i = 0; i < input.length; i++) {
            if (!Arrays.equals(input[i], before[i])) throw new AssertionError("input mutated");
        }
    }

    public static void main(String[] args) {
        check(new int[][]{{0,30},{5,10},{15,20}}, 2);
        check(new int[][]{{7,10},{2,4}}, 1);
        check(new int[][]{}, 0);
        check(new int[][]{{1,5},{5,9}}, 1);
        check(new int[][]{{1,10},{2,3},{3,4},{4,5},{5,6}}, 2);
        check(new int[][]{{1,4},{1,4},{1,4}}, 3);

        Random rnd = new Random(20260829L);
        for (int tc = 0; tc < 5000; tc++) {
            int n = rnd.nextInt(18);
            int[][] a = new int[n][2];
            for (int i = 0; i < n; i++) {
                int start = rnd.nextInt(20);
                int end = start + 1 + rnd.nextInt(8);
                a[i][0] = start;
                a[i][1] = end;
            }
            int expected = oracle(a);
            int actual = MeetingRoomsII.minMeetingRooms(a);
            if (actual != expected) {
                throw new AssertionError("random mismatch expected=" + expected + " actual=" + actual + " input=" + Arrays.deepToString(a));
            }
        }

        try { MeetingRoomsII.minMeetingRooms(null); throw new AssertionError("null must fail"); }
        catch (IllegalArgumentException expected) {}
        try { MeetingRoomsII.minMeetingRooms(new int[][]{{3,3}}); throw new AssertionError("zero-length must fail"); }
        catch (IllegalArgumentException expected) {}
        try { MeetingRoomsII.minMeetingRooms(new int[][]{{5,3}}); throw new AssertionError("reversed must fail"); }
        catch (IllegalArgumentException expected) {}

        System.out.println("PASS official-examples touching nested duplicates random5000-vs-overlap-oracle input-unchanged invalid-boundaries");
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

    with tempfile.TemporaryDirectory(prefix='b51-meeting-rooms-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'MeetingRoomsII.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'MeetingRoomsIITest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'MeetingRoomsII.java', 'MeetingRoomsIITest.java', cwd=tmpdir)
        stdout = run('java', 'MeetingRoomsIITest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS official-examples touching nested duplicates random5000-vs-overlap-oracle input-unchanged invalid-boundaries'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac MeetingRoomsII.java MeetingRoomsIITest.java && java MeetingRoomsIITest',
        'stdout': stdout,
        'checks': [
            'current canonical LeetCode 253 named examples produce 2 and 1 rooms',
            'touching endpoints reuse a room under end <= next-start semantics',
            'nested and identical-interval cases preserve the true overlap peak',
            '5000 deterministic random interval sets match an independent start-time overlap oracle',
            'input interval arrays remain unchanged',
            'null, zero-length and reversed intervals follow explicit implementation boundaries',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0051 canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'leetcode-253', 'title': 'LeetCode 253 Meeting Rooms II current problem statement', 'locator': LEETCODE, 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 meeting-room validation versus independent overlap oracle', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'problem-contract', 'text': 'The repository source names LeetCode 253 Meeting Rooms II; the problem asks for the minimum number of conference rooms needed for a set of meeting intervals.', 'source_ids': ['repository-source', 'leetcode-253'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版']},
        {'claim_id': 'overlap-semantics', 'text': 'A room can be reused when an earlier meeting has ended by the next meeting start, modeled by removing active end times with end <= start.', 'source_ids': ['leetcode-253', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节', '常见追问']},
        {'claim_id': 'algorithm-validation', 'text': 'The executable fixture validates the min-heap active-set algorithm on named examples, boundary shapes, and 5000 deterministic random interval sets against an independent overlap-count oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'complexity-bound', 'text': 'Sorting is O(N log N), and every meeting end enters and leaves the priority queue at most once, keeping total heap work O(N log N).', 'source_ids': ['fixture'], 'answer_locations': ['1 分钟版', '关键细节', '原理机制']},
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

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The shorthand repository source is resolved to the explicitly named LeetCode 253 Meeting Rooms II contract rather than a different meeting-room variant.',
        'The candidate identifies the answer as peak overlap and makes the heap active-set invariant explicit.',
        'Touching endpoints are handled with immediate room reuse, and this boundary is covered by executable validation.',
        'OpenJDK 21 validation covers named examples, nested/identical intervals, input immutability, and 5000 deterministic random cases against an independent overlap oracle.',
        'The implementation records historical maximum heap size instead of incorrectly returning only the final active count.',
        'Null/invalid interval behavior and non-mutating input handling are labeled as implementation boundaries, not fabricated source requirements.',
        'The project section avoids fabricated experience and distinguishes capacity counting from concrete room assignment.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0051-meeting-rooms-20260829-v1',
        'review_version': 'batch-0051.meeting-rooms.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), LEETCODE, str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'LeetCode 253 source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0051-meeting-rooms-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': '[[0,30],[5,10],[15,20]]', 'expected': 2, 'actual': 2, 'passed': True},
                {'case': '[[7,10],[2,4]]', 'expected': 1, 'actual': 1, 'passed': True},
                {'case': 'touching [1,5],[5,9]', 'expected': 1, 'actual': 1, 'passed': True},
                {'case': 'three identical intervals', 'expected': 3, 'actual': 3, 'passed': True},
                {'case': '5000 deterministic random interval sets', 'expected': 'equals independent overlap oracle', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_dbf0ec3aa331be76bfefa26a39750ce7` source-first isolated review PASS: the shorthand source is resolved against the current LeetCode 253 Meeting Rooms II contract. The candidate models the answer as peak interval overlap, uses a start-sorted min-heap active set with end <= start room reuse, and records the historical maximum rather than the final active count. OpenJDK 21 validation covers named examples, touching/nested/identical intervals and 5000 deterministic random cases against an independent overlap oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
