'use strict';

const fs = require('fs');
const path = require('path');

function ensureDir(dirPath) {
    fs.mkdirSync(dirPath, { recursive: true });
}

function stableCopy(value) {
    if (Array.isArray(value)) {
        return value.map(stableCopy);
    }
    if (value && typeof value === 'object') {
        const out = {};
        for (const key of Object.keys(value).sort()) {
            out[key] = stableCopy(value[key]);
        }
        return out;
    }
    return value;
}

function stableStringify(value) {
    return JSON.stringify(stableCopy(value));
}

function stablePrettyStringify(value) {
    return `${JSON.stringify(stableCopy(value), null, 2)}\n`;
}

function readJson(filePath, fallback = undefined) {
    if (!fs.existsSync(filePath)) {
        if (fallback !== undefined) return fallback;
        throw new Error(`JSON file not found: ${filePath}`);
    }
    return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

function writeJson(filePath, value) {
    ensureDir(path.dirname(filePath));
    fs.writeFileSync(filePath, stablePrettyStringify(value), 'utf8');
}

function readJsonl(filePath, fallback = []) {
    if (!fs.existsSync(filePath)) {
        return fallback;
    }
    const raw = fs.readFileSync(filePath, 'utf8').trim();
    if (!raw) return [];
    return raw.split(/\r?\n/).map((line, index) => {
        try {
            return JSON.parse(line);
        } catch (error) {
            throw new Error(`Invalid JSONL at ${filePath}:${index + 1}: ${error.message}`);
        }
    });
}

function writeJsonl(filePath, records) {
    ensureDir(path.dirname(filePath));
    const body = records.map(stableStringify).join('\n');
    fs.writeFileSync(filePath, body ? `${body}\n` : '', 'utf8');
}

function listJsonFiles(dirPath) {
    if (!fs.existsSync(dirPath)) return [];
    return fs.readdirSync(dirPath)
        .filter((file) => file.endsWith('.json'))
        .sort()
        .map((file) => path.join(dirPath, file));
}

module.exports = {
    ensureDir,
    stableCopy,
    stableStringify,
    stablePrettyStringify,
    readJson,
    writeJson,
    readJsonl,
    writeJsonl,
    listJsonFiles,
};
