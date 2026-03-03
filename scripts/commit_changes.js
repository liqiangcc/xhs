const { execSync } = require('child_process');

/**
 * Automates the git commit process for XHS note processing.
 */

try {
    console.log('--- Git Commit Automation ---');

    // Add scripts
    console.log('Adding scripts...');
    execSync('git add scripts/*.js');

    // Add processed notes
    console.log('Adding structured and tagged notes...');
    execSync('git add note_structured/*.json note_tagged/*.json');

    // Commit
    const commitMessage = 'feat: auto-processed XHS notes and updated scripts';
    console.log(`Committing with message: "${commitMessage}"`);
    execSync(`git commit -m "${commitMessage}"`);

    console.log('[SUCCESS] All changes added and committed.');
} catch (error) {
    console.error('[FAILED] Failed to commit changes.');
    console.error(error.stdout || error.message);
    process.exit(1);
}
