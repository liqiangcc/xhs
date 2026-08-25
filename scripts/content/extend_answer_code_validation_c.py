#!/usr/bin/env python3
"""Extend answer-quality coding validation to source-appropriate C snippets.

Idempotent migration helper used by the bounded GitHub Actions workflow. It updates
only the validator, its regression test, and the coding requirement label.
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
        "const regex = /(?:```|~~~)(java|sql|javascript|js|go)\\s*\\n([\\s\\S]*?)\\n(?:```|~~~)/gi;",
        "const regex = /(?:```|~~~)(java|sql|javascript|js|go|c)\\s*\\n([\\s\\S]*?)\\n(?:```|~~~)/gi;",
        "extractCodeBlocks language regex",
    )

    compile_c = """function compileC(code) {
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-gcc-'));
    try {
        const filePath = path.join(tempDir, 'candidate.c');
        const objectPath = path.join(tempDir, 'candidate.o');
        fs.writeFileSync(filePath, code, 'utf8');
        const result = childProcess.spawnSync('gcc', ['-std=c17', '-Wall', '-Wextra', '-Werror', '-pedantic', '-c', filePath, '-o', objectPath], {
            encoding: 'utf8',
            timeout: 15000,
        });
        if (result.error?.code === 'ENOENT') return { ok: false, error: 'gcc_not_available' };
        if (result.error) return { ok: false, error: 'c_compile_failed', detail: result.error.message };
        if (result.status !== 0) {
            return {
                ok: false,
                error: 'c_compile_failed',
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
    if "function compileC(code) {" not in source:
        if marker not in source:
            raise SystemExit("parseJavaScript marker drifted")
        source = source.replace(marker, compile_c + marker, 1)

    source = replace_once(
        source,
        """            const validation = block.language === 'java'
                ? compileJava(block.code)
                : block.language === 'sql'
                    ? parseSql(block.code)
                    : block.language === 'go'
                        ? compileGo(block.code)
                        : parseJavaScript(block.code);""",
        """            const validation = block.language === 'java'
                ? compileJava(block.code)
                : block.language === 'sql'
                    ? parseSql(block.code)
                    : block.language === 'go'
                        ? compileGo(block.code)
                        : block.language === 'c'
                            ? compileC(block.code)
                            : parseJavaScript(block.code);""",
        "specialized validation dispatch",
    )

    source = replace_once(
        source,
        "/(?:```|~~~)(?:java|sql|javascript|js|go)\\b/i.test(answer.content)",
        "/(?:```|~~~)(?:java|sql|javascript|js|go|c)\\b/i.test(answer.content)",
        "require-code language regex",
    )

    source = replace_once(
        source,
        "    compileJava,\n    parseSql,",
        "    compileJava,\n    compileC,\n    parseSql,",
        "module export",
    )
    quality_path.write_text(source, encoding="utf-8")

    test_path = Path("test/answer_code_validation.test.js")
    tests = test_path.read_text(encoding="utf-8")
    tests = replace_once(
        tests,
        "const { compileJava, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');",
        "const { compileJava, compileC, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');",
        "test import",
    )
    c_test = """

test('C validation compiles complete source and rejects broken implementations', () => {
    assert.equal(compileC('#include <stddef.h>\\nchar *copy(char *dst, const char *src) { char *out = dst; while ((*dst++ = *src++) != \\'\\0\\') {} return out; }').ok, true);
    assert.equal(compileC('char *copy(char *dst, const char *src) { return dst + ; }').ok, false);
});
"""
    if "test('C validation compiles complete source" not in tests:
        anchor = "\ntest('SQL validation checks statement structure balance and placeholders', () => {"
        if anchor not in tests:
            raise SystemExit("test insertion anchor drifted")
        tests = tests.replace(anchor, c_test + anchor, 1)
    test_path.write_text(tests, encoding="utf-8")

    config_path = Path("config/answer_quality.json")
    config = config_path.read_text(encoding="utf-8")
    config = replace_once(
        config,
        "runnable_java_or_sql",
        "runnable_source_appropriate_code_or_sql",
        "answer quality coding requirement",
    )
    config_path.write_text(config, encoding="utf-8")

    print("C answer validation support applied or already present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
