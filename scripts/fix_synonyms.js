const fs = require('fs');
const path = require('path');

const taggedDir = 'note_tagged';
const files = fs.readdirSync(taggedDir);

// Define standard synonyms mapping
const synonymMap = {
    // 数据库 & 索引
    'b+ tree': 'b+树',
    'b+tree': 'b+树',
    'red-black tree': '红黑树',
    'slow query': '慢查询',
    'distributed lock': '分布式锁',
    'rate limiting': '限流',
    'garbage collection': 'gc',
    'memory leak': '内存泄漏',
    'concurrency control': '并发控制',
    'optimistic lock': '乐观锁',
    'pessimistic lock': '悲观锁',
    'read/write lock': '读写锁',
    'thread pool': '线程池',
    'message queue': '消息队列',
    'design pattern': '设计模式',
    'virtual memory': '虚拟内存',
    'page replacement': '页面置换',
    'two pointers': '双指针',
    'linked list': '链表',
    'reverse linked list': '链表反转',
    'hash map': 'hashmap',
    'binary tree': '二叉树',
    'dynamic programming': '动态规划',
    'dp': '动态规划',
    'backtracking': '回溯算法',
    'stack': '栈',
    'queue': '队列',
    'microservices': '微服务',
    'service discovery': '服务注册与发现',
    'circuit breaker': '熔断降级',
    'bloom filter': '布隆过滤器'
};

function normalizeEntity(entity) {
    if (typeof entity !== 'string') return entity;
    const lower = entity.toLowerCase();

    // Exact synonym match
    if (synonymMap[lower]) {
        return synonymMap[lower];
    }

    return entity;
}

function normalizeArray(arr) {
    if (!Array.isArray(arr)) return arr;
    let changed = false;
    const newArr = arr.map(e => {
        const normalized = normalizeEntity(e);
        if (normalized !== e) {
            changed = true;
        }
        return normalized;
    });

    if (changed) {
        // deduplicate
        return [...new Set(newArr)];
    }
    return arr;
}

let updatedNotes = 0;
console.log('1. Processing note_tagged files for synonyms...');

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

console.log('\n2. Processing hashmap_slim.json for synonyms...');
// We use the same robust regeneration script logic to ensure consistency
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
console.log('\n🎉 Finished standardizing synonyms!');
