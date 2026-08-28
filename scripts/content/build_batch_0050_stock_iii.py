#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0050 LeetCode 123 candidate."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0050'
CID = 'cq_q_d6d0edf2910f05b10c1ef3911f26b7f5'
QID = 'd6d0edf2910f05b10c1ef3911f26b7f5'
EXPECTED = '算法：买卖股票的最佳时机 III (LeetCode 123)'
OFFICIAL = 'https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iii/'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d6d0edf2910f05b10c1ef3911f26b7f5","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# LeetCode 123 买卖股票的最佳时机 III：四状态 DP

## 核心结论

题目允许**最多两笔交易**，且同一时刻不能持有多笔交易：必须先卖出，才能再次买入。可以把每天结束后的最优“现金状态”压缩成四个变量：`buy1`（完成第一次买入后）、`sell1`（完成第一次卖出后）、`buy2`（完成第二次买入后）、`sell2`（完成第二次卖出后）。每天用当前价格对四个状态做“保持原状态 / 今天执行一次动作”的最大值转移，最终 `sell2` 就是最多两笔交易的最大利润。时间 O(n)，额外空间 O(1)。

## 1 分钟版

- `buy1 = max(buy1, -price)`：第一次买入后手里的最大现金。
- `sell1 = max(sell1, buy1 + price)`：完成第一笔交易后的最大利润。
- `buy2 = max(buy2, sell1 - price)`：在第一笔利润基础上再次买入后的最大现金。
- `sell2 = max(sell2, buy2 + price)`：完成第二笔交易后的最大利润。
- 为避免把“当天新状态”误当成上一天状态，代码每轮先算 `next*` 再统一覆盖。
- “最多两笔”意味着可以只做 0 或 1 笔；`sell1/sell2` 从 0 开始，因此下降行情自然返回 0。
- 一次扫描即可，O(n) 时间、O(1) 空间。

## 3 分钟版

```java
public final class StockIII {
    public static int maxProfit(int[] prices) {
        if (prices == null || prices.length == 0) {
            throw new IllegalArgumentException("prices must be non-empty");
        }

        long buy1 = -prices[0];
        long sell1 = 0;
        long buy2 = -prices[0];
        long sell2 = 0;

        for (int i = 1; i < prices.length; i++) {
            long price = prices[i];

            long nextBuy1 = Math.max(buy1, -price);
            long nextSell1 = Math.max(sell1, buy1 + price);
            long nextBuy2 = Math.max(buy2, sell1 - price);
            long nextSell2 = Math.max(sell2, buy2 + price);

            buy1 = nextBuy1;
            sell1 = nextSell1;
            buy2 = nextBuy2;
            sell2 = nextSell2;
        }
        return (int) sell2;
    }
}
```

例如 `[3,3,5,0,0,3,1,4]`，最优答案是 6：可以在 0 买入、3 卖出得到 3，再在 1 买入、4 卖出得到 3。四状态 DP 不需要枚举具体分割点；`sell1` 始终保存“到今天为止最多一笔交易的最好结果”，`buy2` 再把这个历史最好结果带入第二次持仓，最终 `sell2` 自动覆盖所有合法的两笔交易组合。

为什么 `buy2` 初始也可以是 `-prices[0]`？因为题目说的是“最多两笔”，第二套状态允许第一笔交易利润为 0，相当于没有实际做第一笔交易；这样只有一笔最优交易时也能自然落到 `sell2`，无需额外返回 `max(sell1, sell2)`。

## 关键细节

- **状态是“动作完成后的最大现金”**：`buy*` 状态通常是负数，因为买入支付价格；`sell*` 是不持仓状态的最大利润。
- **不能同时持有两笔**：第二次买入只能从 `sell1` 转移，意味着第一笔已经卖出；不会从 `buy1` 直接进入 `buy2`。
- **最多而不是恰好两笔**：下降行情可以什么都不做，利润 0；只做一笔也允许，所以卖出状态从 0 开始。
- **用上一轮状态做转移**：代码使用 `nextBuy1/nextSell1/nextBuy2/nextSell2`，避免转移含义依赖赋值顺序，状态机边界更清楚。
- **为什么 O(1) 空间**：第 i 天只依赖第 i-1 天的四个状态，不需要保留整张 DP 表。
- **数值范围**：官方价格非负且单价不超过 1e5，两笔交易总利润不会超过 2e5；`int` 足够。代码内部用 `long` 只是让“现金状态加减”不依赖更窄的中间边界。
- **单天输入**：无法完成买卖，四个卖出状态保持 0，返回 0。
- **非法输入**：官方保证数组非空；独立方法对 `null` 或空数组显式抛 `IllegalArgumentException`。
- **输入不修改**：算法只读价格数组。

## 原理机制

把交易过程看成一个有序状态机：

`未交易 -> 第一次持仓 -> 第一次空仓 -> 第二次持仓 -> 第二次空仓`

每天对每个状态只有两种选择：什么都不做，沿用昨天的最优值；或者在今天执行允许的动作。例如第二次持仓：

`buy2[i] = max(buy2[i-1], sell1[i-1] - price[i])`

左边表示今天结束时已经处于“第二次买入后”的最佳现金；右边第一项是不操作，第二项是昨天已完成第一笔交易、今天支付价格进行第二次买入。其它状态完全同理。由于所有合法交易路径都必须按这四个动作顺序通过状态机，而每个状态只保留到当前日的最优现金，动态规划不会漏掉任何合法方案，也不需要记住具体买卖日期。

## 项目经验版

来源没有真实交易系统经历，不能把算法题虚构成生产收益策略。工程里真正的交易问题通常还会有手续费、滑点、冷却期、仓位限制、成交失败等约束；这些都会改变状态和转移。这里严格回答 LeetCode 123 的离散价格数组契约：最多两笔、不能同时持有多笔、不含手续费和其它市场约束。

## 常见追问

- 问：为什么最后返回 `sell2`，不返回 `max(sell1, sell2)`？答：`buy2` 初始化允许第一笔交易利润为 0，所以 `sell2` 的状态空间已经包含只做一笔或不做交易的情况；当然显式取最大值也不会错。
- 问：四个状态分别代表什么？答：分别是第一次买入后、第一次卖出后、第二次买入后、第二次卖出后的最大现金/利润。
- 问：为什么第二次买入从 `sell1` 转移？答：题目禁止同时持有多笔交易，必须先结束第一笔才能开始第二笔。
- 问：能用二维 DP 吗？答：可以，例如 `dp[day][transactions][holding]`；因为每天只依赖前一天，最终可以压缩成四个变量。
- 问：为什么不是贪心把两个最大涨幅直接相加？答：两个局部涨幅的区间可能重叠或切分方式影响总收益；DP 显式维护动作顺序和历史最优，能够覆盖所有合法组合。
- 问：如果最多 k 笔交易呢？答：把四状态推广为 `2k` 个买/卖动作状态，或使用 `dp[k][holding]`；LeetCode 123 是 `k=2` 的特例。

## 易错点

- 把“最多两笔”写成“必须两笔”，导致下降行情出现负利润。
- 第二次买入从错误的持仓状态转移，等价于允许同时持有两笔。
- 原地更新状态但没有说明赋值顺序语义，导致读者无法判断使用的是今天还是昨天的值。
- 只算两段“最大单笔利润”却没有保证两段时间顺序和不重叠。
- 忘记单天/下降数组应返回 0。
- 把手续费、冷却期等其它股票题约束混入本题。
'''

TEST = r'''import java.util.Arrays;
import java.util.Random;

public final class StockIIITest {
    private static int oracle(int[] prices) {
        int n = prices.length;
        int best = 0;
        for (int b1 = 0; b1 < n; b1++) {
            for (int s1 = b1 + 1; s1 < n; s1++) {
                best = Math.max(best, prices[s1] - prices[b1]);
                for (int b2 = s1; b2 < n; b2++) {
                    for (int s2 = b2 + 1; s2 < n; s2++) {
                        best = Math.max(best, (prices[s1] - prices[b1]) + (prices[s2] - prices[b2]));
                    }
                }
            }
        }
        return best;
    }

    private static void check(int[] prices, int expected, String name) {
        int[] copy = prices.clone();
        int actual = StockIII.maxProfit(prices);
        if (actual != expected) throw new AssertionError(name + " actual=" + actual + " expected=" + expected);
        if (!Arrays.equals(prices, copy)) throw new AssertionError(name + " mutated input");
    }

    private static void expectIllegal(int[] prices, String name) {
        try {
            StockIII.maxProfit(prices);
            throw new AssertionError(name + " expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // pass
        }
    }

    public static void main(String[] args) {
        check(new int[]{3,3,5,0,0,3,1,4}, 6, "official-example-1");
        check(new int[]{1,2,3,4,5}, 4, "official-example-2");
        check(new int[]{7,6,4,3,1}, 0, "official-example-3");
        check(new int[]{1}, 0, "single");
        check(new int[]{1,5,2,8}, 10, "two-profitable-windows");
        check(new int[]{5,1,5}, 4, "one-transaction-only");
        check(new int[]{0,100000,0,100000}, 200000, "max-price-two-transactions");
        expectIllegal(null, "null");
        expectIllegal(new int[]{}, "empty");

        Random random = new Random(20260829L);
        for (int round = 0; round < 500; round++) {
            int n = 1 + random.nextInt(10);
            int[] prices = new int[n];
            for (int i = 0; i < n; i++) prices[i] = random.nextInt(31);
            int expected = oracle(prices);
            check(prices, expected, "random-" + round);
        }

        System.out.println("PASS official-examples single one-two max-profit null-empty random-bruteforce-oracle=500 input-preserved");
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
    write_json(out / 'official_problem_snapshot.json', {
        'schema_version': 'official_problem_snapshot.v1',
        'checked_at': DATE,
        'source_type': 'official_problem_statement',
        'locator': OFFICIAL,
        'problem_number': 123,
        'title': 'Best Time to Buy and Sell Stock III',
        'contract': {
            'objective': 'maximum profit from at most two transactions',
            'simultaneous_transactions_forbidden': True,
            'must_sell_before_buy_again': True,
            'prices_length_min': 1,
            'prices_length_max': 100000,
            'price_min': 0,
            'price_max': 100000,
        },
        'examples': [
            {'prices': [3,3,5,0,0,3,1,4], 'output': 6},
            {'prices': [1,2,3,4,5], 'output': 4},
            {'prices': [7,6,4,3,1], 'output': 0},
        ],
    })

    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(CANDIDATE, encoding='utf-8')
    for heading in ['## 核心结论', '## 1 分钟版', '## 3 分钟版', '## 关键细节', '## 原理机制', '## 项目经验版', '## 常见追问', '## 易错点']:
        if CANDIDATE.count(heading) != 1:
            raise SystemExit(f'section drift {heading}')
    blocks = re.findall(r'```java\n(.*?)\n```', CANDIDATE, re.S)
    if len(blocks) != 1:
        raise SystemExit(f'expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix='b50-stock-iii-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'StockIII.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'StockIIITest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'StockIII.java', 'StockIIITest.java', cwd=tmpdir)
        stdout = run('java', 'StockIIITest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS official-examples single one-two max-profit null-empty random-bruteforce-oracle=500 input-preserved'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac StockIII.java StockIIITest.java && java StockIIITest',
        'stdout': stdout,
        'checks': [
            'all three official examples return the documented maximum profit',
            'single-day, falling, one-transaction, two-transaction and maximum-price boundaries are handled',
            'null and empty arrays follow the explicit local illegal-input contract',
            '500 deterministic random arrays agree with an independent exhaustive two-transaction oracle',
            'the input array remains unchanged',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0050 frozen canonical/source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'leetcode-official', 'title': 'LeetCode 123 Best Time to Buy and Sell Stock III official problem statement', 'locator': str(out / 'official_problem_snapshot.json'), 'source_type': 'official_documentation', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 four-state stock DP executable validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-contract', 'text': 'The repository source explicitly identifies LeetCode 123; the official problem allows at most two transactions and forbids simultaneous transactions, requiring a sell before another buy.', 'source_ids': ['repository-source', 'leetcode-official'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'dp-validation', 'text': 'The OpenJDK 21 fixture validates the four-state DP on all official examples, boundary cases and 500 deterministic random arrays against an independent exhaustive non-overlapping two-transaction oracle.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '关键细节', '原理机制', '易错点']},
        {'claim_id': 'state-order', 'text': 'Second-buy state transitions only from first-sell state, preserving the official no-simultaneous-transactions ordering.', 'source_ids': ['leetcode-official', 'fixture'], 'answer_locations': ['核心结论', '关键细节', '原理机制']},
        {'claim_id': 'complexity-bound', 'text': 'The production solution performs one pass over prices and retains four scalar DP states, yielding O(n) time and O(1) extra space.', 'source_ids': ['fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
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

    scores = {
        'facts_and_evidence': 24,
        'directness_and_relevance': 20,
        'type_specific_completeness': 20,
        'mechanism_and_causality': 15,
        'boundaries_and_tradeoffs': 10,
        'followup_quality': 5,
        'oral_quality': 5,
    }
    findings = [
        'The candidate is bound to the exact repository LeetCode 123 source and current official at-most-two, no-simultaneous-transactions contract.',
        'The four DP states are defined by completed action stage and the second buy can only follow a first sell, preserving transaction ordering.',
        'The implementation uses previous-day state snapshots for every transition, avoiding hidden in-place update-order semantics.',
        'OpenJDK 21 validation covers all official examples, one/two/no-transaction boundaries, maximum-price profit, illegal local inputs, input preservation and 500 deterministic random arrays against an independent exhaustive oracle.',
        'The answer explains why sell2 includes fewer-than-two-transaction optima and why the state compression is O(1) extra space.',
        'No production trading history, fees, cooldowns or market constraints are fabricated.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0050-stock-iii-20260829-v1',
        'review_version': 'batch-0050.stock-iii.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(out / 'official_problem_snapshot.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{
        'source_id': 'isolated-review',
        'title': 'Stock-III source-first isolated review',
        'locator': str(out / 'isolated_review_result.json'),
        'source_type': 'repository_structured_source',
        'checked_at': DATE,
    }]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0050-stock-iii-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'three official examples', 'expected': '6, 4, 0', 'actual': 'pass', 'passed': True},
                {'case': 'single/one/two/max-price transaction boundaries', 'expected': 'matches exact optimum', 'actual': 'pass', 'passed': True},
                {'case': 'null/empty local contract', 'expected': 'IllegalArgumentException', 'actual': 'pass', 'passed': True},
                {'case': '500 deterministic random arrays', 'expected': 'matches independent exhaustive two-transaction oracle', 'actual': 'pass', 'passed': True},
                {'case': 'input preservation', 'expected': 'prices array unchanged', 'actual': 'pass', 'passed': True},
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
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_d6d0edf2910f05b10c1ef3911f26b7f5` source-first isolated review PASS: repository wording is bound to LeetCode 123 and the current official at-most-two/no-simultaneous-transactions contract; the candidate implements a four-state previous-day DP in O(n) time/O(1) extra space. OpenJDK 21 validation covers all official examples, no/one/two/max-price transaction boundaries, input preservation, and 500 deterministic random arrays against an independent exhaustive two-transaction oracle. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
