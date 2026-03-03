const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * XHS Note Processor
 * Usage: node scripts/xhs_process.js <uuid>
 * 
 * 1. Read note_desc/{uuid}.txt
 * 2. (Manual/AI Step) Logic to structure -> note_structured/{uuid}.json
 * 3. Call node scripts/generate_hashes.js note_structured/{uuid}.json
 * 4. (Manual/AI Step) Logic to tag -> note_tagged/{uuid}.json
 */

const uuid = process.argv[2];
if (!uuid) {
    console.error('Usage: node scripts/xhs_process.js <uuid>');
    process.exit(1);
}

const paths = {
    desc: path.join('note_desc', `${uuid}.txt`),
    img: path.join('note_img_txt', `${uuid}.txt`),
    structured: path.join('note_structured', `${uuid}.json`),
    tagged: path.join('note_tagged', `${uuid}.json`)
};

function runHashGenerator(structuredPath) {
    try {
        console.log(`[RUN] Generating hashes for ${structuredPath}...`);
        const output = execSync(`node scripts/generate_hashes.js ${structuredPath}`, { encoding: 'utf-8' });
        return output.split('\n').filter(line => line.trim()).map(line => {
            const [index, hash, question] = line.split('|');
            return { index, hash, question };
        });
    } catch (e) {
        console.error(`Error running generate_hashes.js: ${e.message}`);
        return [];
    }
}

async function processNote() {
    console.log(`\n--- Workflow Execution for Note: ${uuid} ---`);

    if (!fs.existsSync(paths.desc)) {
        console.error(`[ERROR] Source file not found: ${paths.desc}`);
        return;
    }

    // Step 1: Extraction Check
    if (!fs.existsSync(paths.structured)) {
        console.log(`[PENDING] Extraction needed for ${uuid}.`);
        // The agent will perform this step manually or via skill call
        return;
    }

    // Step 2: Generate Hashes using existing script
    const hashes = runHashGenerator(paths.structured);
    if (hashes.length === 0) {
        console.error(`[ERROR] Failed to generate hashes.`);
        return;
    }

    console.log(`[SUCCESS] Generated ${hashes.length} hashes.`);
    console.table(hashes.slice(0, 5)); // Show first 5

    // Step 3: Tagging Check
    if (fs.existsSync(paths.tagged)) {
        console.log(`[DONE] Note ${uuid} is already tagged.`);
        return;
    }

    console.log(`[CONTINUE] Proceeding to tagging for ${uuid}...`);
}

processNote();
