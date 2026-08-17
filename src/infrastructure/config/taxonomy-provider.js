'use strict';

const path = require('path');
const { readJson } = require('../../../scripts/lib/io');

const DEFAULT_TAXONOMY_PATH = path.resolve(__dirname, '..', '..', '..', 'config', 'taxonomy.json');

function loadTaxonomy(options = {}) {
    const taxonomyPath = options.taxonomyPath
        ? path.resolve(options.taxonomyPath)
        : DEFAULT_TAXONOMY_PATH;
    return readJson(taxonomyPath);
}

module.exports = {
    DEFAULT_TAXONOMY_PATH,
    loadTaxonomy,
};
