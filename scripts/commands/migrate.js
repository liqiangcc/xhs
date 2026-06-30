'use strict';

const { main: buildQuestionsMain } = require('../migrate/build_questions_from_tagged');

function main(argv = process.argv) {
    const args = argv.slice(2);
    const subcommand = args[0];
    if (subcommand === 'build-questions') {
        return buildQuestionsMain(['node', 'scripts/migrate/build_questions_from_tagged.js', ...args.slice(1)]);
    }
    console.error('Usage: node scripts/xhs.js migrate build-questions [--check]');
    return 1;
}

module.exports = {
    main,
};
