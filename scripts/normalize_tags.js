/**
 * normalize_tags.js
 * 一次性规范化 note_tagged/ 中的 domain.l1、question_type、cognitive_depth 字段。
 *
 * 用法:
 *   node scripts/normalize_tags.js              # dry-run，只打印统计
 *   node scripts/normalize_tags.js --apply      # 实际写入文件
 */

const fs = require('fs');
const path = require('path');

const APPLY = process.argv.includes('--apply');
const taggedDir = path.join(__dirname, '..', 'note_tagged');

// ============================================================
// 1. L1 Domain 规范化映射 （目标 ~15 个标准分类）
// ============================================================
const L1_MAP = {
    // --- Java ---
    'Java基础': 'Java',
    'Java开发': 'Java',
    'Java后端': 'Java',
    'Java架构': 'Java',
    '并发编程': 'Java',

    // --- Spring ---
    'Spring生态': 'Spring',
    '常用框架': 'Spring',
    '后端框架': 'Spring',

    // --- 数据库 ---
    '数据库': '数据库',
    '数据库/数仓': '数据库',
    '大数据': '数据库',
    '大数据技术': '数据库',
    '大数据/数仓': '数据库',

    // --- 缓存 & 中间件 ---
    '缓存': '中间件',
    '中间件': '中间件',
    '消息中间件': '中间件',
    '微服务与中间件': '中间件',
    '分布式系统 with 中间件': '中间件',
    '分布式系统 with 中件间': '中间件',
    '异步处理': '中间件',
    '微服务': '中间件',

    // --- 分布式系统 ---
    '分布式系统': '分布式系统',
    '分布式架构': '分布式系统',
    '分布式系统与架构': '分布式系统',
    '分布式服务': '分布式系统',
    '分布式': '分布式系统',
    '分布式开发': '分布式系统',

    // --- 系统设计 ---
    '系统设计': '系统设计',
    '架构设计': '系统设计',
    '架构': '系统设计',
    '架构设计与演进': '系统设计',
    '场景设计': '系统设计',
    '场景实践': '系统设计',
    '业务架构与实战': '系统设计',
    '业务架构 with 实战': '系统设计',
    '业务架构与實戰': '系统设计',
    '业务架构': '系统设计',
    '业务模型': '系统设计',
    '高可用': '系统设计',

    // --- 算法 ---
    '算法与数据结构': '算法',
    '数据结构与算法': '算法',
    '算法/数据结构': '算法',
    '算法': '算法',
    '数据结构': '算法',
    '算法 with 数据结构': '算法',
    '算法与数据望结构': '算法',

    // --- 计算机网络 ---
    '计算机网络': '计算机网络',
    '网络': '计算机网络',
    '网络协议': '计算机网络',
    '网络安全': '计算机网络',
    '计算机安全': '计算机网络',
    '计算网络': '计算机网络',
    '权限安全': '计算机网络',

    // --- 操作系统 ---
    '操作系统': '操作系统',
    '系统编程': '操作系统',
    '计算机体系结构': '操作系统',
    '计算机基础': '操作系统',
    '计算理论与基础': '操作系统',
    '计算机科学理论': '操作系统',
    '嵌入式': '操作系统',
    '内存管理': '操作系统',

    // --- 前端 ---
    '前端开发': '前端',
    '前端基础': '前端',
    '前端': '前端',
    '前端框架': '前端',
    '前端工程化': '前端',
    '前端技术': '前端',
    '全栈知识': '前端',

    // --- 云原生 & DevOps ---
    '云原生与工程化': '云原生/DevOps',
    '云原生': '云原生/DevOps',
    '云原生/DevOps': '云原生/DevOps',
    '云原生 with 工程化': '云原生/DevOps',
    '云计算': '云原生/DevOps',
    '运维/监控': '云原生/DevOps',
    '运维与部署': '云原生/DevOps',
    '运维/云原生': '云原生/DevOps',
    '计算资源与运维': '云原生/DevOps',
    '基础设施': '云原生/DevOps',

    // --- C/C++ ---
    'C/C++': 'C/C++',
    'C/C++基础': 'C/C++',
    'C++开发': 'C/C++',

    // --- Go ---
    'Go开发': 'Go',

    // --- AI ---
    'AI与大模型': 'AI/大模型',
    '人工智能': 'AI/大模型',
    'AI技术': 'AI/大模型',

    // --- 工程实践 / 软技能 ---
    '后端基础': '工程实践',
    '基础语言': '工程实践',
    '编程语言基础': '工程实践',
    '通用能力': '工程实践',
    '通用工程能力': '工程实践',
    '通用基础': '工程实践',
    '工程实践': '工程实践',
    '开发工具': '工程实践',
    '开发工具/规范': '工程实践',
    '研发通用': '工程实践',
    '设计模式': '工程实践',
    '软件工程': '工程实践',
    '软件工程与设计模式': '工程实践',
    '软件工程 with 设计模式': '工程实践',
    '软件测试': '工程实践',
    '协同与治理': '工程实践',
    '后端开发': '工程实践',

    // --- 其他 ---
    '其他': '其他',
    '其他语言': '其他',
    '其他技术': '其他',
    '项目经验': '其他',
    '项目经历': '其他',
    '求职综合': '其他',
    '通用面试': '其他',
    '非技术性': '其他',
    '团队协作': '其他',
};

// ============================================================
// 2. Question Type 规范化映射 （目标 ~10 个标准分类）
// ============================================================
const TYPE_MAP = {
    // Concept
    '八股文_Concept': '八股文_Concept',
    '八稿文_Concept': '八股文_Concept',  // typo fix

    // UnderTheHood
    '原理深度_UnderTheHood': '原理深度_UnderTheHood',
    '数据库深挖': '原理深度_UnderTheHood',
    '分布式深挖': '原理深度_UnderTheHood',

    // Scenario / Design
    '场景设计_Scenario': '场景设计_Scenario',
    '从场景方案_DesignPattern': '场景设计_Scenario',
    '方案设计': '场景设计_Scenario',
    '系统设计_Architecture': '系统设计_Architecture',
    '架构设计_Architecture': '系统设计_Architecture',
    '架构设计_Design': '系统设计_Architecture',
    '架构设计_System': '系统设计_Architecture',
    '设计模式_Pattern': '系统设计_Architecture',
    '业务架构_BizArch': '系统设计_Architecture',

    // Coding
    '算法手撕_Coding': '算法手撕_Coding',
    '代码手撕_Coding': '算法手撕_Coding',
    '手撕代码_Coding': '算法手撕_Coding',
    '算法实现_Algorithm': '算法手撕_Coding',
    '算法题_Algorithm': '算法手撕_Coding',
    '算法实现_Implementation': '算法手撕_Coding',
    '代码预测_Output': '算法手撕_Coding',
    '脚本题_Puzzle': '算法手撕_Coding',

    // Project
    '项目深挖_Project': '项目深挖_Project',
    '项目深挖_ProjectDeepDive': '项目深挖_Project',
    '项目实践_Experience': '项目深挖_Project',

    // Experience & Behavioral
    '面经分享_Experience': '经验思考_Reflection',
    '经验思考_Reflection': '经验思考_Reflection',
    '行为软技_Behavioral': '行为软技_Behavioral',
    '软素质_SoftSkills': '行为软技_Behavioral',
    '职业意识': '行为软技_Behavioral',
    '通用业务_GeneralBusiness': '行为软技_Behavioral',
    '业务背景_Business': '行为软技_Behavioral',

    // Ops
    '工具使用_Tooling': '工具使用_Tooling',
    '日常排障_TroubleShooting': '工具使用_Tooling',
    '性能调优_Tuning': '工具使用_Tooling',
    '研发规范_Specification': '工具使用_Tooling',

    // Other
    '其他': '其他_Other',
    '其他_Other': '其他_Other',
    '智力题_Brainteaser': '其他_Other',
    '智力题_Puzzle': '其他_Other',
    '逻辑智力_Puzzles': '其他_Other',
};

// ============================================================
// 3. Cognitive Depth 规范化映射
// ============================================================
const DEPTH_MAP = {
    'L1_Principle': 'L1_Principle',
    'L1_Mechanism': 'L1_Principle',
    'L2_Mechanism': 'L2_Mechanism',
    'L3_Diagnostic': 'L3_Diagnostic',
    'L3_Analysis': 'L3_Diagnostic',
    'L3_Optimization': 'L3_Diagnostic',
    'L3_Implementation': 'L3_Diagnostic',
    'L4_Evaluation': 'L3_Diagnostic',
    'N_A': 'N_A',
};

// ============================================================
// Execute
// ============================================================
const files = fs.readdirSync(taggedDir).filter(f => f.endsWith('.json'));

let totalFiles = 0;
let totalQuestions = 0;
let l1Changed = 0;
let typeChanged = 0;
let depthChanged = 0;
let l1Unknown = {};
let typeUnknown = {};
let depthUnknown = {};
let filesModified = 0;

files.forEach(f => {
    const filePath = path.join(taggedDir, f);
    const raw = fs.readFileSync(filePath, 'utf8');
    const j = JSON.parse(raw);
    totalFiles++;

    if (!j.tagged_questions || j.tagged_questions.length === 0) return;

    let modified = false;

    j.tagged_questions.forEach(q => {
        totalQuestions++;

        // Normalize L1
        if (q.domain && q.domain.l1) {
            const orig = q.domain.l1;
            if (L1_MAP[orig] !== undefined) {
                if (L1_MAP[orig] !== orig) {
                    q.domain.l1 = L1_MAP[orig];
                    l1Changed++;
                    modified = true;
                }
            } else {
                l1Unknown[orig] = (l1Unknown[orig] || 0) + 1;
            }
        }

        // Normalize question_type
        if (q.question_type) {
            const orig = q.question_type;
            if (TYPE_MAP[orig] !== undefined) {
                if (TYPE_MAP[orig] !== orig) {
                    q.question_type = TYPE_MAP[orig];
                    typeChanged++;
                    modified = true;
                }
            } else {
                typeUnknown[orig] = (typeUnknown[orig] || 0) + 1;
            }
        }

        // Normalize cognitive_depth
        if (q.cognitive_depth) {
            const orig = q.cognitive_depth;
            if (DEPTH_MAP[orig] !== undefined) {
                if (DEPTH_MAP[orig] !== orig) {
                    q.cognitive_depth = DEPTH_MAP[orig];
                    depthChanged++;
                    modified = true;
                }
            } else {
                depthUnknown[orig] = (depthUnknown[orig] || 0) + 1;
            }
        }
    });

    if (modified && APPLY) {
        fs.writeFileSync(filePath, JSON.stringify(j, null, 2) + '\n', 'utf8');
        filesModified++;
    } else if (modified) {
        filesModified++;
    }
});

// ============================================================
// Report
// ============================================================
console.log(`\n${'='.repeat(50)}`);
console.log(APPLY ? '  APPLY MODE — files have been updated' : '  DRY-RUN MODE — no files changed (use --apply)');
console.log(`${'='.repeat(50)}\n`);

console.log(`Total files scanned: ${totalFiles}`);
console.log(`Total questions scanned: ${totalQuestions}`);
console.log(`Files that would be modified: ${filesModified}\n`);

console.log('--- Domain L1 ---');
console.log(`  Normalized: ${l1Changed}`);
if (Object.keys(l1Unknown).length > 0) {
    console.log(`  UNKNOWN (not mapped):`);
    Object.entries(l1Unknown).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => {
        console.log(`    ${v}\t"${k}"`);
    });
}

console.log('\n--- Question Type ---');
console.log(`  Normalized: ${typeChanged}`);
if (Object.keys(typeUnknown).length > 0) {
    console.log(`  UNKNOWN (not mapped):`);
    Object.entries(typeUnknown).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => {
        console.log(`    ${v}\t"${k}"`);
    });
}

console.log('\n--- Cognitive Depth ---');
console.log(`  Normalized: ${depthChanged}`);
if (Object.keys(depthUnknown).length > 0) {
    console.log(`  UNKNOWN (not mapped):`);
    Object.entries(depthUnknown).sort((a, b) => b[1] - a[1]).forEach(([k, v]) => {
        console.log(`    ${v}\t"${k}"`);
    });
}

console.log('');
