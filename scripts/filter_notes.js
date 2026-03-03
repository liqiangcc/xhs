const fs = require('fs');
const path = require('path');

/**
 * Scans note_desc for interview notes that haven't been structured yet.
 * Filters by keywords (Java, round info) and minimum content length.
 * Usage: node scripts/filter_notes.js [limit]
 */

const limit = parseInt(process.argv[2]) || 10;
const noteDescDir = 'note_desc';
const noteStructuredDir = 'note_structured';

try {
    const structuredFiles = new Set(
        fs.readdirSync(noteStructuredDir)
            .filter(f => f.endsWith('.json'))
            .map(f => path.basename(f, '.json'))
    );

    const allFiles = fs.readdirSync(noteDescDir)
        .filter(f => f.endsWith('.txt'));

    let foundCount = 0;
    const results = [];

    for (const file of allFiles) {
        const id = path.basename(file, '.txt');

        // Skip if already structured
        if (structuredFiles.has(id)) continue;

        try {
            const content = fs.readFileSync(path.join(noteDescDir, file), 'utf-8');

            const hasRoundInfo = /一面|二面|三面|校招|社招|实习|面经/.test(content);
            const hasTechInfo = /Java|Spring|MySQL|Redis|架构|算法/.test(content);
            const isLongEnough = content.length > 500;

            if (hasRoundInfo && hasTechInfo && isLongEnough) {
                results.push(file);
                foundCount++;
                if (foundCount >= limit) break;
            }
        } catch (e) {
            // Skip unreadable files
        }
    }

    if (results.length > 0) {
        console.log(results.join('\n'));
    } else {
        console.warn('No pending notes found matching the criteria.');
    }
} catch (error) {
    console.error(`Error scanning notes: ${error.message}`);
    process.exit(1);
}
