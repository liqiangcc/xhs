#!/usr/bin/env python3
"""Retire batch-0035 singleton whose coding contract is not recoverable.

The raw note preserves only "手撕链表逆序求和".  That phrase does not fix the
input/output contract: it could mean reversing one list then summing node values,
adding numbers encoded by reversed linked lists, or another linked-list task.
Do not manufacture a familiar LeetCode contract to satisfy answer coverage.
"""
from __future__ import annotations
import json
from pathlib import Path
import shutil

ROOT=Path('.')
CANONICAL_ID='cq_q_7eb3b8f2b4f6c12f3afffc6e8f2b500c'
QUESTION_ID='7eb3b8f2b4f6c12f3afffc6e8f2b500c'
EXPECTED='算法：链表逆序求和'
SOURCE_NOTE_ID='6821b6d30000000021000d2c'
SOURCE_NOTE=ROOT/f'note_tagged/{SOURCE_NOTE_ID}.json'
RAW_NOTE=ROOT/f'note_img_txt/{SOURCE_NOTE_ID}.txt'
EXPLANATION=(
    '原始图片文字只保留“手撕链表逆序求和”，tagged note 将其归一为“算法：链表逆序求和”。'
    '来源没有保存究竟是单链表反转后对节点值求和、两个以链表表示的整数相加、数字位是否逆序存储、'
    '输入链表数量、节点取值范围、输出是数值还是链表、进位规则、样例或边界条件。'
    '这些解释会产生不同的数据模型、算法和正确性条件，因此不能因为“链表/求和”而自行补成 Add Two Numbers 等熟悉题目。'
    '在获得更强原始来源前，该 singleton 无法恢复 strict-valid Coding 答案，应以可解释的 incomplete_or_unreadable 记录 fail-closed。'
)

def read_json(p): return json.loads(p.read_text(encoding='utf-8'))
def write_json(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read_jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_jsonl(p,rows): p.write_text(''.join(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for r in rows),encoding='utf-8')

def main():
    tagged=read_json(SOURCE_NOTE)
    q=next((x for x in tagged.get('tagged_questions',[]) if x.get('question_id')==QUESTION_ID),None)
    if not q or q.get('original_question')!=EXPECTED: raise SystemExit('exact tagged source wording missing/drifted')
    if q.get('question_type')!='算法手撕_Coding': raise SystemExit(f"source type drifted: {q.get('question_type')}")
    raw=RAW_NOTE.read_text(encoding='utf-8')
    if '手撕链表逆序求和' not in raw: raise SystemExit('raw OCR phrase missing')

    cp=ROOT/'data/questions/canonical_questions.jsonl'; qp=ROOT/'data/questions/questions.jsonl'; pp=ROOT/'review/progress.json'; ap=ROOT/'config/question_validity_audit.json'
    canon=read_jsonl(cp); questions=read_jsonl(qp); progress=read_json(pp); audit=read_json(ap)
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
        if (d.get('source_note_id'),d.get('source_question_index'))==ref: decisions[i]=replacement; found=True; break
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
    print(f'Retired source-unrecoverable batch 0035 singleton: {CANONICAL_ID}')
    return 0

if __name__=='__main__': raise SystemExit(main())
