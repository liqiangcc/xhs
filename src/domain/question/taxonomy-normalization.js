'use strict';

function assertTaxonomy(taxonomy) {
    if (!taxonomy || typeof taxonomy !== 'object' || Array.isArray(taxonomy)) {
        throw new Error('taxonomy is required');
    }
    return taxonomy;
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

function isCanonicalDomain(domain, taxonomy) {
    return Boolean(
        domain
        && (taxonomy.domain_l1 || []).includes(domain.l1)
        && (taxonomy.domain_l2_by_l1?.[domain.l1] || []).includes(domain.l2)
    );
}

function normalizeDomainPair(domain, taxonomy) {
    const key = domainPairKey(domain?.l1, domain?.l2);
    const target = parseDomainTarget(taxonomy.domain_pair_aliases?.[key]);
    if (!target || !isCanonicalDomain(target, taxonomy)) return null;
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

function findCanonicalDomainByL2(l2, taxonomy) {
    const value = normalizeText(l2);
    if (!value) return null;
    const normalized = taxonomy.domain_l2_aliases?.[value] || value;
    if (!normalized || normalized === '其他') return null;

    const owners = [];
    for (const [l1, values] of Object.entries(taxonomy.domain_l2_by_l1 || {})) {
        if (values.includes(normalized)) owners.push(l1);
    }
    if (owners.length !== 1) return null;
    return { l1: owners[0], l2: normalized };
}

function normalizeDomainL1(l1, taxonomy) {
    const value = normalizeText(l1);
    if ((taxonomy.domain_l1 || []).includes(value)) return makeResult(true, value, value, 'canonical');
    const normalized = taxonomy.domain_l1_aliases?.[value];
    if (normalized && (taxonomy.domain_l1 || []).includes(normalized)) {
        return makeResult(true, value, normalized, 'legacy_alias');
    }
    return makeResult(false, value, null, 'unknown_domain_l1');
}

function normalizeDomainL2(l2, canonicalL1, taxonomy) {
    const value = normalizeText(l2);
    const allowed = taxonomy.domain_l2_by_l1?.[canonicalL1] || [];
    if (allowed.includes(value)) return makeResult(true, value, value, 'canonical');

    const normalized = taxonomy.domain_l2_aliases?.[value];
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

function validateDomain(domain, taxonomyInput) {
    const taxonomy = assertTaxonomy(taxonomyInput);
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
    if (!valid && (taxonomy.domain_l2_by_l1?.[l1.normalized_value] || []).includes('其他')) {
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

function normalizeEntity(entity, taxonomyInput) {
    const taxonomy = assertTaxonomy(taxonomyInput);
    const value = normalizeText(entity);
    if (!value) return '';
    const key = value.toLowerCase().replace(/\s+/g, '');
    return taxonomy.entity_synonyms?.[key]
        || taxonomy.entity_synonyms?.[value.toLowerCase()]
        || value;
}

module.exports = {
    validateDomain,
    normalizeEntity,
};
