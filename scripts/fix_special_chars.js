const fs = require('fs');
const path = require('path');

const taggedDir = 'note_tagged';
const files = fs.readdirSync(taggedDir);

function normalizeEntity(entity) {
    if (typeof entity !== 'string') return entity;

    let normalized = entity.trim();

    // 1. Remove parentheticals at the end (e.g. "快表 (TLB)" -> "快表")
    // Note: If the entire string is in parentheses, we don't want to strip it to nothing, 
    // but usually it's "中文 (English)".
    normalized = normalized.replace(/\s*[（\(].*?[）\)]\s*$/, '');

    // 2. Remove leading/trailing special chars (like @, #, etc.) EXCEPT + and # for C++, C#, B+树
    normalized = normalized.replace(/^[^a-zA-Z0-9\u4e00-\u9fa5\+\#]+/, '');
    normalized = normalized.replace(/[^a-zA-Z0-9\u4e00-\u9fa5\+\#]+$/, '');

    // 3. Special cases mapping for things that are left
    const mapping = {
        'tcp/ip': 'tcp',
        'http/https': 'http',
        'ssl/tls': 'https', // usually grouped with https
        'i/o': 'io',
        '磁盘i/o': '磁盘io',
        '网络i/o': '网络io'
    };

    const lower = normalized.toLowerCase();
    if (mapping[lower]) {
        return mapping[lower];
    }

    // If we stripped everything and it's empty now, return original to avoid empty tags
    if (normalized === '') return entity;

    return normalized;
}

function normalizeArray(arr) {
    if (!Array.isArray(arr)) return arr;
    let changed = false;
    // Use flatMap in case stripping created a duplicate and we want to remove it
    const newArr = arr.map(e => {
        const normalized = normalizeEntity(e);
        if (normalized !== e) {
            changed = true;
        }
        return normalized;
    });

    if (changed) {
        // deduplicate
        return [...new Set(newArr.filter(Boolean))];
    }
    return arr;
}

let updatedNotes = 0;
console.log('1. Processing note_tagged files for special characters...');

files.forEach(f => {
    const filePath = path.join(taggedDir, f);
    const fileContent = fs.readFileSync(filePath, 'utf8');
    let d;
    try {
        d = JSON.parse(fileContent);
    } catch (e) {
        return; // Skip invalid JSON
    }

    let isNoteUpdated = false;

    if (d.tagged_questions) {
        d.tagged_questions.forEach(q => {
            if (q.tech_entities) {
                const normalized = normalizeArray(q.tech_entities);
                // Compare arrays structurally
                if (JSON.stringify(normalized) !== JSON.stringify(q.tech_entities)) {
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

console.log('\n2. Processing hashmap_slim.json for special characters...');
const hashmapList = [];
files.forEach(f => {
    const d = JSON.parse(fs.readFileSync(path.join(taggedDir, f), 'utf8'));
    (d.tagged_questions || []).forEach(q => {
        if (q.question_id && q.original_question) {
            hashmapList.push({
                question_id: q.question_id,
                original_question: q.original_question,
                domain: q.domain,
                question_type: q.question_type,
                cognitive_depth: q.cognitive_depth,
                tech_entities: q.tech_entities,
                business_context: q.business_context,
                is_valid_for_library: q.is_valid_for_library
            });
        }
    });
});

fs.writeFileSync('hashmap_slim.json', JSON.stringify(hashmapList, null, 2), 'utf8');
console.log(`✅ Rebuilt hashmap_slim.json with ${hashmapList.length} total questions.`);
console.log('\n🎉 Finished cleaning special characters!');
