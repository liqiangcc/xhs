'use strict';

const path = require('path');
const { readJson, readJsonl } = require('./io');

const DEFAULT_SCHEMA_DIR = path.resolve(__dirname, '..', '..', 'schemas');

function loadSchema(schemaNameOrPath, schemaDir = DEFAULT_SCHEMA_DIR) {
    const schemaPath = path.isAbsolute(schemaNameOrPath)
        ? schemaNameOrPath
        : path.join(schemaDir, schemaNameOrPath);
    return readJson(schemaPath);
}

function typeOf(value) {
    if (value === null) return 'null';
    if (Array.isArray(value)) return 'array';
    if (Number.isInteger(value)) return 'integer';
    return typeof value;
}

function matchesType(value, expected) {
    if (expected === 'number') return typeof value === 'number' && Number.isFinite(value);
    if (expected === 'integer') return Number.isInteger(value);
    return typeOf(value) === expected;
}

function validateValue(value, schema, pointer = '$') {
    const errors = [];
    if (!schema || typeof schema !== 'object') return errors;

    if (schema.type) {
        const types = Array.isArray(schema.type) ? schema.type : [schema.type];
        if (!types.some((type) => matchesType(value, type))) {
            errors.push({
                path: pointer,
                message: `expected type ${types.join('|')}, got ${typeOf(value)}`,
            });
            return errors;
        }
    }

    if (schema.enum && !schema.enum.includes(value)) {
        errors.push({
            path: pointer,
            message: `expected one of ${schema.enum.join(', ')}`,
        });
    }

    if (typeof value === 'string' && schema.pattern) {
        const re = new RegExp(schema.pattern);
        if (!re.test(value)) {
            errors.push({
                path: pointer,
                message: `does not match pattern ${schema.pattern}`,
            });
        }
    }

    if (typeof value === 'number') {
        if (typeof schema.minimum === 'number' && value < schema.minimum) {
            errors.push({ path: pointer, message: `must be >= ${schema.minimum}` });
        }
        if (typeof schema.maximum === 'number' && value > schema.maximum) {
            errors.push({ path: pointer, message: `must be <= ${schema.maximum}` });
        }
    }

    if (Array.isArray(value)) {
        if (typeof schema.minItems === 'number' && value.length < schema.minItems) {
            errors.push({ path: pointer, message: `must contain at least ${schema.minItems} items` });
        }
        if (schema.items) {
            value.forEach((item, index) => {
                errors.push(...validateValue(item, schema.items, `${pointer}[${index}]`));
            });
        }
    }

    if (value && typeof value === 'object' && !Array.isArray(value)) {
        for (const field of schema.required || []) {
            if (!(field in value)) {
                errors.push({ path: pointer, message: `missing required field ${field}` });
            }
        }
        for (const [key, childSchema] of Object.entries(schema.properties || {})) {
            if (key in value) {
                errors.push(...validateValue(value[key], childSchema, `${pointer}.${key}`));
            }
        }
        if (schema.additionalProperties === false) {
            const known = new Set(Object.keys(schema.properties || {}));
            for (const key of Object.keys(value)) {
                if (!known.has(key)) {
                    errors.push({ path: `${pointer}.${key}`, message: 'additional property is not allowed' });
                }
            }
        }
    }

    return errors;
}

function validateRecord(record, schema) {
    return validateValue(record, schema);
}

function validateJsonlFile(filePath, schema) {
    const records = readJsonl(filePath);
    const errors = [];
    records.forEach((record, index) => {
        const recordErrors = validateRecord(record, schema);
        for (const error of recordErrors) {
            errors.push({
                line: index + 1,
                question_id: record.question_id,
                ...error,
            });
        }
    });
    return {
        file: filePath,
        count: records.length,
        error_count: errors.length,
        errors,
    };
}

module.exports = {
    DEFAULT_SCHEMA_DIR,
    loadSchema,
    validateRecord,
    validateJsonlFile,
};
