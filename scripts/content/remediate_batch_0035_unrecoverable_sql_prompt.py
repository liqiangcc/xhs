#!/usr/bin/env python3
"""Retire batch-0035 SQL singleton whose executable contract is not recoverable.

The source description only says the interviewer asked the candidate to "写sql" and
the tagged projection says "写SQL题目".  No schema, rows, requested result, filter,
join, grouping, ordering, SQL dialect, or examples survive.  A strict-valid Coding
answer cannot be reconstructed without inventing the missing problem.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil

ROOT=Path('.')
CANONICAL_ID='cq_q_82b0328e96bc4a148f49b73e6ff2dbd2'
EXPECTED='写SQL题目'
SOURCE_NOTE_ID='67d3dbe1000000001b024087'
SOURCE_NOTE=ROOT/f'note_tagged/{SOURCE_NOTE_ID}.json'
SOURCE_DESC=ROOT/f'note_desc/{SOURCE_NOTE_ID}.txt'
EXPLANATION=(
    '来源正文只保留“面试官就让写sql”，tagged note 仅归一为“写SQL题目”。'
    '没有保存表结构、字段、样例数据、要查询的结果、过滤条件、关联关系、聚合/窗口要求、排序、SQL 方言或边界样例。'
    '这些缺失信息决定 SQL 的结果粒度、JOIN、WHERE/HAVING、GROUP BY、窗口函数以及正确性验证；'
    '不能为了满足 Answer 覆盖自行编造一道常见 SQL 题。'
    '在获得更强原始来源前，该 singleton 无法恢复 strict-valid Coding 答案，应以可解释的 incomplete_or_unreadable 记录 fail-closed。'
)

def read_json(p): return json.loads(p.read_text(encoding='utf-8'))
def write_json(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read_jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_jsonl(p,rows): p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')

def main():
    tagged=read_json(SOURCE_NOTE)
    tagged_rows=[x for x in tagged.get('tagged_questions',[]) if x.get('original_question')==EXPECTED]
    if len(tagged_rows)!=1: raise SystemExit(f'exact tagged source wording missing/drifted: {len(tagged_rows)}')
    if tagged_rows[0].get('question_type')!='算法手撕_Coding': raise SystemExit(f"source type drifted: {tagged_rows[0].get('question_type')}")
    desc=SOURCE_DESC.read_text(encoding='utf-8')
    if '让写sql' not in desc.lower(): raise SystemExit('source description no longer preserves the generic SQL mention')

    cp=ROOT/'data/questions/canonical_questions.jsonl'; qp=ROOT/'data/questions/questions.jsonl'; pp=ROOT/'review/progress.json'; ap=ROOT/'config/question_validity_audit.json'
    canon=read_jsonl(cp); questions=read_jsonl(qp); progress=read_json(pp); audit=read_json(ap)
    c=next((x for x in canon if x.get('canonical_id')==CANONICAL_ID),None)
    if c is None:
        if any(x.get('canonical_id')==CANONICAL_ID for x in questions): raise SystemExit('canonical missing while active Question binding remains')
        if (ROOT/'review/answers'/f'{CANONICAL_ID}.md').exists(): raise SystemExit('canonical missing while active Answer remains')
        if any(x.get('canonical_id')==CANONICAL_ID for x in progress.get('items',[])): raise SystemExit('canonical missing while ReviewProgress remains')
        print('already retired'); return 0
    qids=list(c.get('question_ids') or [])
    if len(qids)!=1 or int(c.get('frequency',0))!=1: raise SystemExit(f"not singleton: {qids} frequency={c.get('frequency')}")
    qid=qids[0]
    rows=[x for x in questions if x.get('question_id')==qid]
    if len(rows)!=1: raise SystemExit(f'expected one Question row for {qid}, got {len(rows)}')
    row=rows[0]
    if row.get('canonical_id')!=CANONICAL_ID or row.get('is_valid_for_library') is not True: raise SystemExit('Question ownership/validity drifted')
    if row.get('original_question')!=EXPECTED or row.get('source_note_id')!=SOURCE_NOTE_ID: raise SystemExit(f'Question source projection drifted: {row}')

    ref=(row['source_note_id'],row['source_question_index'])
    replacement={'source_note_id':row['source_note_id'],'source_question_index':row['source_question_index'],'question_id':qid,'original_question':row['original_question'],'decision':'exclude','exclusion_reason':'incomplete_or_unreadable','exclusion_note':EXPLANATION}
    decisions=list(audit.get('decisions',[])); found=False
    for i,d in enumerate(decisions):
        if (d.get('source_note_id'),d.get('source_question_index'))==ref:
            decisions[i]=replacement; found=True; break
    if not found: decisions.append(replacement)

    canon=[x for x in canon if x.get('canonical_id')!=CANONICAL_ID]
    before=len(progress.get('items',[])); progress['items']=[x for x in progress.get('items',[]) if x.get('canonical_id')!=CANONICAL_ID]
    if len(progress['items'])!=before-1: raise SystemExit('expected one ReviewProgress item to retire')
    active=ROOT/'review/answers'/f'{CANONICAL_ID}.md'; archived=ROOT/'review/archive/answers'/f'{CANONICAL_ID}.md'
    if not active.exists(): raise SystemExit('active long-tail Answer missing')
    archived.parent.mkdir(parents=True,exist_ok=True)
    if archived.exists():
        if archived.read_bytes()!=active.read_bytes(): raise SystemExit('archive differs from active Answer')
        active.unlink()
    else: shutil.move(str(active),str(archived))
    if (ROOT/'review/candidates/answers'/f'{CANONICAL_ID}.md').exists(): raise SystemExit('unexpected candidate exists')

    decisions.sort(key=lambda d:(str(d.get('source_note_id','')),int(d.get('source_question_index',0))))
    audit['decisions']=decisions; audit['audited_at']='2026-08-26'; audit['include_count']=sum(d.get('decision')=='include' for d in decisions); audit['exclude_count']=sum(d.get('decision')=='exclude' for d in decisions)
    write_json(ap,audit); write_jsonl(cp,sorted(canon,key=lambda x:x['canonical_id'])); progress['updated_at']='2026-08-26'; progress['items']=sorted(progress.get('items',[]),key=lambda x:x.get('canonical_id','')); write_json(pp,progress)
    print(f'Retired source-unrecoverable SQL singleton: {CANONICAL_ID} question={qid}')
    return 0

if __name__=='__main__': raise SystemExit(main())
