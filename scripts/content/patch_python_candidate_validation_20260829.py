from pathlib import Path

p = Path('scripts/lib/answer_quality.js')
s = p.read_text(encoding='utf-8')
old = r"const regex = /(?:```|~~~)(java|sql|javascript|js|go|c|cpp|c\+\+|cc|cxx|bash|sh|shell)\s*\n([\s\S]*?)\n(?:```|~~~)/gi;"
new = r"const regex = /(?:```|~~~)(java|sql|javascript|js|go|c|cpp|c\+\+|cc|cxx|bash|sh|shell|python|py)\s*\n([\s\S]*?)\n(?:```|~~~)/gi;"
if old not in s:
    raise SystemExit('extractCodeBlocks language list drifted')
s = s.replace(old, new, 1)

anchor = '\nfunction compileGo(code) {'
python_fn = r'''
function validatePython(code) {
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-python-'));
    try {
        const filePath = path.join(tempDir, 'candidate.py');
        fs.writeFileSync(filePath, code, 'utf8');
        const result = childProcess.spawnSync('python3', ['-m', 'py_compile', filePath], {
            encoding: 'utf8',
            timeout: 10000,
        });
        if (result.error?.code === 'ENOENT') return { ok: false, error: 'python3_not_available' };
        if (result.error) return { ok: false, error: 'python_parse_failed', detail: result.error.message };
        if (result.status !== 0) {
            return {
                ok: false,
                error: 'python_parse_failed',
                detail: String(result.stderr || result.stdout || '').trim().slice(0, 1200),
            };
        }
        return { ok: true };
    } finally {
        fs.rmSync(tempDir, { recursive: true, force: true });
    }
}
'''
if anchor not in s:
    raise SystemExit('compileGo anchor drifted')
s = s.replace(anchor, '\n' + python_fn + anchor, 1)

old_dispatch = """                                : ['bash', 'sh', 'shell'].includes(block.language)
                                    ? validateShell(block.code)
                                    : parseJavaScript(block.code);"""
new_dispatch = """                                : ['bash', 'sh', 'shell'].includes(block.language)
                                    ? validateShell(block.code)
                                    : ['python', 'py'].includes(block.language)
                                        ? validatePython(block.code)
                                        : parseJavaScript(block.code);"""
if old_dispatch not in s:
    raise SystemExit('coding dispatch drifted')
s = s.replace(old_dispatch, new_dispatch, 1)

old_export = '    validateShell,\n    compileGo,'
new_export = '    validateShell,\n    validatePython,\n    compileGo,'
if old_export not in s:
    raise SystemExit('module export anchor drifted')
s = s.replace(old_export, new_export, 1)
p.write_text(s, encoding='utf-8')

t = Path('test/answer_code_validation.test.js')
x = t.read_text(encoding='utf-8')
old_import = "const { compileJava, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');"
new_import = "const { compileJava, validatePython, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');"
if old_import not in x:
    raise SystemExit('test import drifted')
x = x.replace(old_import, new_import, 1)
marker = "\ntest('SQL validation checks statement structure balance and placeholders', () => {"
python_test = r'''

test('Python validation recognizes python/py fences and rejects syntax errors', () => {
    assert.equal(validatePython('def add(a, b):\n    return a + b').ok, true);
    assert.equal(validatePython('def broken(:\n    pass').ok, false);
    const context = { canonical: { canonical_title: 'Python 字典构造' }, primary_entities: ['python dict'], source_variants: ['在Python中建立字典对象有哪些方法？'] };
    const evidence = { validation: { boundary_tests: [
        { case: 'literal', expected: 'dict', passed: true },
        { case: 'fromkeys mutable value', expected: 'shared', passed: true },
        { case: 'comprehension mutable value', expected: 'independent', passed: true },
    ] } };
    for (const language of ['python', 'py']) {
        const candidate = { metadata: { answer_type: 'coding' }, content: [
            '## 核心结论', 'Python dict 可以通过字面量、dict 构造器和推导式建立。',
            '## 常见追问', '- 问：fromkeys？答：可共享同一 value。', '- 问：独立 list？答：用推导式。', '- 问：关键字？答：生成字符串键。',
            '## 3 分钟版', '```' + language, 'def build():\n    return {"a": 1}', '```',
        ].join('\n') };
        const result = validateSpecializedCandidate(candidate, evidence, context);
        assert.equal(result.errors.some((row) => row.error === 'coding_block_required'), false, language);
        assert.equal(result.errors.some((row) => row.error.endsWith('_validation_failed')), false, language);
    }
});
'''
if marker not in x:
    raise SystemExit('test insertion marker drifted')
x = x.replace(marker, python_test + marker, 1)
t.write_text(x, encoding='utf-8')
