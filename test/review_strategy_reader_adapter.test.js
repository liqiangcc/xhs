'use strict';

const fs = require('fs');
const os = require('os');
const path = require('path');
const test = require('node:test');
const assert = require('node:assert/strict');

const { writeJson } = require('../scripts/lib/io');
const {
    createFileReviewStrategyReaderAdapter,
} = require('../src/infrastructure/config/review-strategy-reader-adapter');

test('FileReviewStrategyReaderAdapter reads the configured review strategy without interpreting it', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-review-strategy-reader-'));
    try {
        const strategyPath = path.join(root, 'review_strategy.json');
        const strategy = {
            schema_version: 'review_strategy.v1',
            priority_weights: { P0: 99 },
        };
        writeJson(strategyPath, strategy);

        const reader = createFileReviewStrategyReaderAdapter({ strategyPath });
        assert.deepEqual(reader.read(), strategy);
    } finally {
        fs.rmSync(root, { recursive: true, force: true });
    }
});
