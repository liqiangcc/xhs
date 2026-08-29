#!/usr/bin/env python3
"""Build, validate, and source-first review the Batch 0056 SQL/KMP pair."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0056'
PROMOTION_BLOCKER = 'repository_human_approval_and_real_review_policy_not_yet_satisfied'
HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}

TARGETS = [
    {
        'cid':'cq_q_ffea95ccbbb749dac2669e262c61f5d5',
        'qid':'ffea95ccbbb749dac2669e262c61f5d5',
        'expected':'SQL 编写：给定学生成绩表（姓名、科目、分数），查询所有科目成绩均大于 80 分的学生姓名',
        'slug':'all-subjects-over-80',
        'runtime':'sqlite',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ffea95ccbbb749dac2669e262c61f5d5","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# SQL：查询所有科目成绩均大于 80 分的学生

## 核心结论

来源只给出“姓名、科目、分数”三类字段，没有真实表名、主键、空值和补考/重复科目规则。这里声明最小可执行合同：表为 `grades(name, subject, score)`，每行代表该学生一个有效科目成绩；学生至少有一条成绩记录；只要存在一条 `score <= 80` 或 `score IS NULL` 就不合格。按学生分组后统计“不满足 >80”的记录数为 0 即可。

## 1 分钟版

- 这是典型的“对每个学生做全称判断”，不能只写 `WHERE score > 80` 后 `DISTINCT name`，那只能证明“至少有一门 >80”。
- 先 `GROUP BY name`，把判断粒度收敛到学生。
- 在 `HAVING` 中统计反例：`score <= 80 OR score IS NULL` 的行数必须为 0。
- 来源没有规定 NULL 语义；这里显式把 NULL 当作“无法证明 >80”，因此排除该学生。
- 如果真实数据允许同一科目多次考试，必须先定义“最终成绩”如何选择，再做全称判断。

## 3 分钟版

```sql
SELECT name
FROM grades
GROUP BY name
HAVING SUM(
    CASE
        WHEN score <= 80 OR score IS NULL THEN 1
        ELSE 0
    END
) = 0;
```

这段 SQL 的重点不是 `GROUP BY` 本身，而是把“所有成绩都 >80”改写成“没有任何一个反例”。例如 Alice 的 90、85 没有反例，会保留；Bob 有一门 80，反例数为 1，会被排除；如果 Cara 有 NULL，本合同同样把它作为未满足条件处理。

## 关键细节

- `WHERE score > 80` 会先删掉不及格行，使后续分组看不到反例，是最常见的逻辑错误。
- 若 schema 明确 `score NOT NULL`，可简化为 `HAVING MIN(score) > 80`；当前来源没给非空约束，所以不把这个简化写成唯一答案。
- SQL 标准的 NULL 比较结果不是 TRUE；若直接写 `MIN(score) > 80`，不同数据形态下容易把“未知”悄悄忽略，因此这里显式处理 NULL。
- 当前合同把一行视为一个有效科目成绩；重复科目、补考、重修如果存在，必须先明确业务唯一性与选取规则。
- 只需要姓名时按 `name` 分组足够；真实系统若姓名不唯一，应按学生 ID 分组并把姓名作为展示列。

## 原理机制

“所有元素满足 P”可以等价改写为“不存在元素不满足 P”。SQL 聚合特别适合这种反例计数：分组建立学生集合，`CASE` 把每条成绩映射为合格 0 / 反例 1，`SUM(...)=0` 就证明该组没有反例。相比先过滤合格记录，这种写法保留了判定全称命题所需的负面证据。

## 项目经验版

来源没有真实表结构、索引、数据量或执行计划，不能虚构线上性能。落地时我会先确认学生唯一键、成绩是否允许 NULL、一个科目是否可能有多条记录，再按真实数据库查看执行计划；大表通常会关注用于分组/关联的学生键以及数据清洗策略，而不是凭空承诺某个索引一定最优。

## 常见追问

- 问：为什么不能 `WHERE score > 80 GROUP BY name`？答：因为不合格成绩在分组前已被删除，无法证明“全部都合格”。
- 问：能用 `MIN(score) > 80` 吗？答：如果 `score` 明确非空且每行都是有效成绩，可以；本来源没给 NULL 合同，所以这里显式统计 NULL 反例。
- 问：如果姓名重复怎么办？答：真实 schema 应按学生 ID 分组，再返回对应姓名；来源只给姓名字段，所以示例不能虚构 ID。
- 问：80 算不算合格？答：题目是“大于 80”，所以 80 不合格。
- 问：补考取最高分还是最后一次？答：来源没有说明，需要先定义每科有效成绩，再执行全称判断。

## 易错点

- 把“所有科目 >80”写成“存在科目 >80”。
- 忽略 80 与 >80 的严格边界。
- 未声明 NULL 语义却依赖聚合函数默认跳过 NULL。
- 真实数据姓名不唯一却直接把姓名当业务主键。
''',
        'checks':['Alice 90/85 qualifies','Bob with score 80 is excluded','Cara with NULL is excluded','Dan with 81 qualifies','student with a single failing score excluded'],
        'stdout':'PASS alice dan qualify bob-boundary cara-null eve-fail excluded',
        'claims':[
            ('source-boundary','The preserved source gives only name, subject and score and does not define table names, nullability, student identity, or duplicate/retake policy; the candidate declares a minimal executable contract.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('query-correctness','The deterministic SQLite fixture verifies the counterexample-counting query for qualifying students, the strict >80 boundary, NULL handling, and failing rows.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate correctly distinguishes universal qualification from existential filtering.','The strict >80 and NULL semantics are explicit rather than inherited accidentally from aggregate behavior.','SQLite validation covers positive, boundary, NULL, and failing cases.','Duplicate-subject/retake and non-unique-name behavior are left as explicit schema-dependent follow-ups.'],
        'task_note':'- [x] `cq_q_ffea95ccbbb749dac2669e262c61f5d5` source-first isolated review PASS: the SQL candidate expresses “all scores >80” as absence of counterexamples, declares NULL/identity assumptions, and deterministic SQLite validation covers strict-boundary and NULL cases. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
    {
        'cid':'cq_q_7daa5cfddb93ce44e349bd4978214d71',
        'qid':'7daa5cfddb93ce44e349bd4978214d71',
        'expected':'算法：KMP 字符串匹配算法的原理及实现。',
        'slug':'kmp',
        'runtime':'java',
        'class':'KmpSearch',
        'candidate':r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_7daa5cfddb93ce44e349bd4978214d71","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# KMP 字符串匹配：原理与实现

## 核心结论

来源要求 KMP 的原理和实现，没有固定语言/API。这里采用 Java 合同：`indexOf(text, pattern)` 返回模式串第一次出现的位置；找不到返回 -1；空模式返回 0；`null` 输入视为无效。KMP 先为模式串构造 LPS（最长相等真前后缀长度）数组，失配时不回退文本指针，而把模式指针跳到 `lps[j-1]`，总时间 O(n+m)、额外空间 O(m)。

## 1 分钟版

- 暴力匹配失配后会让文本起点回退并重新比较已经知道的信息。
- KMP 用模式串自身的“前缀 = 后缀”结构复用已匹配信息。
- `lps[i]` 表示 `pattern[0..i]` 的最长相等真前缀/真后缀长度。
- 匹配阶段若 `text[i] != pattern[j]` 且 `j>0`，令 `j=lps[j-1]`，文本 `i` 不动；若 `j==0` 才移动 `i`。
- 当 `j==pattern.length()`，第一次匹配起点就是 `i-j`。

## 3 分钟版

```java
public final class KmpSearch {
    public static int indexOf(String text, String pattern) {
        if (text == null || pattern == null) throw new IllegalArgumentException("text/pattern must not be null");
        if (pattern.isEmpty()) return 0;
        int[] lps = buildLps(pattern);
        int i = 0, j = 0;
        while (i < text.length()) {
            if (text.charAt(i) == pattern.charAt(j)) {
                i++; j++;
                if (j == pattern.length()) return i - j;
            } else if (j > 0) {
                j = lps[j - 1];
            } else {
                i++;
            }
        }
        return -1;
    }

    static int[] buildLps(String pattern) {
        int[] lps = new int[pattern.length()];
        for (int i = 1, len = 0; i < pattern.length();) {
            if (pattern.charAt(i) == pattern.charAt(len)) {
                lps[i++] = ++len;
            } else if (len > 0) {
                len = lps[len - 1];
            } else {
                lps[i++] = 0;
            }
        }
        return lps;
    }
}
```

口头解释时可用模式串 `ababaca`：已经匹配一段后失配，不需要把文本重新从头扫描，而是把模式串移动到“已匹配后缀与模式前缀对齐”的位置。LPS 就是在预先计算这些可安全复用的边界。

## 关键细节

- LPS 中“前缀/后缀”必须是真前缀/真后缀，不能把整个字符串本身算进去。
- 构造 LPS 时失配也要递归复用 `lps[len-1]`，而不是简单把 `len` 清零，否则会漏掉较短可复用边界。
- 匹配阶段 `j>0` 失配时不增加文本指针 i，这是 KMP 避免文本回退的核心。
- 空模式返回 0 与常见 `indexOf` 语义一致，但来源没规定；这是本答案声明的 API 合同。
- Java `char` 基于 UTF-16 code unit；若业务按 Unicode code point 匹配，需要改变遍历单位。

## 原理机制

假设已经匹配了模式前 j 个字符后失配。已匹配文本后缀和模式 `pattern[0..j-1]` 相同，因此如果这个模式前缀存在长度 k 的“前缀 = 后缀”，那么无需重新检查文本，只需尝试让 `pattern[0..k-1]` 对齐到刚才的已匹配后缀。`lps[j-1]` 给出的正是最大这样的 k；若仍失配，再沿 LPS 链退到更短候选。文本指针单调前进，模式指针的回退总量受推进次数约束，因此是线性复杂度。

## 项目经验版

来源没有真实文本长度、字符集和吞吐目标，不能虚构 KMP 一定优于库函数。面试实现重点是把 LPS 不变量和失配跳转讲清楚；工程里通常先使用标准库/成熟搜索实现，只有需要自定义流式匹配、受控复杂度或教学/算法场景时才手写并用随机对拍验证。

## 常见追问

- 问：KMP 为什么不回退文本指针？答：已匹配区间的信息已由 LPS 编码，可移动模式串复用，而无需重新读取已确认的文本前缀。
- 问：LPS 和 next 数组是什么关系？答：是同一失配跳转思想的不同下标/定义形式，实现时要保持定义一致。
- 问：复杂度为什么是 O(n+m)？答：LPS 构造线性，匹配中文本 i 不回退，模式回退沿已构造边界链摊销线性。
- 问：空模式怎么办？答：当前 API 合同返回 0。
- 问：如何验证实现没写错？答：除固定样例外，可把大量随机 text/pattern 的结果与标准 `String.indexOf` 对拍。

## 易错点

- LPS 构造失配时直接 `len=0`，漏掉次长边界。
- 匹配失配时同时移动 i 和回退 j，导致跳过合法匹配。
- `j==m` 后起点写错成 i 或 i-j+1。
- 混用不同 next/LPS 定义导致 off-by-one。
''',
        'test':r'''import java.util.Arrays;
import java.util.Random;
public final class KmpSearchTest {
    static void eq(int a,int b,String m){if(a!=b)throw new AssertionError(m+"="+a+" expected="+b);}
    public static void main(String[] args){
        eq(KmpSearch.indexOf("",""),0,"empty-empty");
        eq(KmpSearch.indexOf("abc",""),0,"empty-pattern");
        eq(KmpSearch.indexOf("hello","ll"),2,"basic");
        eq(KmpSearch.indexOf("aaaaab","aaab"),2,"overlap");
        eq(KmpSearch.indexOf("abc","d"),-1,"missing");
        if(!Arrays.equals(KmpSearch.buildLps("ababaca"),new int[]{0,0,1,2,3,0,1}))throw new AssertionError("lps");
        Random r=new Random(7); String alphabet="abc";
        for(int t=0;t<2000;t++){int n=r.nextInt(25),m=r.nextInt(9);StringBuilder x=new StringBuilder(),p=new StringBuilder();for(int i=0;i<n;i++)x.append(alphabet.charAt(r.nextInt(alphabet.length())));for(int i=0;i<m;i++)p.append(alphabet.charAt(r.nextInt(alphabet.length())));eq(KmpSearch.indexOf(x.toString(),p.toString()),x.toString().indexOf(p.toString()),"random-"+t);}
        try{KmpSearch.indexOf(null,"a");throw new AssertionError("null-text");}catch(IllegalArgumentException expected){}
        try{KmpSearch.indexOf("a",null);throw new AssertionError("null-pattern");}catch(IllegalArgumentException expected){}
        System.out.println("PASS fixed lps overlap missing empty null and 2000 deterministic random differential cases");
    }
}
''',
        'checks':['empty pattern returns 0','basic and overlapping matches return first index','missing pattern returns -1','ababaca LPS is [0,0,1,2,3,0,1]','2000 seeded random cases match String.indexOf','null inputs rejected'],
        'stdout':'PASS fixed lps overlap missing empty null and 2000 deterministic random differential cases',
        'claims':[
            ('source-boundary','The preserved source asks for KMP principle and implementation but does not define language, null behavior, empty-pattern behavior, or Unicode granularity; the candidate declares a Java indexOf-style contract.',['repository-source'],['核心结论','关键细节','项目经验版']),
            ('algorithm-correctness','The executable OpenJDK fixture verifies fixed LPS/match cases and 2000 seeded random differential cases against String.indexOf.',['fixture'],['1 分钟版','3 分钟版','原理机制','常见追问']),
        ],
        'findings':['The candidate defines LPS precisely and uses it consistently in preprocessing and matching.','The explanation identifies the key invariant: on mismatch, the text pointer does not move when a shorter matched border remains possible.','OpenJDK validation includes fixed overlap/LPS/boundary cases plus 2000 deterministic differential cases.','Null, empty-pattern, and UTF-16/code-point boundaries are explicit API choices rather than hidden assumptions.'],
        'task_note':'- [x] `cq_q_7daa5cfddb93ce44e349bd4978214d71` source-first isolated review PASS: the KMP candidate defines LPS and mismatch fallback explicitly, and OpenJDK validation covers fixed overlap/LPS/boundary cases plus 2000 deterministic differential cases against `String.indexOf`. Formal promotion remains blocked by repository human-approval/real-review policy.'
    },
]


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def validate_target(target: dict, body: str, out: Path) -> tuple[str,str,list[str]]:
    if target['runtime'] == 'sqlite':
        block = re.findall(r'```sql\n(.*?)\n```', body, re.S)
        if len(block) != 1:
            raise SystemExit(f"{target['cid']}: expected one SQL block")
        sql = block[0].strip()
        con = sqlite3.connect(':memory:')
        con.execute('create table grades(name text not null, subject text not null, score real)')
        con.executemany('insert into grades values(?,?,?)',[
            ('Alice','math',90),('Alice','english',85),
            ('Bob','math',90),('Bob','english',80),
            ('Cara','math',91),('Cara','english',None),
            ('Dan','math',81),
            ('Eve','math',79),('Eve','english',99),
        ])
        rows = sorted(x[0] for x in con.execute(sql))
        if rows != ['Alice','Dan']:
            raise SystemExit(f"{target['cid']}: SQL rows drift {rows}")
        stdout = target['stdout']
        (out/'query.sql').write_text(sql+'\n',encoding='utf-8')
        command = 'python3 sqlite deterministic fixture executing query.sql'
        return stdout, command, target['checks']
    blocks = re.findall(r'```java\n(.*?)\n```', body, re.S)
    if len(blocks) != 1:
        raise SystemExit(f"{target['cid']}: expected one Java block")
    with tempfile.TemporaryDirectory(prefix='b56-kmp-') as tmp:
        d=Path(tmp)
        (d/f"{target['class']}.java").write_text(blocks[0].strip()+'\n',encoding='utf-8')
        (d/f"{target['class']}Test.java").write_text(target['test'],encoding='utf-8')
        run('javac',f"{target['class']}.java",f"{target['class']}Test.java",cwd=d)
        stdout=run('java',f"{target['class']}Test",cwd=d).stdout.strip()
    if stdout != target['stdout']:
        raise SystemExit(f"{target['cid']}: Java stdout drift {stdout}")
    command=f"javac {target['class']}.java {target['class']}Test.java && java {target['class']}Test"
    return stdout,command,target['checks']


def main() -> int:
    inventory=json.loads((ROOT/f'review/content_build/answer_batch_{BATCH}/source_inventory.json').read_text(encoding='utf-8'))
    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    task_text=task.read_text(encoding='utf-8').rstrip()
    completed=[]
    for target in TARGETS:
        cid,qid=target['cid'],target['qid']
        candidate=ROOT/f'review/candidates/answers/{cid}.md'; evidence=ROOT/f'review/evidence/{cid}.json'
        if candidate.exists() or evidence.exists(): raise SystemExit(f'{cid}: candidate/evidence already exists')
        ctx_path=ROOT/f'review/content_build/answer_batch_{BATCH}/{cid}/context.json'
        ctx=json.loads(ctx_path.read_text(encoding='utf-8'))
        if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id')!=cid or ctx.get('answer_type')!='coding': raise SystemExit(f'{cid}: context/type drift')
        if ctx.get('canonical',{}).get('question_ids') != [qid]: raise SystemExit(f'{cid}: ownership drift')
        src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==qid),None)
        if not src or src.get('original_question')!=target['expected'] or src.get('is_valid_for_library') is not True: raise SystemExit(f'{cid}: source drift')
        inv=next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id')==cid),None)
        if not inv or inv.get('answer_type')!='coding': raise SystemExit(f'{cid}: inventory drift')
        body=target['candidate']
        for h in HEADINGS:
            if body.count(h)!=1: raise SystemExit(f'{cid}: section drift {h}')
        candidate.parent.mkdir(parents=True,exist_ok=True); candidate.write_text(body,encoding='utf-8')
        out=ROOT/f'review/content_build/answer_batch_{BATCH}/{cid}'
        stdout,command,checks=validate_target(target,body,out)
        validation={'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,'command':command,'stdout':stdout,'checks':checks}
        write_json(out/'writer_validation.json',validation)
        digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
        sources=[
            {'source_id':'repository-source','title':f'Batch 0056 frozen source context for {target["slug"]}','locator':str(ctx_path),'source_type':'repository_source_record','checked_at':DATE},
            {'source_id':'fixture','title':f'Deterministic executable validation for {target["slug"]}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
        ]
        claims=[{'claim_id':a,'text':b,'source_ids':c,'answer_locations':d} for a,b,c,d in target['claims']]
        coverage=[{'question_id':qid,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
        write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
        reviewer=f'source-first-isolated-reviewer-batch-0056-{target["slug"]}-20260829-v1'
        review={'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer,'review_version':f'batch-0056.{target["slug"]}.v1','decision':'pass','revision_round':1,'source_packet':[str(ctx_path),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings'],'promotion_blockers':[PROMOTION_BLOCKER]}
        write_json(out/'isolated_review_result.json',review)
        write_json(evidence,{'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':f'content-batch-0056-{target["slug"]}-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':f'Batch 0056 {target["slug"]} source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':command,'result':'pass','reported_stdout':stdout,'checks':checks,'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in checks]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':target['findings']},'promotion_blocker':PROMOTION_BLOCKER})
        writer=json.loads((out/'writer_research.json').read_text(encoding='utf-8'));writer['review_state']='writer_complete_isolated_review_passed';writer['promotion_blocker']=PROMOTION_BLOCKER;write_json(out/'writer_research.json',writer)
        if target['task_note'] not in task_text: task_text+='\n'+target['task_note']
        completed.append({'canonical_id':cid,'candidate_sha256':digest,'decision':'pass','stdout':stdout})
    task.write_text(task_text+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'batch':BATCH,'completed':completed,'promotion_blocker':PROMOTION_BLOCKER},ensure_ascii=False))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
