from pathlib import Path

p = Path('scripts/lib/answer_quality.js')
s = p.read_text(encoding='utf-8')

old = r"const regex = /(?:```|~~~)(java|sql|javascript|js|go|c|cpp|c\+\+|cc|cxx)\s*\n([\s\S]*?)\n(?:```|~~~)/gi;"
new = r"const regex = /(?:```|~~~)(java|sql|javascript|js|go|c|cpp|c\+\+|cc|cxx|bash|sh|shell)\s*\n([\s\S]*?)\n(?:```|~~~)/gi;"
if old not in s:
    raise SystemExit('extractCodeBlocks pattern drifted')
s = s.replace(old, new, 1)

anchor = '\nfunction compileGo(code) {'
shell_fn = r'''
function validateShell(code) {
    const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-shell-'));
    try {
        const filePath = path.join(tempDir, 'candidate.sh');
        fs.writeFileSync(filePath, code, 'utf8');
        const result = childProcess.spawnSync('bash', ['-n', filePath], {
            encoding: 'utf8',
            timeout: 10000,
        });
        if (result.error?.code === 'ENOENT') return { ok: false, error: 'bash_not_available' };
        if (result.error) return { ok: false, error: 'shell_parse_failed', detail: result.error.message };
        if (result.status !== 0) {
            return {
                ok: false,
                error: 'shell_parse_failed',
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
s = s.replace(anchor, '\n' + shell_fn + anchor, 1)

go_old = """        const result = childProcess.spawnSync('go', ['test', filePath], {
            encoding: 'utf8',
            timeout: 10000,
        });"""
go_new = """        const result = childProcess.spawnSync('go', ['test', filePath], {
            encoding: 'utf8',
            timeout: 30000,
        });"""
if go_old not in s:
    raise SystemExit('compileGo timeout block drifted')
s = s.replace(go_old, go_new, 1)

old_dispatch = """                        : ['cpp', 'c++', 'cc', 'cxx'].includes(block.language)
                                ? compileCpp(block.code)
                                : parseJavaScript(block.code);"""
new_dispatch = """                        : ['cpp', 'c++', 'cc', 'cxx'].includes(block.language)
                                ? compileCpp(block.code)
                                : ['bash', 'sh', 'shell'].includes(block.language)
                                    ? validateShell(block.code)
                                    : parseJavaScript(block.code);"""
if old_dispatch not in s:
    raise SystemExit('coding dispatch drifted')
s = s.replace(old_dispatch, new_dispatch, 1)

old_export = '    compileCpp,\n    parseSql,'
new_export = '    compileCpp,\n    validateShell,\n    parseSql,'
if old_export not in s:
    raise SystemExit('module export anchor drifted')
s = s.replace(old_export, new_export, 1)
p.write_text(s, encoding='utf-8')

t = Path('test/answer_code_validation.test.js')
x = t.read_text(encoding='utf-8')
old_import = "const { compileJava, compileC, compileCpp, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');"
new_import = "const { compileJava, compileC, compileCpp, validateShell, parseSql, validateSpecializedCandidate } = require('../scripts/lib/answer_quality');"
if old_import not in x:
    raise SystemExit('test import drifted')
x = x.replace(old_import, new_import, 1)
marker = "\ntest('SQL validation checks statement structure balance and placeholders', () => {"
shell_test = r'''

test('shell validation accepts bash/sh fences and rejects malformed scripts', () => {
    assert.equal(validateShell("set -euo pipefail\nprintf '%s\\n' ok").ok, true);
    assert.equal(validateShell('if true; then\n  echo ok').ok, false);
    const context = { canonical: { canonical_title: 'Linux URL 计数' }, primary_entities: ['awk', 'sort', 'uniq'], source_variants: ['统计 URL 次数'] };
    const evidence = { validation: { boundary_tests: [
        { case: 'non-adjacent duplicates', expected: '3/2/1', passed: true },
        { case: 'blank line', expected: 'ignored', passed: true },
        { case: 'query variants', expected: 'distinct', passed: true },
    ] } };
    for (const language of ['bash', 'sh', 'shell']) {
        const fence = '```' + language;
        const candidate = { metadata: { answer_type: 'coding' }, content: [
            '## 核心结论', 'awk、sort、uniq 组成 URL 计数流水线。',
            '## 常见追问', '- 问：为何 sort？答：让重复行相邻。', '- 问：空行？答：过滤。', '- 问：query？答：按契约处理。',
            '## 3 分钟版', fence, "awk 'NF {print $0}' urls.txt | sort | uniq -c", '```',
        ].join('\n') };
        const result = validateSpecializedCandidate(candidate, evidence, context);
        assert.equal(result.errors.some((row) => row.error === 'coding_block_required'), false, language);
        assert.equal(result.errors.some((row) => row.error.endsWith('_validation_failed')), false, language);
    }
});
'''
if marker not in x:
    raise SystemExit('test insertion marker drifted')
x = x.replace(marker, shell_test + marker, 1)
t.write_text(x, encoding='utf-8')
