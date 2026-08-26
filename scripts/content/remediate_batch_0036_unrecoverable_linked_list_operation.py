#!/usr/bin/env python3
"""Retire the batch-0036 generic linked-list-operation singleton fail-closed.

The primary image text preserves only the category-level phrase "链表操作" under
an algorithm section. It does not preserve which linked-list operation was asked,
its input/output representation, constraints, examples, or required behavior.
Generating a strict-valid Coding answer would therefore manufacture a problem.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil

ROOT=Path('.')
CANONICAL_ID='cq_q_863524333cd6488b996a811a4497ebdc'
QUESTION_ID='863524333cd6488b996a811a4497ebdc'
EXPECTED='算法：链表操作'
SOURCE_NOTE_ID='6826b6e6000000000303adfd'
SOURCE_NOTE=ROOT/f'note_tagged/{SOURCE_NOTE_ID}.json'
STRUCTURED_NOTE=ROOT/f'note_structured/{SOURCE_NOTE_ID}.json'
RAW_NOTE=ROOT/f'note_img_txt/{SOURCE_NOTE_ID}.txt'
EXPLANATION=(
    '原始图片文字在“七、算法题”下只保留“链表操作”，structured/tagged note 也没有保存更具体的操作。'
    '来源没有说明是反转、合并、删除、查找、判环、分组翻转或其他链表问题，也没有输入链表数量、节点结构、'
    '返回值、约束、样例或边界条件。不同解释会产生不同的输入输出契约、算法和正确性条件。'
    '当前全库对“链表操作”的有效 Question 近邻只有这一条，无法从另一份同源题面补回缺失合同；'
    '因此不能为满足覆盖而自行选择某个熟悉 LeetCode 链表题。获得更强原始来源前，该 singleton 无法形成 strict-valid Coding 答案，'
    '应以 incomplete_or_unreadable 可解释记录 fail-closed。'
)

def read_json(p): return json.loads(p.read_text(encoding='utf-8'))
def write_json(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read_jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_jsonl(p,rows): p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')

def main():
    tagged=read_json(SOURCE_NOTE)
    structured=read_json(STRUCTURED_NOTE)
    raw=RAW_NOTE.read_text(encoding='utf-8')
    q=next((x for x in tagged.get('tagged_questions',[]) if x.get('question_id')==QUESTION_ID),None)
    if not q or q.get('original_question')!=EXPECTED: raise SystemExit('exact tagged source wording missing/drifted')
    if q.get('question_type')!='算法手撕_Coding': raise SystemExit(f"source type drifted: {q.get('question_type')}")
    if EXPECTED not in (structured.get('questions') or []): raise SystemExit('structured source wording missing')
    if '七、算法题' not in raw or '3. 链表操作' not in raw: raise SystemExit('primary image text no longer preserves generic linked-list phrase')

    cp=ROOT/'data/questions/canonical_questions.jsonl'; qp=ROOT/'data/questions/questions.jsonl'; pp=ROOT/'review/progress.json'; ap=ROOT/'config/question_validity_audit.json'
    canon=read_jsonl(cp); questions=read_jsonl(qp); progress=read_json(pp); audit=read_json(ap)
    near=[x for x in questions if x.get('is_valid_for_library') is not False and '链表操作' in str(x.get('original_question',''))]
    if len(near)!=1 or near[0].get('question_id')!=QUESTION_ID: raise SystemExit(f'source-near neighborhood drifted: {[(x.get("question_id"),x.get("original_question")) for x in near]}')
    c=next((x for x in canon if x.get('canonical_id')==CANONICAL_ID),None)
    if c is None:
        if any(x.get('canonical_id')==CANONICAL_ID for x in questions): raise SystemExit('canonical missing while active Question binding remains')
        if (ROOT/'review/answers'/f'{CANONICAL_ID}.md').exists(): raise SystemExit('canonical missing while active Answer remains')
        if any(x.get('canonical_id')==CANONICAL_ID for x in progress.get('items',[])): raise SystemExit('canonical missing while ReviewProgress remains')
        print('already retired'); return 0
    if list(c.get('question_ids') or [])!=[QUESTION_ID] or int(c.get('frequency',0))!=1: raise SystemExit(f"not singleton: {c.get('question_ids')} frequency={c.get('frequency')}")
    rows=[x for x in questions if x.get('question_id')==QUESTION_ID]
    if len(rows)!=1: raise SystemExit(f'expected one Question row, got {len(rows)}')
    row=rows[0]
    if row.get('canonical_id')!=CANONICAL_ID or row.get('is_valid_for_library') is not True: raise SystemExit('Question ownership/validity drifted')
    if row.get('original_question')!=EXPECTED or row.get('source_note_id')!=SOURCE_NOTE_ID: raise SystemExit('Question source projection drifted')

    ref=(row['source_note_id'],row['source_question_index'])
    replacement={'source_note_id':row['source_note_id'],'source_question_index':row['source_question_index'],'question_id':QUESTION_ID,'original_question':row['original_question'],'decision':'exclude','exclusion_reason':'incomplete_or_unreadable','exclusion_note':EXPLANATION}
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
    candidate=ROOT/'review/candidates/answers'/f'{CANONICAL_ID}.md'
    if candidate.exists(): raise SystemExit('unexpected candidate exists; source-unrecoverable retirement must not discard candidate silently')

    decisions.sort(key=lambda d:(str(d.get('source_note_id','')),int(d.get('source_question_index',0))))
    audit['decisions']=decisions; audit['audited_at']='2026-08-26'; audit['include_count']=sum(d.get('decision')=='include' for d in decisions); audit['exclude_count']=sum(d.get('decision')=='exclude' for d in decisions)
    write_json(ap,audit); write_jsonl(cp,sorted(canon,key=lambda x:x['canonical_id'])); progress['updated_at']='2026-08-26'; progress['items']=sorted(progress.get('items',[]),key=lambda x:x.get('canonical_id','')); write_json(pp,progress)
    print(f'Retired source-unrecoverable batch 0036 singleton: {CANONICAL_ID}')
    return 0

if __name__=='__main__': raise SystemExit(main())
