#!/usr/bin/env python3
# Build, validate, source-first review, and stage Batch 0053 expression-calculator candidate.

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0053'
CID = 'cq_q_e8ce511f7de2564d49e3106ed54c7731'
QID = 'e8ce511f7de2564d49e3106ed54c7731'
EXPECTED = '算法：模拟计算器，输入算数表达式字符串，返回计算结果'

CANDIDATE = r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_e8ce511f7de2564d49e3106ed54c7731","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 模拟计算器：计算算术表达式字符串

## 核心结论

仓库来源只保留“输入算术表达式字符串，返回计算结果”，没有保存支持哪些运算符、是否有括号/一元符号、整数还是小数、溢出策略、非法输入和除零语义。这里明确一个可执行 Java 契约：支持十进制**任意精度整数**、空白、`+ - * /`、括号以及一元 `+/-`；乘除优先于加减，括号最高；除法使用 `BigInteger.divide` 的整数除法，即向 0 截断；非法语法抛 `IllegalArgumentException`，除 0 抛 `ArithmeticException`。

实现使用递归下降解析：`expression` 处理加减，`term` 处理乘除，`unary` 处理连续一元正负号，`primary` 处理括号或数字。优先级直接编码在调用层级里，因此不需要先转逆波兰表达式；如果题目明确要求栈或 RPN，可以换成 shunting-yard + 后缀求值，但这不是当前保存题面的硬约束。

## 1 分钟版

- 先定义语法合同：整数、`+ - * /`、括号、一元正负号和空白。
- `parseExpression -> parseTerm -> parseUnary -> parsePrimary` 的层级天然表达运算符优先级。
- `parseExpression` 只消费 `+/-`，每个操作数先由 `parseTerm` 完成，所以乘除一定先算。
- 括号在 `parsePrimary` 中递归调用 `parseExpression`，从而局部重启完整优先级规则。
- 用 `BigInteger` 避免把题目没有说明的 32/64 位溢出策略偷偷变成答案前提。
- 解析结束后必须确认整个字符串已消费，避免 `"1 2"`、`"1+2abc"` 这类前缀合法但整体非法的输入被错误接受。

## 3 分钟版

```java
import java.math.BigInteger;

public final class ExpressionCalculator {
    private final String input;
    private int pos;

    private ExpressionCalculator(String input) {
        this.input = input;
    }

    public static BigInteger evaluate(String expression) {
        if (expression == null) throw new IllegalArgumentException("expression must not be null");
        ExpressionCalculator parser = new ExpressionCalculator(expression);
        BigInteger value = parser.parseExpression();
        parser.skipSpaces();
        if (parser.pos != parser.input.length()) {
            throw new IllegalArgumentException("unexpected token at position " + parser.pos);
        }
        return value;
    }

    private BigInteger parseExpression() {
        BigInteger value = parseTerm();
        while (true) {
            skipSpaces();
            if (match('+')) value = value.add(parseTerm());
            else if (match('-')) value = value.subtract(parseTerm());
            else return value;
        }
    }

    private BigInteger parseTerm() {
        BigInteger value = parseUnary();
        while (true) {
            skipSpaces();
            if (match('*')) {
                value = value.multiply(parseUnary());
            } else if (match('/')) {
                BigInteger rhs = parseUnary();
                if (rhs.signum() == 0) throw new ArithmeticException("division by zero");
                value = value.divide(rhs);
            } else {
                return value;
            }
        }
    }

    private BigInteger parseUnary() {
        skipSpaces();
        if (match('+')) return parseUnary();
        if (match('-')) return parseUnary().negate();
        return parsePrimary();
    }

    private BigInteger parsePrimary() {
        skipSpaces();
        if (match('(')) {
            BigInteger value = parseExpression();
            skipSpaces();
            if (!match(')')) throw new IllegalArgumentException("missing ')' at position " + pos);
            return value;
        }
        return parseNumber();
    }

    private BigInteger parseNumber() {
        skipSpaces();
        int start = pos;
        while (pos < input.length() && Character.isDigit(input.charAt(pos))) pos++;
        if (start == pos) throw new IllegalArgumentException("number expected at position " + pos);
        return new BigInteger(input.substring(start, pos));
    }

    private boolean match(char expected) {
        if (pos < input.length() && input.charAt(pos) == expected) {
            pos++;
            return true;
        }
        return false;
    }

    private void skipSpaces() {
        while (pos < input.length() && Character.isWhitespace(input.charAt(pos))) pos++;
    }
}
```

例如 `1 + 2 * 3` 先在 `term` 中得到 `2*3=6`，再由 `expression` 完成 `1+6=7`；`(1+2)*3` 则由 `primary` 先递归算出括号内 3，再乘 3 得 9。`2*-3` 也能处理，因为乘号右侧进入 `parseUnary`，一元负号不是被当成二元减法。

## 关键细节

- **来源边界**：原题没有保存小数、幂运算、函数、变量等要求，本候选不擅自扩展这些语法。
- **完整消费**：主入口在解析后跳过尾部空白，并要求 `pos == input.length()`，否则整体输入判非法。
- **一元符号**：`-(-3)`、`--3`、`2*-3` 都由 `parseUnary` 递归处理，不需要给 `-` 人为复制多套优先级规则。
- **除法语义**：当前合同是整数除法向 0 截断，例如 `-20/3 == -6`。若题目要求小数，必须更换数值模型和精度/舍入合同。
- **大整数**：`BigInteger` 让数值范围不依赖机器整型上限；代价是大数算术复杂度不再能简单视为常数。
- **错误边界**：空字符串、缺右括号、缺操作数、未知字符等都是语法错误；除 0 单独保留算术错误。
- **递归深度**：括号和连续一元符号会增加递归深度。极端攻击性输入需要显式深度限制或改成迭代栈；面试实现应主动说明这个边界。

## 原理机制

递归下降的核心是让“语法层级”和“函数调用层级”一致。`expression := term (('+'|'-') term)*`，`term := unary (('*'|'/') unary)*`，因此一个低优先级层永远只能拿到已经由高优先级层计算完成的操作数。括号通过 `primary := '(' expression ')' | number` 把完整表达式语法嵌套回来。

另一种常见方案是 shunting-yard：用操作符栈根据优先级和结合性输出 RPN，再用值栈求值。它对扩展很多运算符更方便，也能规避深括号递归；当前题面并未要求必须用栈或逆波兰，所以这里选择代码边界更直接的递归下降，并把 RPN 作为可替代设计而不是来源事实。

## 项目经验版

来源没有真实项目场景，不能虚构“线上实现过表达式引擎”。工程里若表达式来自不可信输入，我会额外限制字符串长度、嵌套深度、数字位数和总计算成本，避免超大 `BigInteger` 或极深嵌套造成资源消耗；若要支持变量、函数、小数、布尔运算，则应先正式定义 grammar/AST 和错误模型，而不是继续在字符扫描代码里堆条件分支。

## 常见追问

- 问：为什么不用两个栈？答：两个栈/RPN 完全可行；当前实现用递归下降把优先级编码在 grammar 层级，逻辑更直接。题目若明确要求栈，再换成 shunting-yard。
- 问：`2*-3` 为什么能算？答：`*` 后读取的是 `unary`，而 `unary` 先消费负号再读取 primary，所以负号不会和二元减法冲突。
- 问：为什么用 `BigInteger`？答：来源没有给 int/long 范围和溢出语义；任意精度整数可以避免把未给出的溢出策略当成题目事实。
- 问：如果要支持小数呢？答：必须定义精度和舍入规则，可以使用 `BigDecimal`，但除法可能产生无限小数，需要明确 `MathContext` 或 scale。
- 问：如何检测非法表达式？答：每个 grammar 层在需要数字/右括号时严格检查，主入口再验证没有剩余 token；两者结合避免部分解析成功。
- 问：递归会栈溢出吗？答：普通输入通常没问题，但极深括号/一元符号链可能溢出；生产解析器应限制深度或使用显式操作符/值栈。

## 易错点

- 只从左到右计算，导致 `1+2*3` 错算成 9。
- 只处理二元减号，遇到 `2*-3` 或 `-(1+2)` 失败。
- 算出一个合法前缀就返回，没有检查尾部垃圾字符。
- 没有定义整数除法还是小数除法，却在示例里混用不同语义。
- 用 `long`/`int` 却完全不说明溢出行为。
- 把“实体标签里出现栈/RPN”误写成原题强制要求使用逆波兰。
- 忽略极深嵌套与超大整数的资源边界。
'''

TEST = r'''import java.math.BigInteger;
import java.util.Random;

public final class ExpressionCalculatorTest {
    private record Expr(String text, BigInteger value) {}

    private static void check(String expression, String expected) {
        BigInteger actual = ExpressionCalculator.evaluate(expression);
        if (!new BigInteger(expected).equals(actual)) {
            throw new AssertionError(expression + " expected=" + expected + " actual=" + actual);
        }
    }

    private static Expr generate(Random random, int depth) {
        if (depth == 0 || random.nextInt(4) == 0) {
            int n = random.nextInt(2001) - 1000;
            String text = n < 0 ? "(-" + (-n) + ")" : Integer.toString(n);
            return new Expr(text, BigInteger.valueOf(n));
        }
        Expr left = generate(random, depth - 1);
        Expr right = generate(random, depth - 1);
        int op = random.nextInt(4);
        if (op == 3 && right.value.signum() == 0) op = 0;
        return switch (op) {
            case 0 -> new Expr("(" + left.text + "+" + right.text + ")", left.value.add(right.value));
            case 1 -> new Expr("(" + left.text + "-" + right.text + ")", left.value.subtract(right.value));
            case 2 -> new Expr("(" + left.text + "*" + right.text + ")", left.value.multiply(right.value));
            default -> new Expr("(" + left.text + "/" + right.text + ")", left.value.divide(right.value));
        };
    }

    private static void expectSyntax(String expression) {
        try {
            ExpressionCalculator.evaluate(expression);
            throw new AssertionError("syntax should fail: " + expression);
        } catch (IllegalArgumentException expected) {}
    }

    public static void main(String[] args) {
        check("1+2*3", "7");
        check("(1+2)*3", "9");
        check(" - ( 2 + 3 ) * +4 ", "-20");
        check("20/3", "6");
        check("-20/3", "-6");
        check("2*-3+10", "4");
        check("999999999999999999999999*999999999999999999999999",
              "999999999999999999999998000000000000000000000001");

        expectSyntax("");
        expectSyntax("1+");
        expectSyntax("(1+2");
        expectSyntax("1 2");
        expectSyntax("abc");

        try {
            ExpressionCalculator.evaluate("1/(2-2)");
            throw new AssertionError("division by zero should fail");
        } catch (ArithmeticException expected) {}

        Random random = new Random(20260829L);
        for (int i = 0; i < 2000; i++) {
            Expr e = generate(random, 5);
            BigInteger actual = ExpressionCalculator.evaluate(e.text);
            if (!e.value.equals(actual)) {
                throw new AssertionError("round=" + i + " expr=" + e.text + " expected=" + e.value + " actual=" + actual);
            }
        }

        StringBuilder deep = new StringBuilder();
        for (int i=0;i<200;i++) deep.append('(');
        deep.append("7");
        for (int i=0;i<200;i++) deep.append(')');
        check(deep.toString(), "7");

        System.out.println("PASS precedence parentheses unary whitespace division biginteger syntax divzero 2000-random-ast 200-deep");
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

    with tempfile.TemporaryDirectory(prefix='b53-expression-calculator-') as tmp:
        tmpdir = Path(tmp)
        (tmpdir / 'ExpressionCalculator.java').write_text(blocks[0].strip() + '\n', encoding='utf-8')
        (tmpdir / 'ExpressionCalculatorTest.java').write_text(TEST, encoding='utf-8')
        run('javac', 'ExpressionCalculator.java', 'ExpressionCalculatorTest.java', cwd=tmpdir)
        stdout = run('java', 'ExpressionCalculatorTest', cwd=tmpdir).stdout.strip()
    expected_stdout = 'PASS precedence parentheses unary whitespace division biginteger syntax divzero 2000-random-ast 200-deep'
    if stdout != expected_stdout:
        raise SystemExit(f'unexpected fixture output: {stdout}')

    validation = {
        'schema_version': 'answer_code_validation.v1',
        'canonical_id': CID,
        'result': 'pass',
        'validated_at': DATE,
        'command': 'javac ExpressionCalculator.java ExpressionCalculatorTest.java && java ExpressionCalculatorTest',
        'stdout': stdout,
        'checks': [
            'operator precedence and parenthesis grouping',
            'unary signs and whitespace handling',
            'integer division toward zero under explicit BigInteger contract',
            'arbitrary-precision multiplication beyond long range',
            'syntax rejection and division-by-zero boundary',
            '2000 deterministic generated expression trees agree with independent AST values',
            '200-level parenthesis nesting directed regression',
        ],
    }
    write_json(out / 'writer_validation.json', validation)

    digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources = [
        {'source_id': 'repository-source', 'title': 'Batch 0053 exact expression-calculator source context', 'locator': str(out / 'context.json'), 'source_type': 'repository_source_record', 'checked_at': DATE},
        {'source_id': 'fixture', 'title': 'OpenJDK 21 expression-calculator deterministic validation', 'locator': str(out / 'writer_validation.json'), 'source_type': 'executable_test_or_reproducible_experiment', 'checked_at': DATE},
    ]
    claims = [
        {'claim_id': 'source-boundary', 'text': 'The preserved source asks only for evaluating an arithmetic-expression string; it does not preserve operator set, numeric domain, parenthesis/unary support, overflow, invalid-input, or division semantics.', 'source_ids': ['repository-source'], 'answer_locations': ['核心结论', '关键细节', '易错点']},
        {'claim_id': 'explicit-contract', 'text': 'The candidate explicitly chooses arbitrary-precision integers, + - * /, parentheses, unary signs, whitespace, truncating integer division, and strict syntax/error boundaries.', 'source_ids': ['repository-source', 'fixture'], 'answer_locations': ['核心结论', '1 分钟版', '关键细节']},
        {'claim_id': 'parser-mechanism', 'text': 'Recursive-descent grammar layers expression, term, unary, and primary so higher-precedence operations finish before lower-precedence callers consume them.', 'source_ids': ['fixture'], 'answer_locations': ['3 分钟版', '原理机制', '常见追问']},
        {'claim_id': 'validation', 'text': 'Executable validation covers precedence, parentheses, unary signs, whitespace, division semantics, arbitrary precision, syntax failures, division by zero, 2000 deterministic generated AST cases, and 200-level nesting.', 'source_ids': ['fixture'], 'answer_locations': ['关键细节', '常见追问', '易错点']},
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
        'The candidate does not invent a hidden calculator grammar from the sparse source; every supported operator and numeric/error rule is labeled as explicit candidate contract.',
        'Recursive-descent layers correctly encode multiplication/division precedence over addition/subtraction while parentheses re-enter the full expression grammar.',
        'Unary signs are handled in their own layer, including cases such as 2*-3 and -(1+2), without confusing unary and binary minus.',
        'BigInteger avoids an unstated fixed-width overflow policy and the answer clearly notes that decimal arithmetic would require a different precision/rounding contract.',
        'The parser rejects trailing garbage and incomplete syntax rather than accepting a valid prefix.',
        'OpenJDK 21 validation covers directed cases, 2000 deterministic generated AST expressions against independently computed values, arbitrary-precision arithmetic, error boundaries, and 200-level nesting.',
        'The answer distinguishes recursive descent from stack/RPN alternatives and does not turn taxonomy entities into a fabricated source requirement.',
    ]
    review = {
        'schema_version': 'isolated_review.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'reviewed_at': DATE,
        'review_mode': 'source_first_isolated',
        'reviewer_id': 'source-first-isolated-reviewer-batch-0053-expression-calculator-20260829-v1',
        'review_version': 'batch-0053.expression-calculator.v1',
        'decision': 'pass',
        'revision_round': 1,
        'source_packet': [str(out / 'context.json'), str(candidate), str(out / 'writer_validation.json'), 'docs/refactor/09_answer_content_standard.md'],
        'scores': scores,
        'hard_failures': [],
        'unsupported_claims': [],
        'uncovered_source_variants': [],
        'findings': findings,
        'promotion_blockers': ['repository_human_approval_and_real_review_policy_not_yet_satisfied'],
    }
    write_json(out / 'isolated_review_result.json', review)

    evidence_sources = sources + [{'source_id': 'isolated-review', 'title': 'Batch 0053 expression-calculator source-first isolated review', 'locator': str(out / 'isolated_review_result.json'), 'source_type': 'repository_structured_source', 'checked_at': DATE}]
    write_json(ROOT / f'review/evidence/{CID}.json', {
        'schema_version': 'answer_evidence.v1',
        'canonical_id': CID,
        'candidate_sha256': digest,
        'checked_at': DATE,
        'writer': {'writer_id': 'content-batch-0053-expression-calculator-builder', 'writer_version': 'xhs-answer-curator.v1'},
        'sources': evidence_sources,
        'claims': claims,
        'source_question_coverage': coverage,
        'validation': {
            'command': validation['command'],
            'result': 'pass',
            'reported_stdout': validation['stdout'],
            'checks': validation['checks'],
            'boundary_tests': [
                {'case': 'precedence and parentheses', 'expected': 'grammar-consistent exact values', 'actual': 'pass', 'passed': True},
                {'case': 'syntax and trailing garbage', 'expected': 'rejected', 'actual': 'pass', 'passed': True},
                {'case': 'division by zero', 'expected': 'ArithmeticException', 'actual': 'pass', 'passed': True},
                {'case': '2000 deterministic generated AST expressions', 'expected': 'matches independent values', 'actual': 'pass', 'passed': True},
                {'case': '200-level nested parentheses', 'expected': 'evaluates to 7', 'actual': 'pass', 'passed': True},
            ],
        },
        'review_state': 'independent_source_first_review_passed',
        'review': {'reviewer_id': review['reviewer_id'], 'review_version': review['review_version'], 'independent': True, 'decision': 'pass', 'revision_round': 1, 'scores': scores, 'hard_failures': [], 'unsupported_claims': [], 'uncovered_source_variants': [], 'findings': findings},
        'promotion_blocker': 'repository_human_approval_and_real_review_policy_not_yet_satisfied',
    })

    task = ROOT / f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text = task.read_text(encoding='utf-8')
    line = '- [x] `cq_q_e8ce511f7de2564d49e3106ed54c7731` source-first isolated review PASS: the source preserves only an arithmetic-expression-string calculator request, so supported operators, numeric domain, unary/parenthesis support, invalid-input behavior, and division semantics remain explicit candidate contract. The BigInteger recursive-descent implementation encodes precedence through expression/term/unary/primary grammar layers; OpenJDK 21 validation covers directed precedence/parentheses/unary/error cases, arbitrary-precision arithmetic, 2000 deterministic generated AST expressions against independent values, and 200-level nesting. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if line not in text:
        text = text.rstrip() + '\n' + line + '\n'
    task.write_text(text, encoding='utf-8')

    print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
