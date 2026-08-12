'use strict';

/**
 * Composition-root anchor for the incremental architecture migration.
 *
 * Phase A deliberately wires no production use cases yet. Concrete adapters
 * must be introduced here only when a vertical slice is migrated, rather than
 * being instantiated from Domain or Application modules.
 */
function createApplication() {
    return Object.freeze({});
}

module.exports = {
    createApplication,
};
