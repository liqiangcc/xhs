'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { currentDateString, defaultDate } = require('../scripts/lib/date');

test('currentDateString uses the configured timezone', () => {
    const now = new Date('2026-06-30T18:00:00Z');

    assert.equal(currentDateString({ now, timeZone: 'UTC' }), '2026-06-30');
    assert.equal(currentDateString({ now, timeZone: 'Asia/Shanghai' }), '2026-07-01');
});

test('defaultDate respects explicit dates before environment fallbacks', () => {
    const originalReviewDate = process.env.XHS_REVIEW_DATE;
    const originalBuildDate = process.env.XHS_BUILD_DATE;
    process.env.XHS_REVIEW_DATE = '2026-07-02';
    process.env.XHS_BUILD_DATE = '2026-07-03';

    try {
        assert.equal(defaultDate({ date: '2026-07-04' }), '2026-07-04');
        assert.equal(defaultDate({ buildDate: '2026-07-05' }), '2026-07-05');
        assert.equal(defaultDate(), '2026-07-02');
    } finally {
        if (originalReviewDate === undefined) delete process.env.XHS_REVIEW_DATE;
        else process.env.XHS_REVIEW_DATE = originalReviewDate;
        if (originalBuildDate === undefined) delete process.env.XHS_BUILD_DATE;
        else process.env.XHS_BUILD_DATE = originalBuildDate;
    }
});
