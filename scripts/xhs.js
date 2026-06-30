#!/usr/bin/env node
'use strict';

function printHelp() {
    console.log([
        'XHS CLI',
        '',
        'Usage: node scripts/xhs.js <command> [subcommand] [options]',
        '',
        'Commands:',
        '  migrate build-questions   Build Question main data from note_tagged',
        '  migrate status            Show migration output status',
        '  migrate run all --check   Run registered migrations in check mode',
        '  validate all              Validate schema, taxonomy, and hash consistency',
        '  validate schema           Validate questions.jsonl schema',
        '  validate taxonomy         Report taxonomy canonical/legacy/unknown status',
        '  validate hash             Validate question_id hashes',
        '  index build               Build query indexes from questions.jsonl',
        '  index check               Verify indexes are up to date',
        '  query entity <value>      Query by tech entity',
        '  query company <value>     Query by company',
        '  query domain --l1 <v>     Query by domain l1 or l2',
        '  query hotspot             Show repeated question_id hotspots',
        '  canonical suggest         Generate canonical candidates',
        '  canonical accept          Confirm a canonical candidate',
        '  canonical list|check      Inspect canonical coverage and quality',
        '  canonical merge|split     Maintain canonical question groups',
        '  canonical stats           Show canonical coverage',
        '  answer init|status        Manage canonical answer files',
        '  answer validate|sync      Validate answer metadata and sync statuses',
        '  review prepare|today      Prepare and list due review items',
        '  review mark|weak          Mark review result and inspect weak items',
        '  issue render|sync|check   Render and sync GitHub review issue cards',
    ].join('\n'));
}

function main(argv = process.argv) {
    const command = argv[2];
    if (!command || command === 'help' || command === '--help') {
        printHelp();
        return 0;
    }

    const forwarded = ['node', `scripts/commands/${command}.js`, ...argv.slice(3)];
    if (command === 'migrate') return require('./commands/migrate').main(forwarded);
    if (command === 'validate') return require('./commands/validate').main(forwarded);
    if (command === 'index') return require('./commands/index').main(forwarded);
    if (command === 'query') return require('./commands/query').main(forwarded);
    if (command === 'canonical') return require('./commands/canonical').main(forwarded);
    if (command === 'answer') return require('./commands/answer').main(forwarded);
    if (command === 'review') return require('./commands/review').main(forwarded);
    if (command === 'issue') return require('./commands/issue').main(forwarded);

    console.error(`Unknown command: ${command}`);
    printHelp();
    return 1;
}

if (require.main === module) {
    process.exitCode = main(process.argv);
}

module.exports = {
    main,
};
