'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');
const { writeJsonl } = require('../scripts/lib/io');
const { createApplication } = require('../src/bootstrap/create-application');
const { createCanonicalFsPaths } = require('../src/infrastructure/filesystem/canonical-paths');

test('production canonical check writes the report only when requested', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-canonical-check-fs-'));
    try {
        const paths = createCanonicalFsPaths(root);
        writeJsonl(paths.canonicalQuestions, []);
        writeJsonl(paths.questions, []);
        const app = createApplication({ root });

        const dry = app.canonical.check({ write_report: false });
        assert.equal(dry.schema_version, 'canonical_quality_report.v1');
        assert.equal(fs.existsSync(paths.qualityReport), false);

        const written = app.canonical.check({ write_report: true });
        assert.equal(written.schema_version, 'canonical_quality_report.v1');
        assert.deepEqual(JSON.parse(fs.readFileSync(paths.qualityReport, 'utf8')), written);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
