from pathlib import Path

p=Path('scripts/lib/answer_quality.js')
s=p.read_text(encoding='utf-8')
old="if (options['require-code'] && !/(?:```|~~~)(?:java|sql|javascript|js|go|c|cpp|c\\+\\+|cc|cxx)(?:\\s|$)/i.test(answer.content)) return false;"
new="if (options['require-code'] && !/(?:```|~~~)(?:java|sql|javascript|js|go|c|cpp|c\\+\\+|cc|cxx|bash|sh|shell)(?:\\s|$)/i.test(answer.content)) return false;"
if old not in s:
    raise SystemExit('require-code selection regex drifted')
s=s.replace(old,new,1)
p.write_text(s,encoding='utf-8')

t=Path('test/answer_candidate.test.js')
x=t.read_text(encoding='utf-8')
marker="\ntest('require-code accepts and compiles a Go coding candidate', () => {"
test=r'''

test('require-code selects and validates a Bash coding candidate', () => {
    const root = fs.mkdtempSync(path.join(os.tmpdir(), 'xhs-answer-bash-candidate-'));
    writeJson(path.join(root, 'config', 'answer_quality.json'), QUALITY);
    writeJsonl(path.join(root, 'data', 'questions', 'canonical_questions.jsonl'), [{
        schema_version: 'canonical_question.v1', canonical_id: 'cq_bash', canonical_title: '统计 URL 次数',
        aliases: [], question_ids: ['q-bash'], primary_domain: { l1: 'Linux', l2: 'Shell' }, primary_entities: ['awk','sort','uniq'],
        companies: [], frequency: 1, review_priority: 'P0', answer_status: 'needs_update',
    }]);
    writeJsonl(path.join(root, 'data', 'questions', 'questions.jsonl'), [{ question_id: 'q-bash', canonical_id: 'cq_bash', original_question: '统计 URL 次数', question_type: 'coding' }]);
    const candidateDir = path.join(root, 'review', 'candidates', 'answers'); ensureDir(candidateDir);
    const candidatePath = path.join(candidateDir, 'cq_bash.md');
    const sections = ['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','项目经验版','常见追问','易错点'];
    const lines=['<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_bash","version":1,"status":"draft","quality_tier":"candidate","answer_type":"coding","updated_at":"2026-08-27"} -->','# 统计 URL 次数'];
    for(const title of sections){ lines.push('',`## ${title}`,''); if(title==='3 分钟版') lines.push('```bash',"awk 'NF {print $0}' urls.txt | sort | uniq -c",'```'); else if(title==='常见追问') lines.push('- 问：为什么排序？答：让重复 URL 相邻。','- 问：空行？答：过滤。','- 问：query？答：按完整字符串。'); else lines.push(`${title}的 awk sort uniq 专属内容。`); }
    fs.writeFileSync(candidatePath,`${lines.join('\n')}\n`,'utf8');
    const evidenceDir=path.join(root,'review','evidence'); ensureDir(evidenceDir);
    writeJson(path.join(evidenceDir,'cq_bash.json'),{schema_version:'answer_evidence.v1',canonical_id:'cq_bash',candidate_sha256:require('crypto').createHash('sha256').update(fs.readFileSync(candidatePath)).digest('hex'),sources:[],claims:[],source_question_coverage:[{question_id:'q-bash',covered:true,answer_locations:['核心结论']}],validation:{boundary_tests:[{case:'duplicates',passed:true},{case:'blank',passed:true},{case:'query',passed:true}]},review:{independent:true,reviewer_id:'reviewer',decision:'pass',scores:{facts_and_evidence:25,directness_and_relevance:20,type_specific_completeness:20,mechanism_and_causality:15,boundaries_and_tradeoffs:10,followup_quality:5,oral_quality:5}}});
    const report=runAnswerAudit({root,candidate:candidatePath,noWrite:true,'require-code':true,'require-evidence':true});
    assert.equal(report.candidate_count,1);
    assert.equal(report.rows[0].errors.some((row)=>row.error==='coding_block_required'),false);
    fs.rmSync(root,{recursive:true,force:true});
});
'''
if marker not in x:
    raise SystemExit('answer candidate insertion marker drifted')
x=x.replace(marker,test+marker,1)
t.write_text(x,encoding='utf-8')
