const fs = require('fs');
const path = require('path');

const taggedDir = 'note_tagged';
const files = fs.readdirSync(taggedDir);

const synonymMap = {
    // 数据库 & 索引 & MySQL
    'b+ tree': 'b+树',
    'b+tree': 'b+树',
    'redo log': 'redo log', // unified lower
    'undo log': 'undo log',
    'binlog': 'binlog',
    'next-key lock': 'next-key lock',
    'slow query': '慢查询',
    'explain': 'explain',
    // 中间件相关
    'zookeeper': 'zookeeper',
    'elasticsearch': 'elasticsearch',
    'rocketmq': 'rocketmq',
    'kafka': 'kafka',
    'zset': 'zset',
    // 基础 & 语言
    'synchronized': 'synchronized',
    'volatile': 'volatile',
    'classloader': 'classloader',
    'hashtable': 'hashtable',
    'hash': 'hash',
    // 概念
    'redlock': 'redlock',
    'jstack': 'jstack',
    'top': 'top',
    'async': 'async',
    'service': 'service',
    'xss': 'xss',
    'epoll': 'epoll',
    'select': 'select',
    // 框架
    'spring boot': 'springboot',
    'spring mvc': 'springmvc',
    'spring cloud': 'springcloud',
    // 并发与集合 (高级合并)
    'threadpoolexecutor': '线程池',
    'concurrenthashmap': 'hashmap',
    'reentrantlock': '锁', // Optional: 锁 is a very broad category, but useful for aggregation
    'redis cluster': 'redis集群',
    'redis Sentinel': 'redis哨兵',
    // 旧的字典
    'red-black tree': '红黑树',
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
    if (typeof entity !== 'string' || !entity) return entity;

    let normalized = entity.trim();

    // 1. Remove parentheticals at the end
    normalized = normalized.replace(/\s*[（\(].*?[）\)]\s*$/, '');

    // 2. Remove leading/trailing special chars EXCEPT + and #
    normalized = normalized.replace(/^[^a-zA-Z0-9\u4e00-\u9fa5\+\#]+/, '');
    normalized = normalized.replace(/[^a-zA-Z0-9\u4e00-\u9fa5\+\#]+$/, '');

    // 3. To lower case for unification
    let lower = normalized.toLowerCase();

    // 4. Special internal punctuation map to fix stuff like ODS/DWD/DWS (we keep them but standardise)
    const mapping = {
        'tcp/ip': 'tcp',
        'http/https': 'http',
        'ssl/tls': 'https',
        'i/o': 'io',
        '磁盘i/o': '磁盘io',
        '网络i/o': '网络io',
        'c++': 'c++',
        'c#': 'c#',
        'b+树': 'b+树'
    };
    if (mapping[lower]) {
        return mapping[lower];
    }

    // 5. Synonym match
    if (synonymMap[lower]) {
        return synonymMap[lower];
    }

    // 6. If it wasn't caught by mapping, we'll just return the lowerCased version 
    // to strictly enforce NO casing inconsistencies anywhere.
    // E.g. "WebSocket" -> "websocket"
    if (normalized === '') return entity;

    return lower;
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
        return [...new Set(newArr.filter(Boolean))];
    }
    return arr;
}

let updatedNotes = 0;
console.log('1. Processing note_tagged files...');

files.forEach(f => {
    const filePath = path.join(taggedDir, f);
    const fileContent = fs.readFileSync(filePath, 'utf8');
    let d;
    try {
        d = JSON.parse(fileContent);
    } catch (e) {
        return;
    }

    let isNoteUpdated = false;

    if (d.tagged_questions) {
        d.tagged_questions.forEach(q => {
            if (q.tech_entities) {
                const normalized = normalizeArray(q.tech_entities);
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

console.log('\n2. Rebuilding hashmap_slim.json ...');
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
console.log('\n🎉 Finished ultimate data sweep!');
