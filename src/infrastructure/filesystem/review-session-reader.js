'use strict';

const fs = require('fs');
const path = require('path');
const { createCanonicalFsPaths } = require('./canonical-paths');

function createFsReviewSessionReader(options = {}) {
    if (!options.root) throw new Error('Filesystem review session reader root is required');
    const paths = options.paths || createCanonicalFsPaths(options.root);

    return {
        list() {
            if (!fs.existsSync(paths.reviewSessionsDir)) return [];
            return fs.readdirSync(paths.reviewSessionsDir)
                .filter((name) => name.endsWith('.json'))
                .sort()
                .map((name) => {
                    const sessionPath = path.join(paths.reviewSessionsDir, name);
                    const source = path.relative(paths.root, sessionPath);
                    try {
                        return {
                            source,
                            session: JSON.parse(fs.readFileSync(sessionPath, 'utf8')),
                        };
                    } catch (error) {
                        return {
                            source,
                            parse_error: 'invalid_json',
                        };
                    }
                });
        },
    };
}

module.exports = {
    createFsReviewSessionReader,
};
