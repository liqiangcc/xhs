'use strict';

const path = require('path');
const { readJson } = require('./io');

const DEFAULT_TAXONOMY_PATH = path.resolve(__dirname, '..', '..', 'config', 'taxonomy.json');

let cachedTaxonomy = null;

function loadTaxonomy(taxonomyPath = DEFAULT_TAXONOMY_PATH) {
    if (!cachedTaxonomy || cachedTaxonomy.__path !== taxonomyPath) {
        cachedTaxonomy = readJson(taxonomyPath);
        Object.defineProperty(cachedTaxonomy, '__path', {
            value: taxonomyPath,
            enumerable: false,
        });
    }
    return cachedTaxonomy;
}

function normalizeText(value) {
    return String(value ?? '').trim();
}

function makeResult(valid, value, normalizedValue, reason) {
    return {
        valid,
        value,
        normalized_value: normalizedValue,
        reason,
        is_canonical: valid && value === normalizedValue,
    };
}

function validateQuestionType(type, taxonomy = loadTaxonomy()) {
    const value = normalizeText(type);
    if (taxonomy.question_types.includes(value)) {
        return makeResult(true, value, value, 'canonical');
    }
    const normalized = taxonomy.question_type_aliases[value];
    if (normalized && taxonomy.question_types.includes(normalized)) {
        return makeResult(true, value, normalized, 'legacy_alias');
    }
    return makeResult(false, value, null, 'unknown_question_type');
}

function validateCognitiveDepth(depth, taxonomy = loadTaxonomy()) {
    const value = normalizeText(depth);
    if (taxonomy.cognitive_depths.includes(value)) {
        return makeResult(true, value, value, 'canonical');
    }
    const normalized = taxonomy.cognitive_depth_aliases[value];
    if (normalized && taxonomy.cognitive_depths.includes(normalized)) {
        return makeResult(true, value, normalized, 'legacy_alias');
    }
    return makeResult(false, value, null, 'unknown_cognitive_depth');
}

function normalizeDomainL1(l1, taxonomy = loadTaxonomy()) {
    const value = normalizeText(l1);
    if (taxonomy.domain_l1.includes(value)) return makeResult(true, value, value, 'canonical');
    const normalized = taxonomy.domain_l1_aliases[value];
    if (normalized && taxonomy.domain_l1.includes(normalized)) {
        return makeResult(true, value, normalized, 'legacy_alias');
    }
    return makeResult(false, value, null, 'unknown_domain_l1');
}

function normalizeDomainL2(l2, canonicalL1, taxonomy = loadTaxonomy()) {
    const value = normalizeText(l2);
    const allowed = taxonomy.domain_l2_by_l1[canonicalL1] || [];
    if (allowed.includes(value)) return makeResult(true, value, value, 'canonical');

    const normalized = taxonomy.domain_l2_aliases[value];
    if (normalized) {
        if (allowed.includes(normalized)) return makeResult(true, value, normalized, 'legacy_alias');

        const existsGlobally = Object.values(taxonomy.domain_l2_by_l1)
            .some((items) => items.includes(normalized));
        if (existsGlobally) return makeResult(true, value, normalized, 'legacy_alias_cross_domain');
    }

    return makeResult(false, value, null, 'unknown_domain_l2');
}

function validateDomain(domain, taxonomy = loadTaxonomy()) {
    const l1 = normalizeDomainL1(domain?.l1, taxonomy);
    if (!l1.valid) {
        return {
            valid: false,
            domain,
            normalized_domain: null,
            reason: l1.reason,
            details: { l1 },
        };
    }

    const l2 = normalizeDomainL2(domain?.l2, l1.normalized_value, taxonomy);
    const valid = l2.valid;
    return {
        valid,
        domain,
        normalized_domain: valid
            ? { l1: l1.normalized_value, l2: l2.normalized_value }
            : { l1: l1.normalized_value, l2: null },
        reason: valid
            ? (l1.reason === 'canonical' && l2.reason === 'canonical' ? 'canonical' : 'legacy_alias')
            : l2.reason,
        details: { l1, l2 },
    };
}

function normalizeEntity(entity, taxonomy = loadTaxonomy()) {
    const value = normalizeText(entity);
    if (!value) return '';
    const key = value.toLowerCase().replace(/\s+/g, '');
    return taxonomy.entity_synonyms[key] || taxonomy.entity_synonyms[value.toLowerCase()] || value;
}

module.exports = {
    DEFAULT_TAXONOMY_PATH,
    loadTaxonomy,
    validateDomain,
    validateQuestionType,
    validateCognitiveDepth,
    normalizeEntity,
};
