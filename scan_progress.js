const fs = require('fs');
const path = require('path');

const CONFIG = {
    dirs: {
        desc: 'note_desc',
        img: 'note_img_txt',
        structured: 'note_structured',
        tagged: 'note_tagged'
    }
};

function getFilenames(dir) {
    if (!fs.existsSync(dir)) return [];
    return fs.readdirSync(dir).map(f => path.basename(f, path.extname(f)));
}

function scan() {
    console.log('--- XHS Pipeline Progress Scan ---\n');

    const descIds = getFilenames(CONFIG.dirs.desc);
    const imgIds = getFilenames(CONFIG.dirs.img);
    const structuredIds = new Set(getFilenames(CONFIG.dirs.structured));
    const taggedIds = new Set(getFilenames(CONFIG.dirs.tagged));

    const allIds = Array.from(new Set([...descIds, ...imgIds]));

    const stats = {
        total: allIds.length,
        pending_structure: 0,
        pending_tag: 0,
        completed: 0
    };

    const tableData = allIds.map(id => {
        const isStructured = structuredIds.has(id);
        const isTagged = taggedIds.has(id);

        let status = 'TODO';
        if (isStructured && isTagged) {
            status = 'DONE';
            stats.completed++;
        } else if (isStructured) {
            status = 'STRUC_DONE';
            stats.pending_tag++;
        } else {
            stats.pending_structure++;
        }

        return { id, isStructured, isTagged, status };
    });

    // Print Summary
    console.log(`Total Notes Found: ${stats.total}`);
    console.log(`✅ Fully Processed: ${stats.completed}`);
    console.log(`⏳ Pending Tagging: ${stats.pending_tag}`);
    console.log(`❌ Pending Structure: ${stats.pending_structure}`);
    console.log('\n--- Details (Top 20 Unfinished) ---\n');

    const unfinished = tableData
        .filter(row => row.status !== 'DONE')
        .slice(0, 20);

    if (unfinished.length === 0) {
        console.log('All processed! Great job.');
    } else {
        console.table(unfinished);
    }
}

scan();
