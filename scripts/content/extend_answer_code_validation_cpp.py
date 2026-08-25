#!/usr/bin/env python3
"""Extend answer-quality coding validation to source-appropriate C++ snippets.

Idempotent bounded migration helper. It updates only the answer validator and its
regression test. The active content branch already supports Java, SQL,
JavaScript, Go and C; this migration adds C++ fence aliases and g++ compilation.
"""

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    if new in text:
        return text
    raise SystemExit(f"{label} drifted")


def main() -> int:
    quality_path = Path("scripts/lib/answer_quality.js")
    source = quality_path.read_text(encoding="utf-8")

    source = replace_once(
        source,
        "const regex = /(?:```|~~~)(java|sql|javascript|js|go|c)\\s*\\n([\\s\\S]*?)\\n(?:```|~~~)/gi;",
        "const regex = /(?:```|~~~)(java|sql|javascript|js|go|c|cpp|c\\+\\+|cc|cxx)\\s*\\n([\\s\\S]*?)\\n(?:```|~~~)/gi;",
        "extractCodeBlocks language regex",
    )

    compile_cpp = """function compileCpp(code) {
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-gpp-'));
    try {
        const filePath = path.join(tempDir, 'candidate.cpp');
        const objectPath = path.join(tempDir, 'candidate.o');
        fs.writeFileSync(filePath, code, 'utf8');
        const result = childProcess.spawnSync('g++', ['-std=c++17', '-Wall', '-Wextra', '-Werror', '-pedantic', '-c', filePath, '-o', objectPath], {
            encoding: 'utf8',
            timeout: 15000,
        });
        if (result.error?.code === 'ENOENT') return { ok: false, error: 'g++_not_available' };
        if (result.error) return { ok: false, error: 'cpp_compile_failed', detail: result.error.message };
        if (result.status !== 0) {
            return {
                ok: false,
                error: 'cpp_compile_failed',
                detail: String(result.stderr || result.stdout || '').trim().slice(0, 2000),
            };
        }
        return { ok: true };
    } finally {
        fs.rmSync(tempDir, { recursive: true, force: true });
    }
}

"""
    marker = "function parseJavaScript(code) {"
    if "function compileCpp(code) {" not in source:
        if marker not in source:
            raise SystemExit("parseJavaScript marker drifted")
        source = source.replace(marker, compile_cpp + marker, 1)

    source = replace_once(
        source,
        """                    : block.language === 'c'
                            ? compileC(block.code)
                            : parseJavaScript(block.code);""",
        """                    : block.language === 'c'
                            ? compileC(block.code)
                            : ['cpp', 'c++', 'cc', 'cxx'].includes(block.language)
                                ? compileCpp(block.code)
                                : parseJavaScript(block.code);""",
        "specialized validation dispatch",
    )

    source = replace_once(
        source,
        "/(?:```|~~~)(?:java|sql|javascript|js|go|c)\\b/i.test(answer.content)",
        "/(?:```|~~~)(?:java|sql|javascript|js|go|c|cpp|c\\+\\+|cc|cxx)(?:\\s|$)/i.test(answer.content)",
        "require-code language regex",
    )

    source = replace_once(
        source,
        "    compileJava,\n    compileC,\n    parseSql,",
        "    compileJava,\n    compileC,\n    compileCpp,\n    parseSql,",
        "module export",
    )
    quality_path.write_text(source, encoding="utf-8")

    test_path = Path("test/answer_code_validation.test.js")
    tests = test_path.read_text(encoding="utf-8")
    tests = replace_once(
        tests,
        "const { compileJava, compileC, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');",
        "const { compileJava, compileC, compileCpp, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');",
        "test import",
    )
    cpp_test = """

test('C++ validation compiles common fence aliases and rejects broken implementations', () => {
    assert.equal(compileCpp('#include <vector>\\nint size(const std::vector<int>& values) { return static_cast<int>(values.size()); }').ok, true);
    assert.equal(compileCpp('int add(int a, int b) { return a + ; }').ok, false);
    const context = { canonical: { canonical_title: '链表中点' }, primary_entities: ['链表'], source_variants: ['链表中点'] };
    const evidence = { validation: { boundary_tests: [
        { case: 'empty', expected: 'nullptr', passed: true },
        { case: 'odd', expected: 'middle', passed: true },
        { case: 'even', expected: 'second middle', passed: true },
    ] } };
    for (const language of ['cpp', 'c++', 'cc', 'cxx']) {
        const candidate = { metadata: { answer_type: 'coding' }, content: [
            '## 核心结论', '链表中点用快慢指针。',
            '## 常见追问', '- 问：空链表？答：空。', '- 问：奇数？答：唯一中点。', '- 问：偶数？答：契约决定。',
            '## 3 分钟版', `\\`\\`\\`${language}`, 'struct Node { int v; Node* next; };', 'Node* middle(Node* h) { Node* s=h; Node* f=h; while (f && f->next) { s=s->next; f=f->next->next; } return s; }', '\\`\\`\\`',
        ].join('\\n') };
        const result = validateSpecializedCandidate(candidate, evidence, context);
        assert.equal(result.errors.some((row) => row.error === 'coding_block_required'), false, language);
        assert.equal(result.errors.some((row) => row.error.endsWith('_validation_failed')), false, language);
    }
});
"""
    if "test('C++ validation compiles common fence aliases" not in tests:
        anchor = "\ntest('SQL validation checks statement structure balance and placeholders', () => {"
        if anchor not in tests:
            raise SystemExit("test insertion anchor drifted")
        tests = tests.replace(anchor, cpp_test + anchor, 1)
    test_path.write_text(tests, encoding="utf-8")

    print("C++ answer validation support applied or already present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
