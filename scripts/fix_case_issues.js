const fs = require('fs');
const path = require('path');

const taggedDir = 'note_tagged';
const files = fs.readdirSync(taggedDir);

// 1. Identify the most frequent casing for each group
console.log('1. Identifying standard casings...');
const entityCount = {};
files.forEach(f => {
    const d = JSON.parse(fs.readFileSync(path.join(taggedDir, f), 'utf8'));
    (d.tagged_questions || []).forEach(q => {
        (q.tech_entities || []).forEach(e => {
            // Ensure it's a string
            if (typeof e === 'string') {
                entityCount[e] = (entityCount[e] || 0) + 1;
            }
        });
    });
});

const lowerMap = Object.create(null);
Object.entries(entityCount).forEach(([e, count]) => {
    const lower = e.toLowerCase();
    if (!lowerMap[lower]) lowerMap[lower] = [];
    lowerMap[lower].push({ ori: e, cnt: count });
});

// Create mapping from lower_case to best_case
const standardCasingMap = Object.create(null);
let totalReplacements = 0;

for (const lower in lowerMap) {
    if (lowerMap[lower].length > 1) {
        // Sort descending by count
        lowerMap[lower].sort((a, b) => b.cnt - a.cnt);
        // The preferred casing is the one most widely used
        const bestCase = lowerMap[lower][0].ori;

        // Map all variations (including the best case itself for simplicity) to the best case
        lowerMap[lower].forEach(item => {
            if (item.ori !== bestCase) {
                standardCasingMap[item.ori] = bestCase;
                totalReplacements++;
            }
        });
    }
}

console.log(`Found ${totalReplacements} casing variations to normalize.`);

// 2. Normalization function
function normalizeArray(arr) {
    if (!Array.isArray(arr)) return arr;
    let changed = false;
    const newArr = arr.map(e => {
        if (typeof e === 'string' && standardCasingMap[e]) {
            changed = true;
            return standardCasingMap[e];
        }
        return e;
    });

    // Also deduplicate in case multiple variations maps to the same standard casing in one array
    if (changed) {
        return [...new Set(newArr)];
    }
    return arr;
}

// 3. Process note_tagged files
console.log('\n2. Updating note_tagged files...');
let updatedNotes = 0;
files.forEach(f => {
    const filePath = path.join(taggedDir, f);
    const fileContent = fs.readFileSync(filePath, 'utf8');
    const d = JSON.parse(fileContent);

    let isNoteUpdated = false;

    if (d.tagged_questions) {
        d.tagged_questions.forEach(q => {
            if (q.tech_entities) {
                const normalized = normalizeArray(q.tech_entities);
                // Simple check if array reference changed 
                // (normalizeArray only returns a new array if there was a modification)
                if (normalized !== q.tech_entities) {
                    q.tech_entities = normalized;
                    isNoteUpdated = true;
                }
            }
        });
    }

    if (isNoteUpdated) {
        fs.writeFileSync(filePath, JSON.stringify(d, null, 4), 'utf8');
        updatedNotes++;
    }
});

console.log(`✅ Updated ${updatedNotes} note_tagged files.`);

// 4. Process hashmap_slim.json
console.log('\n3. Updating hashmap_slim.json...');
if (fs.existsSync('hashmap_slim.json')) {
    try {
        const hashmapObj = JSON.parse(fs.readFileSync('hashmap_slim.json', 'utf8'));
        let isHashmapUpdated = false;

        // Iterate through key-value pairs (assuming structure of the hashmap)
        // Looking at the data earlier, it's an array of objects
        if (Array.isArray(hashmapObj)) {
            hashmapObj.forEach(q => {
                if (q.tech_entities) {
                    const normalized = normalizeArray(q.tech_entities);
                    if (normalized !== q.tech_entities) {
                        q.tech_entities = normalized;
                        isHashmapUpdated = true;
                    }
                }
            });

            if (isHashmapUpdated) {
                fs.writeFileSync('hashmap_slim.json', JSON.stringify(hashmapObj, null, 2), 'utf8');
                console.log(`✅ Updated hashmap_slim.json.`);
            } else {
                console.log(`ℹ️ No casing updates needed in hashmap_slim.json.`);
            }
        } else {
            // if it's an object with question_ids as keys
            for (const qId in hashmapObj) {
                const item = hashmapObj[qId];
                if (item && item.tech_entities) {
                    const normalized = normalizeArray(item.tech_entities);
                    if (normalized !== item.tech_entities) {
                        item.tech_entities = normalized;
                        isHashmapUpdated = true;
                    }
                }
            }
            if (isHashmapUpdated) {
                fs.writeFileSync('hashmap_slim.json', JSON.stringify(hashmapObj, null, 2), 'utf8');
                console.log(`✅ Updated hashmap_slim.json.`);
            } else {
                console.log(`ℹ️ No casing updates needed in hashmap_slim.json.`);
            }
        }

    } catch (err) {
        console.error('Error processing hashmap_slim.json:', err.message);
    }
} else {
    console.log('ℹ️ hashmap_slim.json not found, skipping.');
}

console.log('\n🎉 Finished standardizing tech_entities cases!');
