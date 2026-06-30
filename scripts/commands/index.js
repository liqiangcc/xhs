'use strict';

const { main: buildIndexMain } = require('../build_index');

function main(argv = process.argv) {
    const args = argv.slice(2);
    const subcommand = args[0];
    if (subcommand === 'build') {
        return buildIndexMain(['node', 'scripts/build_index.js', ...args.slice(1)]);
    }
    if (subcommand === 'check') {
        return buildIndexMain(['node', 'scripts/build_index.js', '--check', ...args.slice(1)]);
    }
    console.error('Usage: node scripts/xhs.js index <build|check>');
    return 1;
}

module.exports = {
    main,
};
