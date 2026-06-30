const fs = require('fs');
const path = require('path');
const { computeQuestionId } = require('./lib/hash');

/**
 * Generates MD5 hashes for questions in a structured note file.
 * Usage: node scripts/generate_hashes.js <path_to_structured_json>
 */

const filePath = process.argv[2];

if (!filePath) {
    console.error('Usage: node scripts/generate_hashes.js <path_to_structured_json>');
    process.exit(1);
}

try {
    const absolutePath = path.isAbsolute(filePath) ? filePath : path.join(process.cwd(), filePath);
    const content = fs.readFileSync(absolutePath, 'utf-8');
    const data = JSON.parse(content);

    if (!data.questions || !Array.isArray(data.questions)) {
        console.error('Invalid JSON: "questions" array not found.');
        process.exit(1);
    }

    data.questions.forEach((q, i) => {
        const hash = computeQuestionId(q);
        console.log(`${i}|${hash}|${q}`);
    });
} catch (error) {
    console.error(`Error processing file: ${error.message}`);
    process.exit(1);
}
