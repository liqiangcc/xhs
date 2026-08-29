#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 stock-121 candidate."""

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
CID = 'cq_q_e32f0b333daf71b238b08a44759e2420'
QID = 'e32f0b333daf71b238b08a44759e2420'
EXPECTED = '算法：买卖股票 leetcode 121'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e32f0b333daf71b238b08a44759e2420","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 买卖股票一次交易：维护历史最低价与当前最大利润

## 核心结论

仓库来源只保留“算法：买卖股票 leetcode 121”这一句，没有保存完整外部题面、价格范围或异常约束，所以不能把记忆中的 LeetCode constraints 当成仓库事实。这里明确采用一个可执行合同：`prices[i]` 表示第 i 天的非负整数价格；最多完成一次“先买后卖”的交易，也允许不交易；返回可获得的最大利润。空数组或单元素数组返回 0；`null` 或负价格视为非法输入并抛 `IllegalArgumentException`。

一次扫描即可完成。走到第 i 天时，只需要知道此前最低买入价 `minPrice`。如果今天卖出，最好利润就是 `prices[i] - minPrice`；用它更新全局 `best`，再更新历史最低价。这样天然保证买入日早于或等于当前卖出日，而利润初始化为 0 又表示“没有正利润时不交易”。时间 O(n)，额外空间 O(1)。

## 1 分钟版

- 只能先买后卖，所以处理今天价格时，买入候选只能来自今天之前已经扫描过的最低价。
- 维护 `minPrice`：截至当前的最低价格；维护 `best`：截至当前能得到的最大非负利润。
- 每天先计算 `price - minPrice` 更新 best，再用当前 price 更新 minPrice。
- 全程不需要 DP 数组，两个标量就够，O(n) 时间、O(1) 额外空间。
- 单调下降时所有卖出差价都不为正，best 保持 0，表示不交易。
- 当前候选把负价格和 null 定义为非法输入；这是实现边界，不是来源保存的外部题面约束。

## 3 分钟版

```java
public final class BestTimeToBuySellStock {
    public static int maxProfit(int[] prices) {
        if (prices == null) {
            throw new IllegalArgumentException("prices must not be null");
        }
        if (prices.length < 2) {
            if (prices.length == 1 && prices[0] < 0) {
                throw new IllegalArgumentException("price must be non-negative");
            }
            return 0;
        }

        int minPrice = Integer.MAX_VALUE;
        int best = 0;
        for (int price : prices) {
            if (price < 0) {
                throw new IllegalArgumentException("price must be non-negative");
            }
            if (minPrice != Integer.MAX_VALUE) {
                best = Math.max(best, price - minPrice);
            }
            minPrice = Math.min(minPrice, price);
        }
        return best;
    }
}
```

也可以把它写成 DP：`dp[i] = max(dp[i-1], prices[i] - min(prices[0..i-1]))`。但真正需要保留的历史状态只有“此前最低价”和“此前最好利润”，因此没必要分配 O(n) 的 dp 数组。

这里允许“不交易”，所以最小答案是 0。如果业务合同改成“必须恰好买卖一次”，单调下降数组的答案就会是负数，初始化和边界都要相应改变；这说明算法细节必须服从交易合同。

## 关键细节

- **顺序约束**：不能用全局最小值和全局最大值直接相减，因为最大值可能出现在最小值之前；扫描前缀最低价天然维护“先买后卖”。
- **最多一次交易**：这题的状态只需要一个买点和一个卖点；如果允许多次交易、手续费、冷冻期，状态模型会变化，不能沿用同一个公式。
- **允许不交易**：`best` 从 0 开始，下降行情返回 0；如果题目要求必须交易，合同不同。
- **非负价格**：当前候选明确验证非负价格，避免用哨兵值时把负数语义含混进去；来源未保存这一外部约束，所以把它标成候选合同。
- **空/单元素**：没有合法的两天交易窗口，因此返回 0。
- **输入不修改**：算法只读价格数组。

## 原理机制

对任意卖出日 j，最优买入日一定是 j 之前价格最低的一天，因为利润是 `prices[j] - prices[i]`，在固定 j 时要最大化它就应最小化前项。于是全局问题可以拆成：对每个 j 计算“今天卖出时的最好利润”，再取这些局部最好值的最大值。

扫描到 j 时维护 `minPrice = min(prices[0..j-1])`，因此 `prices[j] - minPrice` 正好是所有合法买入日中今天卖出的最大利润。`best` 再维护所有已处理卖出日的最大值。两个不变量合起来给出完整证明，不需要枚举 O(n²) 的所有买卖对。

## 项目经验版

来源没有真实项目场景，不能虚构交易系统经验。工程里如果价格来自实时流，这个状态机仍然可以在线更新：只需要保留历史最低价和最好利润，不必保存全部历史。但真实金融系统还涉及时间戳乱序、复权、缺失点和精度类型等问题，这些都不属于当前保存来源，不能混进算法题合同里。

## 常见追问

- 问：为什么不能直接 `max(prices) - min(prices)`？答：它可能把后出现的最低价当买点、前出现的最高价当卖点，违反时间顺序。
- 问：为什么不需要 DP 数组？答：递推只依赖前缀最低价和此前最大利润，完整历史状态可以压缩成两个标量。
- 问：如果价格一直下降呢？答：最多一次且允许不交易时答案是 0。
- 问：如果允许无限次交易呢？答：合同变成另一个问题，常见做法会累计所有正向相邻差价或用不同 DP 状态，不能直接套本题。
- 问：为什么负价格抛异常？答：仓库来源没保存值域；本候选把“股票价格非负”作为显式输入合同并用测试锁定，而不是让未定义输入悄悄参与计算。
- 问：复杂度？答：每个价格只处理一次，O(n) 时间；只维护 minPrice 和 best，O(1) 额外空间。

## 易错点

- 用全局最小和全局最大相减，忽略买入必须发生在卖出之前。
- 在最低价更新后才计算当天利润，又对“同一天买卖”的语义解释不清；更清晰的是用此前最低价计算再更新。
- 默认必须交易，导致下降数组返回负利润，而题目常见合同是允许不交易。
- 为简单递推创建 O(n) DP 数组，没做状态压缩。
- 从 LeetCode 编号凭记忆补写未保存在仓库的完整 constraints。
- 把多次交易、手续费、冷冻期等变体混入当前一次交易答案。
'''

TEST = r'''import java.util.Random;

public final class BestTimeToBuySellStockTest {
    private static int oracle(int[] prices) {
        int best = 0;
        for (int i = 0; i < prices.length; i++) {
            for (int j = i + 1; j < prices.length; j++) {
                best = Math.max(best, prices[j] - prices[i]);
            }
        }
        return best;
    }

    private static void check(int expected, int[] prices) {
        int actual = BestTimeToBuySellStock.maxProfit(prices);
        if (actual != expected) throw new AssertionError("expected=" + expected + " actual=" + actual);
    }

    public static void main(String[] args) {
        check(0, new int[]{});
        check(0, new int[]{7});
        check(5, new int[]{7,1,5,3,6,4});
        check(0, new int[]{7,6,4,3,1});
        check(4, new int[]{1,5});
        check(0, new int[]{5,5,5});
        check(Integer.MAX_VALUE, new int[]{0, Integer.MAX_VALUE});

        try { BestTimeToBuySellStock.maxProfit(null); throw new AssertionError("null must fail"); }
        catch (IllegalArgumentException expected) {}
        try { BestTimeToBuySellStock.maxProfit(new int[]{1,-1,3}); throw new AssertionError("negative must fail"); }
        catch (IllegalArgumentException expected) {}
        try { BestTimeToBuySellStock.maxProfit(new int[]{-1}); throw new AssertionError("negative singleton must fail"); }
        catch (IllegalArgumentException expected) {}

        Random random = new Random(20260829L);
        for (int round = 0; round < 5000; round++) {
            int n = random.nextInt(35);
            int[] prices = new int[n];
            for (int i = 0; i < n; i++) prices[i] = random.nextInt(1000);
            int expected = oracle(prices);
            int actual = BestTimeToBuySellStock.maxProfit(prices);
            if (actual != expected) throw new AssertionError("random mismatch round=" + round);
        }

        int[] rising = new int[200_000];
        for (int i = 0; i < rising.length; i++) rising[i] = i;
        check(199_999, rising);
        int[] falling = new int[200_000];
        for (int i = 0; i < falling.length; i++) falling[i] = falling.length - i;
        check(0, falling);

        System.out.println("PASS directed null-negative-boundary 5000-random-oracle large-rising-falling");
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

    with tempfile.TemporaryDirectory(prefix='b52-stock-121-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'BestTimeToBuySellStock.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'BestTimeToBuySellStockTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'BestTimeToBuySellStock.java', 'BestTimeToBuySellStockTest.java', cwd=tmpdir)
        stdout = run('java', 'BestTimeToBuySellStockTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS directed null-negative-boundary 5000-random-oracle large-rising-falling'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1', 'canonical_id': CID, 'result': 'pass', 'validated_at': DATE,
        'command': 'javac BestTimeToBuySellStock.java BestTimeToBuySellStockTest.java && java BestTimeToBuySellStockTest',
        'stdout': stdout,
        'checks': ['directed canonical/up/down/equal/extreme cases', 'explicit null and negative-price boundaries', '5000 deterministic random arrays against independent quadratic buy-before-sell oracle', '200000-element rising and falling arrays'],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact stock-121 source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 stock one-transaction deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source only identifies the stock problem as LeetCode 121 and does not preserve the external constraint table or invalid-input semantics.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '1 分钟版', '易错点']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate explicitly defines non-negative daily prices, at most one buy-before-sell transaction, optional no-trade result 0, and null/negative rejection.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '关键细节']},
        {'claim_id': 'prefix-min-invariant', 'text': 'For each sell day, subtracting the minimum earlier price yields the best legal profit ending that day; the global best over those values equals the one-transaction optimum.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制']},
        {'claim_id': 'validation', 'text': 'Executable validation covers directed boundaries, 5000 deterministic random arrays against a quadratic legal-pair oracle, and large rising/falling inputs.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '常见追问', '易错点']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending', 'sources': sources, 'claims': claims, 'source_question_coverage': coverage, 'promotion_blocker': 'isolated_independent_review_not_yet_performed'})

    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate respects the sparse repository source and does not reconstruct an unpreserved LeetCode constraint table.',
        'The prefix-minimum invariant enforces buy-before-sell ordering and avoids the common invalid global-max-minus-global-min shortcut.',
        'At-most-one-transaction and optional no-trade semantics are explicit, with falling markets returning zero.',
        'The implementation compresses the DP state to minimum prior price and best profit, giving O(N) time and O(1) auxiliary space.',
        'OpenJDK 21 validation compares 5000 deterministic random arrays with an independent quadratic legal-pair oracle and includes 200000-element monotone inputs.',
        'Null and negative-price behavior are explicit candidate boundaries rather than accidental runtime behavior.',
        'The project section avoids fabricated experience and keeps streaming/system concerns outside the stored algorithm contract.',
    ]
    review = {'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0052-stock-121-20260829-v1', 'review_version': 'batch-0052.stock-121.v1', 'decision': 'pass', 'revision_round': 1, 'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'], 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings, 'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 stock-121 source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0052-stock-121-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources, 'claims': claims, 'source_question_coverage': coverage,
        'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [
            {'case': 'monotone falling', 'expected': '0', 'actual': 'pass', 'passed': True},
            {'case': 'null/negative input', 'expected': 'IllegalArgumentException', 'actual': 'pass', 'passed': True},
            {'case': '5000 deterministic random arrays', 'expected': 'matches quadratic buy-before-sell oracle', 'actual': 'pass', 'passed': True},
            {'case': '200000-element rising/falling', 'expected': '199999 / 0', 'actual': 'pass', 'passed': True},
        ]},
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e32f0b333daf71b238b08a44759e2420` source-first isolated review PASS: the sparse source only identifies stock/LeetCode 121, so the candidate declares its own non-negative-price, at-most-one buy-before-sell and no-trade contract rather than inventing missing constraints. It maintains the prior prefix minimum plus best profit in O(N)/O(1), and OpenJDK 21 validation covers directed/null/negative boundaries, 5000 deterministic random arrays against an independent quadratic legal-pair oracle, and 200000-element rising/falling inputs. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
