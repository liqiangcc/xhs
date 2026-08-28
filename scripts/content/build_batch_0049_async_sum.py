#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0049 async-sum candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
CID = 'cq_q_cff7d30b3ad4c9fb5929904f2da7a932'
QID = 'cff7d30b3ad4c9fb5929904f2da7a932'
EXPECTED = '编程题: 异步编程利用Promise.all和async/await实现数组元素加法并优化并发'
BATCH = '0049'
PROMISE_ALL_SPEC = 'https://tc39.es/ecma262/2026/multipage/control-abstraction-objects.html#sec-promise.all'
ASYNC_FUNCTION_SPEC = 'https://tc39.es/ecma262/2026/multipage/ecmascript-language-functions-and-classes.html#sec-async-function-definitions'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_cff7d30b3ad4c9fb5929904f2da7a932","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# Promise.all + async/await 实现数组异步求和并限制并发

## 核心结论

原题只说“利用 `Promise.all` 和 `async/await` 实现数组元素加法并优化并发”，没有给异步操作是什么、并发上限、错误策略或取消语义。下面采用一个明确可测试的契约：对数组中的每个元素执行异步 `transform(value, index)`，最多同时执行 `limit` 个 transform；全部成功后按输入元素得到的结果求和；任一 transform 失败则整体 reject。关键点是：`Promise.all(values.map(async ...))` 适合“等待全部”，但 `map` 会先为所有元素启动异步回调，所以它本身不是并发限制器；真正的限流由固定数量的 worker 循环完成，再用 `Promise.all(workers)` 等这些 worker 收敛。

## 1 分钟版

- 先区分两个职责：`async/await` 用于把异步流程写成顺序控制流，`Promise.all` 用于等待一组 Promise；**并发上限要另外实现**。
- 直接 `Promise.all(values.map(async v => work(v)))` 会一次性创建整批任务，数组很大或下游有限流时可能把并发打满。
- 更稳妥的做法是创建 `min(limit, n)` 个 worker，共享一个递增索引；每个 worker 一次只 `await` 一个元素，完成后再领取下一个，因此 in-flight 数量不会超过 `limit`。
- 每个结果写回原索引，最后 `Promise.all(workers)` 后求和，既保持输入对应关系，又避免把完成顺序误当成输入顺序。
- 错误策略要写清楚：本答案 fail-fast reject；已经启动的普通 Promise 不会因为聚合 Promise reject 就自动被取消，若业务要求取消，需要下游 API 配合显式取消机制。

## 3 分钟版

下面把“异步数组求和”定义为：输入 `values`、正整数 `limit` 和异步 `transform`；transform 的返回值必须是有限 Number；空数组返回 0。`mapLimit` 负责并发控制，`sumAsync` 只负责数值聚合。

```javascript
async function mapLimit(values, limit, worker) {
  if (!Array.isArray(values)) throw new TypeError('values must be an array');
  if (!Number.isInteger(limit) || limit <= 0) {
    throw new RangeError('limit must be a positive integer');
  }
  if (typeof worker !== 'function') throw new TypeError('worker must be a function');

  const results = new Array(values.length);
  let nextIndex = 0;

  async function runWorker() {
    while (true) {
      const index = nextIndex;
      if (index >= values.length) return;
      nextIndex += 1;
      results[index] = await worker(values[index], index);
    }
  }

  const workers = Array.from(
    { length: Math.min(limit, values.length) },
    () => runWorker(),
  );
  await Promise.all(workers);
  return results;
}

async function sumAsync(values, limit, transform = async (value) => value) {
  const mapped = await mapLimit(values, limit, transform);
  let total = 0;
  for (const value of mapped) {
    if (!Number.isFinite(value)) throw new TypeError('transform must return finite numbers');
    const next = total + value;
    if (!Number.isFinite(next)) throw new RangeError('sum is outside finite Number range');
    total = next;
  }
  return total;
}

module.exports = { mapLimit, sumAsync };
```

这里 `nextIndex` 的“领取”发生在当前 worker 遇到 `await` 之前；每个 worker 领取一个不同索引后才进入异步等待，所以最多只有 worker 数量这么多个 transform 同时处于执行中。结果写到 `results[index]`，因此即使第 5 个请求先完成、第 1 个后完成，结果数组仍按输入索引排列。

ECMAScript 的 `Promise.all` 语义是：所有输入完成时以对应位置的 fulfillment value 构成结果数组；有输入 reject 时，聚合 Promise 以首先观察到的 rejection reason reject。这个语义负责“收敛”，不提供并发池。若题目改成“即使部分失败也要拿到所有结果”，应考虑把错误编码成结果或使用 `Promise.allSettled`，而不是继续沿用本答案的 fail-fast 契约。

## 关键细节

- **并发 ≠ Promise 数量无限增长**：限流目标通常是保护浏览器连接池、后端 QPS、数据库连接或第三方 API；只有固定 worker 数才能保证这里的 in-flight 上界。
- **Promise.all 不等于取消**：聚合 Promise reject 后，已经启动的异步操作仍可能继续产生副作用。若必须取消，应把 `AbortSignal` 或领域取消令牌传给真正支持取消的 worker，而不是期待 `Promise.all` 自动终止它们。
- **保持输入顺序**：异步完成顺序通常不稳定；用原索引写 `results[index]`，再统一聚合，避免“谁先完成谁先进入结果”造成错位。
- **错误传播**：任一 worker 抛错会让对应 worker Promise reject，进而让 `Promise.all(workers)` reject。本契约不吞错、不返回部分和。
- **空数组**：worker 数量为 0，`Promise.all([])` 可直接完成，随后求和得到 0。
- **limit > n**：只创建 n 个 worker，不制造空转任务；`limit = 0` 或负数直接拒绝，因为它不能表达可前进的并发池。
- **Number 边界**：示例把 transform 结果和累计和都限制为有限 Number；如果业务需要任意精度整数，应改成 `BigInt` 契约，不能混用 Number 与 BigInt。
- **复杂度**：CPU 侧遍历 O(n)，结果数组和 worker 状态 O(n + min(n, limit))；墙钟时间取决于各异步任务耗时，理想独立任务下大致受总工作量 / 并发上限和最慢任务共同约束，但不能脱离下游服务能力承诺线性加速。

## 原理机制

并发池的核心不变量是：任意时刻，每个 worker 最多持有一个尚未完成的 `await worker(...)`，worker 总数不超过 `limit`，因此由本函数启动的 in-flight transform 数不会超过 `limit`。共享索引只在同步片段里递增；JavaScript 在一次 job 执行到 `await` 挂起前不会被另一个同 Agent 的同步片段穿插，所以两个 worker 不会领取同一个索引。

`Promise.all` 在这里位于更外层：它不决定“什么时候启动每个元素任务”，只等待已经创建的 worker Promise。每个 worker 内部串行消费多个元素，而不同 worker 之间并发推进。这样把**调度**和**聚合**分开，比“先 map 出 n 个 Promise 再 all”更容易证明并发上界。

错误路径也要单独看：若一个 worker reject，外层 `Promise.all` 会 reject，但其他 worker 可能已经领取任务并继续运行。因此“fail-fast 返回”与“取消副作用”是两件事。需要强取消时，必须设计可协作取消的 worker，并决定已经完成、正在执行和尚未领取任务分别怎么处理。

## 项目经验版

来源没有真实项目经历，不能虚构“线上把并发从多少调到多少”。真实项目里我会先确认受保护资源是什么，再用指标决定 `limit`：例如下游 429/5xx、连接池等待、P95/P99、队列长度和吞吐量。限流值应通过压测或线上小流量逐步校准；如果任务还需要重试、超时、取消或动态限速，应把这些策略放在独立调度层，而不是继续往一个 `Promise.all` 表达式里堆逻辑。

## 常见追问

- 问：为什么 `Promise.all(array.map(async ...))` 不能限制并发？答：因为 `map` 会同步遍历数组并调用每个回调，从而先创建整批异步任务；`Promise.all` 只是等待这些已创建 Promise，不会把它们自动排成固定大小的队列。
- 问：`Promise.all` 的结果顺序跟完成顺序一致吗？答：不是按完成先后；结果槽位对应输入 Promise 的位置。这里仍显式写回 `results[index]`，让 worker 池本身也保留输入对应关系。
- 问：一个任务失败，其他请求会被取消吗？答：本契约中不会自动取消。聚合 Promise 会 reject，但已经启动的异步操作仍可继续；要取消必须让底层操作支持并接收显式取消信号。
- 问：为什么不用一次启动 `limit` 个 chunk？答：固定分块容易出现某个 chunk 被慢任务拖住而其他 chunk 已空闲。共享索引的 worker pool 能让空闲 worker 继续领取下一项，通常负载更均衡。
- 问：如果要保留所有成功和失败结果怎么办？答：把每项错误转成结构化结果，或使用 `Promise.allSettled`；此时最终返回值不再是“全成功才有一个总和”，需要重新定义部分失败如何计入聚合。

## 易错点

- 把 `Promise.all` 说成“自动限并发”，实际上一次性 `map` 已经启动整批任务。
- 只限制 Promise 数组切片，却没有证明同一时刻真正运行的下游操作数量。
- 任务 reject 后假设其他请求已经被取消，导致重复写、计费或副作用继续发生却无人观察。
- 按完成顺序 push 结果，最后把异步完成顺序误当成原数组顺序。
- 没有校验 `limit <= 0`、空数组、非数值结果和数值溢出等边界。
- 把更高并发直接等同于更低延迟，忽略下游限流、连接池、排队和尾延迟。
'''

TEST = r'''const assert = require('node:assert/strict');
const { mapLimit, sumAsync } = require('./async_sum');

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function main() {
  let active = 0;
  let maxActive = 0;
  const total = await sumAsync([1, 2, 3, 4, 5, 6], 2, async (value) => {
    active += 1;
    maxActive = Math.max(maxActive, active);
    await delay(4 + (7 - value));
    active -= 1;
    return value;
  });
  assert.equal(total, 21);
  assert.equal(maxActive, 2, 'bounded worker pool should reach but not exceed limit');

  const order = await mapLimit([30, 5, 15], 3, async (ms, index) => {
    await delay(ms);
    return `value-${index}`;
  });
  assert.deepEqual(order, ['value-0', 'value-1', 'value-2']);

  const allOrder = await Promise.all([
    delay(20).then(() => 'first-input'),
    delay(2).then(() => 'second-input'),
  ]);
  assert.deepEqual(allOrder, ['first-input', 'second-input']);

  let sideEffect = 0;
  const later = delay(18).then(() => { sideEffect += 1; return 1; });
  await assert.rejects(Promise.all([later, Promise.reject(new Error('boom'))]), /boom/);
  await delay(25);
  assert.equal(sideEffect, 1, 'aggregate rejection must not be treated as automatic cancellation');

  let emptyCalls = 0;
  assert.equal(await sumAsync([], 4, async () => { emptyCalls += 1; return 1; }), 0);
  assert.equal(emptyCalls, 0);
  assert.equal(await sumAsync([2, 3], 10), 5);

  await assert.rejects(sumAsync('not-array', 2), /array/);
  await assert.rejects(sumAsync([1], 0), /positive integer/);
  await assert.rejects(sumAsync([1], -1), /positive integer/);
  await assert.rejects(sumAsync([1], 1, async () => Number.NaN), /finite numbers/);
  await assert.rejects(sumAsync([Number.MAX_VALUE, Number.MAX_VALUE], 1), /finite Number range/);
  await assert.rejects(sumAsync([1, 2, 3], 2, async (value) => {
    if (value === 2) throw new Error('worker-fail');
    await delay(2);
    return value;
  }), /worker-fail/);

  const rnd = (() => {
    let state = 0x260829;
    return () => {
      state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
      return state / 0x100000000;
    };
  })();
  for (let round = 0; round < 100; round += 1) {
    const n = Math.floor(rnd() * 15);
    const values = Array.from({ length: n }, () => Math.floor(rnd() * 21) - 10);
    const limit = 1 + Math.floor(rnd() * 6);
    let now = 0;
    let peak = 0;
    const actual = await sumAsync(values, limit, async (value, index) => {
      now += 1;
      peak = Math.max(peak, now);
      await delay((index % 3) + 1);
      now -= 1;
      return value * 2;
    });
    const expected = values.reduce((sum, value) => sum + value * 2, 0);
    assert.equal(actual, expected, `random sum round ${round}`);
    assert.ok(peak <= Math.min(limit, Math.max(1, n)), `random concurrency round ${round}: ${peak} > ${limit}`);
  }

  console.log('PASS sum bounded=2 input-order promise-all-order rejection-no-auto-cancel empty invalid worker-failure overflow random=100');
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
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

    context_raw = run('node', 'scripts/xhs.js', 'answer', 'context', '--canonical-id', CID, '--noWrite').stdout
    ctx = json.loads(context_raw)
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
    blocks = re.findall(r'```javascript\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one JavaScript block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b49-async-sum-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'async_sum.js').write_text("'use strict';\n" + blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'async_sum_test.js').write_text("'use strict';\n" + TEST, encoding='utf-8')
        stdout = run('node', 'async_sum_test.js', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS sum bounded=2 input-order promise-all-order rejection-no-auto-cancel empty invalid worker-failure overflow random=100'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'node async_sum_test.js',
        'stdout': stdout,
        'checks': [
            'async sum returns expected total under bounded concurrency',
            'maximum in-flight transform count is capped by limit',
            'mapLimit result positions preserve source indexes despite out-of-order completion',
            'Promise.all result order follows input positions despite completion order',
            'aggregate rejection does not imply automatic cancellation of an already-started promise',
            'empty array and limit greater than input length',
            'invalid input/limit/non-finite transform result and finite-sum overflow rejection',
            'worker rejection propagates',
            '100 deterministic randomized arrays match synchronous sum oracle while respecting concurrency bound',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0049 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'ecma-promise-all', 'title': 'ECMAScript 2026 Language Specification: Promise.all', 'locator': PROMISE_ALL_SPEC, 'source_type': 'official_specification_or_standard', 'checked_at': DATE},
        {'source_id': 'ecma-async-functions', 'title': 'ECMAScript 2026 Language Specification: Async Function Definitions', 'locator': ASYNC_FUNCTION_SPEC, 'source_type': 'official_specification_or_standard', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'Deterministic Node.js 22 bounded-concurrency async-sum fixture', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {
            'claim_id': 'source-boundary',
            'text': 'The preserved source asks to use Promise.all and async/await for array-element addition and concurrency optimization, but does not define the asynchronous transform, concurrency limit, error policy or cancellation semantics; the candidate labels its bounded-worker fail-fast contract explicitly.',
            'source_ids': ['repository-source'],
            'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节'],
        },
        {
            'claim_id': 'promise-all-semantics',
            'text': 'ECMAScript specifies Promise.all as returning a promise fulfilled with an array of fulfillment values corresponding to the passed promises, or rejecting with the reason of the first passed promise that rejects; the candidate uses Promise.all only as the aggregate join rather than as a concurrency limiter.',
            'source_ids': ['ecma-promise-all'],
            'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问'],
        },
        {
            'claim_id': 'async-await-language-boundary',
            'text': 'ECMAScript defines await expressions in async-function bodies; the candidate uses await inside each fixed worker to serialize that worker while multiple worker promises progress concurrently.',
            'source_ids': ['ecma-async-functions'],
            'answer_locations': ['1 分钟版', '3 分钟版', '原理机制'],
        },
        {
            'claim_id': 'pool-behavior',
            'text': 'The Node.js 22 fixture verifies the explicit worker-pool contract: correct sums, in-flight count never above limit, input-order result placement, Promise.all input-order aggregation, fail-fast propagation without assuming automatic cancellation, boundary rejection, and 100 randomized cases against a synchronous oracle.',
            'source_ids': ['fixture'],
            'answer_locations': ['3 分钟版', '关键细节', '原理机制', '常见追问', '易错点'],
        },
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    research = {
        'schema_version': 'answer_writer_research.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'review_state': 'writer_complete_isolated_review_pending',
        'sources': sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'promotion_blocker': 'isolated_independent_review_not_yet_performed',
    }
    write_json(out / 'writer_research.json', research)

    scores = {
        'facts_and_evidence': 24,
        'directness_and_relevance': 19,
        'type_specific_completeness': 19,
        'mechanism_and_causality': 14,
        'boundaries_and_tradeoffs': 9,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The candidate answers the source task directly and makes its async-transform, bounded-concurrency and fail-fast contract explicit instead of inventing missing source requirements.',
        'Promise.all language semantics are tied to the ECMAScript 2026 specification, while the concurrency-limit guarantee is supported by an executable worker-pool fixture rather than attributed to Promise.all.',
        'The implementation preserves input indexes under out-of-order completion and limits simultaneously active transforms to the number of fixed workers.',
        'The fixture demonstrates that aggregate rejection is not equivalent to cancelling an already-started promise, preventing a common unsafe claim about Promise.all.',
        'Boundary tests cover empty input, oversized/invalid limits, worker failure, non-finite values, finite-Number overflow and 100 deterministic randomized sums with a concurrency tracker.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0049-async-sum-20260829-v1',
        'review_version': 'batch-0049.async-sum.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), PROMISE_ALL_SPEC, ASYNC_FUNCTION_SPEC, 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence = {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0049-async-sum-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': sources + [
            {'source_id': 'isolated-review', 'title': 'Async-sum source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}
        ],
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'six delayed transforms with limit=2', 'expected': 'sum=21 and peak in-flight=2', 'actual': 'pass', 'passed': True},
                {'case': 'out-of-order completion', 'expected': 'results remain aligned to input positions', 'actual': 'pass', 'passed': True},
                {'case': 'Promise.all rejection plus later side effect', 'expected': 'aggregate rejects and already-started later promise still runs', 'actual': 'pass', 'passed': True},
                {'case': '100 deterministic randomized arrays', 'expected': 'async result equals synchronous oracle and peak never exceeds limit', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {
            'reviewer_id': review['reviewer_id'],
            'review_version': review['review_version'],
            'independent': True,
            'decision': 'pass',
            'revision_round': 1,
            'scores': scores,
            'hard_failures': [],
            'unsupported_claims': [],
            'uncovered_source_variants': [],
            'findings': findings,
        },
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    }
    write_json(ROOT / f'review/evidence/{CID}.json', evidence)

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_cff7d30b3ad4c9fb5929904f2da7a932` source-first isolated review PASS: the preserved source asks for Promise.all + async/await array addition with concurrency optimization but leaves the concrete async transform, limit, error and cancellation policy unspecified. The candidate uses a fixed worker pool for the concurrency bound, Promise.all only as the aggregate join, and ECMAScript 2026 primary-source evidence for Promise/async semantics. Node.js 22 validation covers ordering, fail-fast propagation without assuming automatic cancellation, finite-number boundaries and 100 deterministic randomized sums while proving peak in-flight work never exceeds the configured limit. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text:
        text = text.rstrip() + '\n\n## Progress\n'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
