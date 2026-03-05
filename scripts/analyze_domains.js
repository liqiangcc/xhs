const fs = require('fs');
const path = require('path');

const td = path.join(__dirname, '..', 'note_tagged');
const files = fs.readdirSync(td).filter(f => f.endsWith('.json'));

const l1Counts = {};
const l2Counts = {};
const typesCounts = {};
const depthCounts = {};

files.forEach(f => {
    const j = JSON.parse(fs.readFileSync(path.join(td, f), 'utf8'));
    if (!j.tagged_questions || j.tagged_questions.length === 0) return;
    j.tagged_questions.forEach(q => {
        // Domain
        if (q.domain) {
            const l1 = q.domain.l1 || '(empty)';
            const l2 = q.domain.l2 || '(empty)';
            l1Counts[l1] = (l1Counts[l1] || 0) + 1;
            l2Counts[l2] = (l2Counts[l2] || 0) + 1;
        }
        // Type
        const t = q.question_type || '(empty)';
        typesCounts[t] = (typesCounts[t] || 0) + 1;
        // Depth
        const d = q.cognitive_depth || '(empty)';
        depthCounts[d] = (depthCounts[d] || 0) + 1;
    });
});

console.log('=== L1 Domain Distribution (sorted by count) ===');
Object.entries(l1Counts).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => {
    console.log(`  ${v}\t${k}`);
});

console.log('\n=== L2 Domain Distribution (sorted by count, top 50) ===');
Object.entries(l2Counts).sort((a, b) => b[1] - a[1]).slice(0, 50).forEach(([k, v]) => {
    console.log(`  ${v}\t${k}`);
});

console.log('\n=== Question Type Distribution ===');
Object.entries(typesCounts).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => {
    console.log(`  ${v}\t${k}`);
});

console.log('\n=== Cognitive Depth Distribution ===');
Object.entries(depthCounts).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => {
    console.log(`  ${v}\t${k}`);
});
