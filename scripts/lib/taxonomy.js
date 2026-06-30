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

function domainPairKey(l1, l2) {
    return `${normalizeText(l1)}/${normalizeText(l2)}`;
}

function parseDomainTarget(target) {
    if (!target) return null;
    if (typeof target === 'string') {
        const [l1, l2] = target.split('/');
        if (!l1 || !l2) return null;
        return { l1, l2 };
    }
    if (target && typeof target === 'object' && target.l1 && target.l2) {
        return { l1: target.l1, l2: target.l2 };
    }
    return null;
}

function isCanonicalDomain(domain, taxonomy = loadTaxonomy()) {
    return Boolean(
        domain
        && taxonomy.domain_l1.includes(domain.l1)
        && (taxonomy.domain_l2_by_l1[domain.l1] || []).includes(domain.l2)
    );
}

function normalizeDomainPair(domain, taxonomy = loadTaxonomy()) {
    const key = domainPairKey(domain?.l1, domain?.l2);
    const target = parseDomainTarget(taxonomy.domain_pair_aliases?.[key]);
    if (!target || !isCanonicalDomain(target, taxonomy)) {
        return null;
    }
    return {
        valid: true,
        domain,
        normalized_domain: target,
        reason: 'legacy_pair_alias',
        details: {
            pair: makeResult(true, key, `${target.l1}/${target.l2}`, 'legacy_pair_alias'),
        },
    };
}

function findCanonicalDomainByL2(l2, taxonomy = loadTaxonomy()) {
    const value = normalizeText(l2);
    if (!value) return null;
    const normalized = taxonomy.domain_l2_aliases[value] || value;
    if (!normalized || normalized === '其他') return null;

    const owners = [];
    for (const [l1, values] of Object.entries(taxonomy.domain_l2_by_l1)) {
        if (values.includes(normalized)) owners.push(l1);
    }
    if (owners.length !== 1) return null;
    return { l1: owners[0], l2: normalized };
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

        const inferred = findCanonicalDomainByL2(value, taxonomy);
        if (inferred) {
            return {
                ...makeResult(true, value, inferred.l2, 'legacy_alias_cross_domain'),
                normalized_l1: inferred.l1,
            };
        }
    }

    return makeResult(false, value, null, 'unknown_domain_l2');
}

function validateDomain(domain, taxonomy = loadTaxonomy()) {
    const pair = normalizeDomainPair(domain, taxonomy);
    if (pair) return pair;

    const l1 = normalizeDomainL1(domain?.l1, taxonomy);
    if (!l1.valid) {
        const inferred = findCanonicalDomainByL2(domain?.l2, taxonomy);
        if (inferred) {
            return {
                valid: true,
                domain,
                normalized_domain: inferred,
                reason: 'legacy_l2_inferred',
                details: {
                    l1,
                    l2: makeResult(true, normalizeText(domain?.l2), inferred.l2, 'legacy_l2_inferred'),
                },
            };
        }
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
    const normalizedL1 = l2.normalized_l1 || l1.normalized_value;
    if (!valid && (taxonomy.domain_l2_by_l1[l1.normalized_value] || []).includes('其他')) {
        return {
            valid: true,
            domain,
            normalized_domain: { l1: l1.normalized_value, l2: '其他' },
            reason: 'legacy_l2_other',
            details: {
                l1,
                l2: makeResult(true, normalizeText(domain?.l2), '其他', 'legacy_l2_other'),
            },
        };
    }
    return {
        valid,
        domain,
        normalized_domain: valid
            ? { l1: normalizedL1, l2: l2.normalized_value }
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
    findCanonicalDomainByL2,
};
