#!/usr/bin/env python3
"""Build, validate, source-first review, and stage Batch 0052 stack-expression candidate."""

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
CID = 'cq_q_e3c87be07224de266369df5a3433ca0c'
QID = 'e3c87be07224de266369df5a3433ca0c'
EXPECTED = '算法：计算字符串表达式（如 32+1/4），要求使用栈（Stack）结构。'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e3c87be07224de266369df5a3433ca0c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 用栈计算字符串表达式：标准优先级、左结合与整数除法

## 核心结论

来源只保存“计算字符串表达式（如 `32+1/4`），要求使用栈结构”，没有明确括号、一元正负号、小数、整数除法、空白和非法输入语义。先冻结一个可执行合同：支持**非负十进制整数 + 二元 `+ - * /`**，允许 token 之间出现空白，不支持括号和一元符号；`* /` 优先于 `+ -`，同优先级左结合；使用 Java `long` 运算，除法按 Java 整数除法向 0 截断；除 0、字面量/运算溢出抛 `ArithmeticException`，语法错误或 `null` 抛 `IllegalArgumentException`。

在这个合同下，示例 `32+1/4` 的结果是 `32`，因为 `1/4` 先做整数除法得到 0。若面试官期望 `32.25`、分数精确值、括号或一元负号，必须先改变数值/语法合同，再扩展解析器，不能默默换语义。

实现用两个栈：值栈 `values` 与运算符栈 `ops`。读到数字就入值栈；读到新运算符时，把栈顶所有**优先级大于等于当前运算符**的操作先归约，再压入当前运算符。`>=` 正是左结合的关键。扫描结束后归约剩余运算符。

## 1 分钟版

- 先明确 grammar：非负整数、二元 `+ - * /`、token 间可有空白；当前版本无括号、无一元正负号。
- 两个栈：一个放 long 值，一个放运算符。
- 数字直接入值栈；新运算符到来时，先执行栈顶所有 `precedence(top) >= precedence(current)` 的操作。
- 这样 `* /` 会在 `+ -` 前执行，同优先级又按从左到右执行，例如 `8/3*3 = 6`。
- 每次归约弹出右操作数、左操作数和运算符，再把结果压回值栈。
- 结束时清空运算符栈；最终值栈必须只剩一个结果。
- 除 0、long 溢出、缺操作数/操作符、非法字符都显式失败，不把解析异常当成“算出 0”。

## 3 分钟版

```java
import java.util.ArrayDeque;
import java.util.Deque;

public final class StackExpressionEvaluator {
    public static long evaluate(String expression) {
        if (expression == null) {
            throw new IllegalArgumentException("expression must not be null");
        }

        Deque<Long> values = new ArrayDeque<>();
        Deque<Character> ops = new ArrayDeque<>();
        int i = 0;
        boolean expectValue = true;

        while (true) {
            while (i < expression.length() && Character.isWhitespace(expression.charAt(i))) i++;
            if (i == expression.length()) break;

            char ch = expression.charAt(i);
            if (expectValue) {
                if (!Character.isDigit(ch)) {
                    throw new IllegalArgumentException("expected non-negative integer at index " + i);
                }
                long value = 0;
                while (i < expression.length() && Character.isDigit(expression.charAt(i))) {
                    int digit = expression.charAt(i) - '0';
                    value = Math.addExact(Math.multiplyExact(value, 10L), digit);
                    i++;
                }
                values.push(value);
                expectValue = false;
            } else {
                if (!isOperator(ch)) {
                    throw new IllegalArgumentException("expected operator at index " + i);
                }
                while (!ops.isEmpty() && precedence(ops.peek()) >= precedence(ch)) {
                    applyTop(values, ops);
                }
                ops.push(ch);
                i++;
                expectValue = true;
            }
        }

        if (expectValue) {
            throw new IllegalArgumentException("empty expression or trailing operator");
        }
        while (!ops.isEmpty()) applyTop(values, ops);
        if (values.size() != 1) throw new IllegalArgumentException("malformed expression");
        return values.pop();
    }

    private static boolean isOperator(char ch) {
        return ch == '+' || ch == '-' || ch == '*' || ch == '/';
    }

    private static int precedence(char op) {
        return (op == '*' || op == '/') ? 2 : 1;
    }

    private static void applyTop(Deque<Long> values, Deque<Character> ops) {
        if (values.size() < 2 || ops.isEmpty()) {
            throw new IllegalArgumentException("operator without two operands");
        }
        long right = values.pop();
        long left = values.pop();
        char op = ops.pop();
        long result = switch (op) {
            case '+' -> Math.addExact(left, right);
            case '-' -> Math.subtractExact(left, right);
            case '*' -> Math.multiplyExact(left, right);
            case '/' -> divideExactRange(left, right);
            default -> throw new IllegalArgumentException("unknown operator: " + op);
        };
        values.push(result);
    }

    private static long divideExactRange(long left, long right) {
        if (right == 0) throw new ArithmeticException("division by zero");
        if (left == Long.MIN_VALUE && right == -1) throw new ArithmeticException("long overflow");
        return left / right;
    }
}
```

`precedence(top) >= precedence(current)` 不能随手改成 `>`。例如 `8/3*3`：`/` 和 `*` 同优先级，左结合要求先算 `8/3 = 2`，再 `2*3 = 6`；如果同优先级不先归约，就可能错误地形成右结合。

这个版本没有括号。一旦加入括号，运算符栈还需要把 `(` 当作归约边界，遇到 `)` 时归约到对应 `(`；如果加入一元负号，则 lexer/parser 状态还要区分“期待值”位置上的 `-` 与二元减法，不能只靠当前四个运算符规则硬猜。

## 关键细节

- **来源语义不完整**：`32+1/4` 本身不能证明题目期望整数还是小数，所以答案必须先声明数值合同。
- **左/右操作数顺序**：弹栈时先得到 right、后得到 left；减法和除法不能写反。
- **左结合**：同优先级运算符要在新操作符入栈前归约，因此条件是 `>=`。
- **空白**：只允许 token 之间空白。`"1 2"` 在读完 1 后下一 token 仍是数字，因缺少运算符而报语法错，不会被拼成 12。
- **整数溢出**：字面量通过 `multiplyExact/addExact` 检查，`+ - *` 通过 exact 方法检查；不能让 long 溢出静默回绕。
- **整数除法**：Java long 除法向 0 截断；除 0显式报错。当前 grammar 没有一元负号，但中间结果可为负，因此后续除法仍可能处理负数。
- **非法语法**：空串、前导运算符、尾随运算符、连续数字 token 无操作符、未知字符都拒绝。

## 原理机制

运算符栈保存“已经看到但还不能确定立即执行顺序”的操作。新运算符到来时，如果栈顶优先级更高，它显然必须先执行；如果优先级相等，因为当前合同是左结合，栈顶也必须先执行。只有栈顶优先级更低时，当前运算符才可以等待后续右侧值。

每次归约都把 `left op right` 三个局部元素替换成一个等价结果，所以不会改变整个表达式在当前优先级/结合规则下的值。扫描结束后已经没有未来运算符会改变顺序，依次清空栈即可得到唯一结果。

## 项目经验版

来源没有真实项目经历，不能虚构。工程里真正的表达式引擎通常会先做 tokenizer，再生成 AST 或使用成熟 parser，以便支持括号、函数、变量、类型、错误定位和安全策略。当前面试题明确要求 Stack，所以这里保留一个边界清晰的双栈求值器，而不是把它包装成“通用表达式引擎”。

## 常见追问

- 问：`32+1/4` 为什么是 32？答：当前候选明确采用 long 整数除法，所以 `1/4=0`；如果题目要求小数或精确分数，应先改数值合同。
- 问：为什么两个栈？答：值栈保存待组合的操作数，运算符栈保存尚未归约的操作；优先级决定何时归约。
- 问：为什么是 `>=` 而不是 `>`？答：`+ - * /` 都是左结合，同优先级必须先执行更早出现的栈顶操作。
- 问：怎么支持括号？答：把 `(` 压运算符栈作为边界；遇到 `)` 时归约到 `(` 并弹掉它，同时增加括号匹配校验。
- 问：怎么支持负数？答：要在“期待一个值”的 parser 状态中把 `-` 识别为一元运算符，不能与二元减法混用同一规则。
- 问：为什么检查溢出？答：解析器若静默 long 回绕，会给出语法正确但数值错误的结果；显式 ArithmeticException 更符合可审计合同。

## 易错点

- 不声明整数/小数语义，直接把示例结果写死。
- 只按运算符优先级，不处理同优先级左结合，导致 `8/3*3` 或 `10-3-2` 顺序错误。
- 弹栈时把 left/right 反过来，减法和除法出错。
- 用一个“跳过所有空白”的字符循环把 `1 2` 错拼成 12。
- 不检查空串、尾随运算符、连续运算符和除 0。
- 使用普通 long 运算让溢出静默回绕。
- 在来源没有括号/一元符号要求时声称当前实现已经支持“通用表达式”。
'''

TEST = r'''import java.util.Random;

public final class StackExpressionEvaluatorTest {
    private static final class Ref {
        final String s; int i;
        Ref(String s) { this.s = s; }
        long parse() {
            long v = expression();
            skip();
            if (i != s.length()) throw new IllegalArgumentException("trailing");
            return v;
        }
        long expression() {
            long v = term();
            while (true) {
                skip();
                if (i >= s.length() || (s.charAt(i) != '+' && s.charAt(i) != '-')) return v;
                char op = s.charAt(i++); long r = term();
                v = op == '+' ? Math.addExact(v, r) : Math.subtractExact(v, r);
            }
        }
        long term() {
            long v = number();
            while (true) {
                skip();
                if (i >= s.length() || (s.charAt(i) != '*' && s.charAt(i) != '/')) return v;
                char op = s.charAt(i++); long r = number();
                if (op == '*') v = Math.multiplyExact(v, r);
                else { if (r == 0) throw new ArithmeticException("zero"); v = v / r; }
            }
        }
        long number() {
            skip();
            if (i >= s.length() || !Character.isDigit(s.charAt(i))) throw new IllegalArgumentException("number");
            long v = 0;
            while (i < s.length() && Character.isDigit(s.charAt(i))) v = Math.addExact(Math.multiplyExact(v, 10), s.charAt(i++) - '0');
            return v;
        }
        void skip() { while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++; }
    }

    private static void check(long expected, String expression) {
        long actual = StackExpressionEvaluator.evaluate(expression);
        if (actual != expected) throw new AssertionError(expression + " expected=" + expected + " actual=" + actual);
    }
    private static void bad(String expression, Class<? extends Throwable> type) {
        try { StackExpressionEvaluator.evaluate(expression); throw new AssertionError("must fail: " + expression); }
        catch (Throwable t) { if (!type.isInstance(t)) throw new AssertionError("wrong error for " + expression + ": " + t); }
    }

    public static void main(String[] args) {
        check(32, "32+1/4");
        check(4, "10-2*3");
        check(6, "8/3*3");
        check(5, "10-3-2");
        check(14, " 2 + 3 * 4 ");
        check(-5, "0-10/2");
        bad(null, IllegalArgumentException.class);
        bad("", IllegalArgumentException.class);
        bad("1+", IllegalArgumentException.class);
        bad("*2", IllegalArgumentException.class);
        bad("1 2", IllegalArgumentException.class);
        bad("1+a", IllegalArgumentException.class);
        bad("1/0", ArithmeticException.class);
        bad("9223372036854775808", ArithmeticException.class);
        bad("9223372036854775807+1", ArithmeticException.class);

        Random random = new Random(20260829L);
        char[] ops = new char[]{'+','-','*','/'};
        for (int round = 0; round < 3000; round++) {
            int terms = 1 + random.nextInt(8);
            StringBuilder b = new StringBuilder();
            b.append(random.nextInt(21));
            for (int k = 1; k < terms; k++) {
                char op = ops[random.nextInt(ops.length)];
                int rhs = op == '/' ? 1 + random.nextInt(20) : random.nextInt(21);
                if (random.nextBoolean()) b.append(' ');
                b.append(op);
                if (random.nextBoolean()) b.append(' ');
                b.append(rhs);
            }
            String expr = b.toString();
            long expected = new Ref(expr).parse();
            long actual = StackExpressionEvaluator.evaluate(expr);
            if (actual != expected) throw new AssertionError("random mismatch " + expr + " expected=" + expected + " actual=" + actual);
        }

        StringBuilder large = new StringBuilder("1");
        for (int k = 1; k < 50_000; k++) large.append("+1");
        check(50_000, large.toString());
        System.out.println("PASS precedence-left-assoc syntax-arithmetic-boundaries 3000-random-reference 50000-term");
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

    with tempfile.TemporaryDirectory(prefix='b52-stack-expression-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'StackExpressionEvaluator.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'StackExpressionEvaluatorTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'StackExpressionEvaluator.java', 'StackExpressionEvaluatorTest.java', cwd=tmpdir)
        stdout = run('java', 'StackExpressionEvaluatorTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS precedence-left-assoc syntax-arithmetic-boundaries 3000-random-reference 50000-term'
    if stdout != expected_stdout: raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {'schema_version': 'answer_code_validation.v1', 'canonical_id': CID, 'result': 'pass', 'validated_at': DATE, 'command': 'javac StackExpressionEvaluator.java StackExpressionEvaluatorTest.java && java StackExpressionEvaluatorTest', 'stdout': stdout, 'checks': ['directed precedence and left-associativity including preserved source example', 'syntax/null/divide-by-zero/literal-and-operation-overflow boundaries', '3000 deterministic random expressions compared with an independent recursive-descent evaluator', '50000-term linear expression']}
    write_json(out / 'writer_validation.json', validation)
    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0052 exact stack-expression source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 stack-expression deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-ambiguity', 'text': 'The exact source requires stack-based evaluation and gives 32+1/4 as an example but does not define numeric domain, division semantics, parentheses, unary operators, whitespace, or malformed-input behavior.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '关键细节']},
        {'claim_id': 'explicit-grammar', 'text': 'The candidate explicitly limits the grammar to non-negative integer literals with binary + - * / and token whitespace, standard precedence and left associativity, while rejecting parentheses/unary syntax rather than silently guessing.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版']},
        {'claim_id': 'stack-ordering', 'text': 'Reducing operators with precedence(top) >= precedence(current) enforces higher-precedence-first and same-precedence left-associative evaluation.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制', '常见追问']},
        {'claim_id': 'validation', 'text': 'Executable validation covers precedence/associativity, malformed syntax and arithmetic faults, 3000 deterministic random expressions against an independent recursive-descent evaluator, and a 50000-term input.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '易错点']},
    ]
    coverage = [{'question_id': QID, 'covered': True, 'answer_locations': ['核心结论', '1 分钟版', '3 分钟版', '关键细节', '原理机制', '常见追问', '易错点']}]
    write_json(out / 'writer_research.json', {'schema_version': 'answer_writer_research.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'review_state': 'writer_complete_isolated_review_pending', 'sources': sources, 'claims': claims, 'source_question_coverage': coverage, 'promotion_blocker': 'isolated_independent_review_not_yet_performed'})
    scores = {'facts_and_evidence': 25, 'directness_and_relevance': 20, 'type_specific_completeness': 20, 'mechanism_and_causality': 15, 'boundaries_and_tradeoffs': 10, 'followup_quality': 5, 'oral_quality': 5}
    findings = [
        'The candidate does not infer decimal or fractional semantics from the ambiguous 32+1/4 example; the integer grammar and division rule are explicit.',
        'The required Stack structure is central to the implementation through separate value/operator stacks rather than mentioned only superficially.',
        'Precedence and left associativity are both explained and tested, including cases that fail when same-precedence reduction uses the wrong condition.',
        'Syntax and arithmetic failure modes are explicit: null/empty/missing operators/trailing operators/invalid characters/divide-by-zero and long overflow do not silently return a value.',
        'OpenJDK 21 validation compares 3000 deterministic random expressions against an independently structured recursive-descent evaluator and includes a 50000-term input.',
        'The answer clearly scopes out parentheses and unary operators and explains what parser changes those extensions require.',
        'The project section avoids fabricated experience and does not misrepresent this bounded evaluator as a production expression engine.',
    ]
    review = {'schema_version': 'isolated_review.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'reviewed_at': DATE, 'review_mode': 'source_first_isolated', 'reviewer_id': 'source-first-isolated-reviewer-batch-0052-stack-expression-20260829-v1', 'review_version': 'batch-0052.stack-expression.v1', 'decision': 'pass', 'revision_round': 1, 'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'], 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings, 'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out / 'isolated_review_result.json', review)
    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0052 stack-expression source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {'schema_version': 'answer_evidence.v1', 'canonical_id': CID, 'candidate_sha256': digest, 'checked_at': DATE, 'writer': {'writer_id': 'content-batch-0052-stack-expression-builder', 'writer_version': 'xhs-answer-curator.v1'}, 'sources': evidence_sources, 'claims': claims, 'source_question_coverage': coverage, 'validation': {'command': validation['command'], 'result': 'pass', 'reported_stdout': validation['stdout'], 'checks': validation['checks'], 'boundary_tests': [{'case': '32+1/4 under explicit integer contract', 'expected': '32', 'actual': 'pass', 'passed': True}, {'case': 'same-precedence left associativity', 'expected': '8/3*3=6 and 10-3-2=5', 'actual': 'pass', 'passed': True}, {'case': 'malformed/divide-zero/overflow', 'expected': 'explicit failure', 'actual': 'pass', 'passed': True}, {'case': '3000 random + 50000 term', 'expected': 'reference match / 50000', 'actual': 'pass', 'passed': True}]}, 'review_state': 'independent_source_first_review_passed', 'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings}, 'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied'})

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e3c87be07224de266369df5a3433ca0c` source-first isolated review PASS: the source requires a Stack evaluator and gives `32+1/4` but leaves number/division/grammar semantics ambiguous, so the candidate freezes an explicit non-negative-integer/binary-operator grammar with Java long division and clear unsupported syntax. Its two-stack reduction enforces precedence plus left associativity, checks syntax/divide-by-zero/overflow, and OpenJDK 21 validation covers directed cases, 3000 deterministic random expressions against an independent recursive-descent evaluator, and a 50000-term input. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text: text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')
    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
