'use strict';

const fs = require('fs');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const ROOT = path.resolve(__dirname, '..');
const SRC = path.join(ROOT, 'src');

function listJavaScriptFiles(dir) {
    if (!fs.existsSync(dir)) return [];
    const out = [];
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) out.push(...listJavaScriptFiles(fullPath));
        else if (entry.isFile() && entry.name.endsWith('.js')) out.push(fullPath);
    }
    return out.sort();
}

function relative(filePath) {
    return path.relative(ROOT, filePath).split(path.sep).join('/');
}

function source(filePath) {
    return fs.readFileSync(filePath, 'utf8');
}

function assertNoMatch(filePath, patterns) {
    const body = source(filePath);
    for (const [label, pattern] of patterns) {
        assert.doesNotMatch(body, pattern, `${relative(filePath)} must not depend on ${label}`);
    }
}

const DOMAIN_FORBIDDEN = [
    ['filesystem', /require\(['"](?:node:)?fs['"]\)|from\s+['"](?:node:)?fs['"]/],
    ['path', /require\(['"](?:node:)?path['"]\)|from\s+['"](?:node:)?path['"]/],
    ['child_process', /require\(['"](?:node:)?child_process['"]\)|from\s+['"](?:node:)?child_process['"]/],
    ['GitHub adapter', /(?:\.\.\/)+(?:infrastructure|interfaces)\/github|github[-_/]/i],
    ['AI infrastructure', /(?:\.\.\/)+infrastructure\/ai|openai|anthropic/i],
    ['database infrastructure', /(?:\.\.\/)+infrastructure\/(?:jsonl|sqlite)|sqlite3|better-sqlite/i],
    ['CLI/transport', /process\.argv|(?:\.\.\/)+interfaces\//],
];

const APPLICATION_FORBIDDEN = [
    ['filesystem', /require\(['"](?:node:)?fs['"]\)|from\s+['"](?:node:)?fs['"]/],
    ['concrete infrastructure', /(?:\.\.\/)+infrastructure\//],
    ['CLI argv', /process\.argv/],
];

test('Domain remains independent from infrastructure and transport concerns', () => {
    for (const filePath of listJavaScriptFiles(path.join(SRC, 'domain'))) {
        assertNoMatch(filePath, DOMAIN_FORBIDDEN);
    }
});

test('Application depends on ports/domain rather than concrete infrastructure', () => {
    for (const filePath of listJavaScriptFiles(path.join(SRC, 'application'))) {
        assertNoMatch(filePath, APPLICATION_FORBIDDEN);
    }
});

test('Composition Root exists before the first migrated vertical slice', () => {
    const bootstrap = require('../src/bootstrap/create-application');
    const app = bootstrap.createApplication();
    assert.equal(Object.isFrozen(app), true);
    assert.deepEqual(Object.keys(app), []);
});
