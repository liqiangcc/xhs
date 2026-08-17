'use strict';

const path = require('path');
const { closure, reachability } = require('../lib/answer_completion');

const ROOT = path.resolve(__dirname, '../..');

function run(options = {}) {
  const root = options.root ? path.resolve(options.root) : ROOT;
  const closureResult = closure({ root, noWrite: true, full: Boolean(options.full) });
  const reachabilityResult = reachability({ root, noWrite: true, full: Boolean(options.full) });

  return {
    schema_version: 'xhs_final_completion_reachability.v1',
    ok: Boolean(closureResult.ok && reachabilityResult.ok),
    closure: {
      ok: Boolean(closureResult.ok),
      canonical_count: closureResult.canonical_count,
      completed_count: closureResult.completed_count,
      incomplete_count: closureResult.incomplete_count,
      answer_file_error_count: (closureResult.answer_file_errors || []).length,
      orphan_answer_count: (closureResult.orphan_answers || []).length,
      orphan_evidence_count: (closureResult.orphan_evidence || []).length,
      incomplete_sample: closureResult.rows || [],
      incomplete_sample_truncated: Boolean(closureResult.incomplete_sample_truncated),
    },
    reachability: {
      ok: Boolean(reachabilityResult.ok),
      valid_question_count: reachabilityResult.valid_question_count,
      reachable_count: reachabilityResult.reachable_count,
      unreachable_count: reachabilityResult.unreachable_count,
      unreachable_sample: reachabilityResult.rows || [],
    },
  };
}

function main(argv = process.argv) {
  try {
    const result = run({ full: argv.includes('--full') });
    console.log(JSON.stringify(result, null, 2));
    return result.ok ? 0 : 2;
  } catch (error) {
    console.error(error.stack || error.message);
    return 1;
  }
}

if (require.main === module) process.exitCode = main(process.argv);

module.exports = { run, main };
