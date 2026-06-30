'use strict';

function normalizedFlag(key) {
    return String(key || '').replace(/-/g, '').toLowerCase();
}

function applyGlobalBooleanOption(options, key) {
    const normalized = normalizedFlag(key);
    if (normalized === 'nowrite') {
        options.noWrite = true;
        options.noManifest = true;
        return true;
    }
    if (normalized === 'nomanifest') {
        options.noManifest = true;
        return true;
    }
    if (normalized === 'noreport') {
        options.noReport = true;
        return true;
    }
    return false;
}

function shouldWriteReports(options = {}) {
    return !options.noWrite && !options.noReport;
}

module.exports = {
    applyGlobalBooleanOption,
    shouldWriteReports,
};
