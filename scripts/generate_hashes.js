const fs = require('fs');
const crypto = require('crypto');
const path = require('path');

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
        // Normalize: lowercase and remove non-alphanumeric/unsupported characters
        const normalized = q.toLowerCase().replace(/[^\w\u4e00-\u9fa5]/g, '');
        const hash = crypto.createHash('md5').update(normalized).digest('hex');
        console.log(`${i}|${hash}|${q}`);
    });
} catch (error) {
    console.error(`Error processing file: ${error.message}`);
    process.exit(1);
}
