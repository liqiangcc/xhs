#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { auditOneCandidate } = require('../lib/answer_quality');

function stable(value) {
    if (Array.isArray(value)) return value.map(stable);
    if (value && typeof value === 'object') {
        return Object.fromEntries(Object.keys(value).sort().map((key) => [key, stable(value[key])]));
    }
    return value;
}

function same(left, right) {
    return JSON.stringify(stable(left)) === JSON.stringify(stable(right));
}

function verifyManifest(options = {}) {
    const root = path.resolve(options.root || path.join(__dirname, '..', '..'));
    const manifestPath = path.resolve(options.manifest || path.join(root, 'review', 'candidates', 'rereview-regressions.json'));
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    if (manifest.schema_version !== 'rereview_regression_manifest.v1' || !Array.isArray(manifest.candidates)) {
        throw new Error('invalid rereview regression manifest');
    }

    const seen = new Set();
    const rows = [];
    for (const spec of manifest.candidates) {
        const canonicalId = spec.canonical_id;
        if (!canonicalId || seen.has(canonicalId)) throw new Error(`invalid or duplicate canonical_id: ${canonicalId || '<missing>'}`);
        seen.add(canonicalId);

        const candidatePath = path.join(root, 'review', 'candidates', 'answers', `${canonicalId}.md`);
        if (!fs.existsSync(candidatePath)) throw new Error(`candidate missing: ${canonicalId}`);
        const row = auditOneCandidate(candidatePath, { root, noWrite: true });
        if (row.candidate_sha256 !== spec.candidate_sha256) {
            throw new Error(`unexpected candidate hash for ${canonicalId}: ${row.candidate_sha256}`);
        }
        if (!row.ok) {
            throw new Error(`candidate/rereview audit failed for ${canonicalId}: ${JSON.stringify({ hard_failures: row.hard_failures, errors: row.errors })}`);
        }
        const minimumScore = Number(spec.minimum_total_score || 90);
        if (row.total_score < minimumScore) {
            throw new Error(`rereview score below threshold for ${canonicalId}: ${row.total_score} < ${minimumScore}`);
        }
        if ((row.hard_failures || []).length) {
            throw new Error(`unexpected hard failures for ${canonicalId}: ${row.hard_failures.join(',')}`);
        }

        if (spec.stored_audit_required) {
            const auditPath = path.join(root, 'review', 'candidates', 'audits', `${canonicalId}.json`);
            if (!fs.existsSync(auditPath)) throw new Error(`stored audit missing: ${canonicalId}`);
            const stored = JSON.parse(fs.readFileSync(auditPath, 'utf8'));
            const fields = ['schema_version', 'ok', 'canonical_id', 'candidate_path', 'candidate_sha256', 'answer_type',
                'quality_tier', 'evidence_path', 'scores', 'total_score', 'hard_failures', 'errors', 'revision_suggestions'];
            for (const field of fields) {
                if (!same(stored[field], row[field])) {
                    throw new Error(`stored audit is stale for ${canonicalId} field ${field}: ${JSON.stringify({ stored: stored[field], computed: row[field] })}`);
                }
            }
        }

        rows.push({
            canonical_id: canonicalId,
            candidate_sha256: row.candidate_sha256,
            total_score: row.total_score,
            stored_audit_verified: Boolean(spec.stored_audit_required),
        });
    }

    return {
        schema_version: 'rereview_regression_report.v1',
        ok: true,
        candidate_count: rows.length,
        rows,
    };
}

if (require.main === module) {
    try {
        const report = verifyManifest();
        console.log(JSON.stringify(report, null, 2));
    } catch (error) {
        console.error(error.stack || error.message || String(error));
        process.exit(1);
    }
}

module.exports = { stable, verifyManifest };
