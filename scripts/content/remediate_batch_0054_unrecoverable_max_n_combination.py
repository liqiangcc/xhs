#!/usr/bin/env python3
"""Retire Batch 0054 '最大为 N 的数字组合' singleton when the executable contract is not recoverable."""
from __future__ import annotations
import json,shutil,subprocess
from pathlib import Path
ROOT=Path('.'); DATE='2026-08-29'
CID='cq_q_f2613a7970f7d61ff1180e5663db4e55'; QID='f2613a7970f7d61ff1180e5663db4e55'; EXPECTED='算法：最大为 N 的数字组合。'; NOTE_ID='68c7f34a000000001d007186'
TAGGED_BLOB='8e624eac21ab021a0843a85d83e9bfd21a1ad6f1'; DESC_BLOB='de804845bc925ced92ed0ad4a0347d35c45599ed'; RAW_BLOB='5d711655f1cf385e24c3b9913fc49223b0a3198b'
EXPLANATION=(
'仓库现存 tagged/structured 题目只保留“最大为 N 的数字组合”，原始笔记正文仅补充“手撕：最大为 N 的数字组合（hard）非hot100”，以及候选人有思路但 25 分钟未完成、最后讲了思路。'
'没有保留可选数字/数组从哪里来、数字是否可重复使用、组合是否要求保持顺序或去重、“最大为 N”是数值上界/长度/元素个数还是其他约束、N 的取值域、输入输出格式与无解语义。'
'这些缺失会对应完全不同的回溯、排列/组合或数位搜索 contract；即使 tagged taxonomy 标成“回溯”，也不足以恢复具体可执行题意。'
'把任一常见 hard 题的细节补进来都会把猜测伪装成原题，因此该 singleton 必须以 incomplete_or_unreadable fail-closed。'
'保留原始 Question 与明确 exclusion_note，但不再保留 Canonical、ReviewProgress 或活动 Answer。'
)
def read_json(p): return json.loads(p.read_text(encoding='utf-8'))
def write_json(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read_jsonl(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def write_jsonl(p,rows): p.write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
def git_blob(p): return subprocess.check_output(['git','hash-object',str(p)],text=True).strip()
def validate_sources():
    tagged=ROOT/f'note_tagged/{NOTE_ID}.json'; desc=ROOT/f'note_desc/{NOTE_ID}.txt'; raw=ROOT/f'note_json/{NOTE_ID}.json'
    for p,expected in [(tagged,TAGGED_BLOB),(desc,DESC_BLOB),(raw,RAW_BLOB)]:
        if git_blob(p)!=expected: raise SystemExit(f'{p}: source blob changed; reassess source-first')
    data=read_json(tagged); q=next((x for x in data.get('tagged_questions',[]) if x.get('question_id')==QID),None)
    if not q or q.get('original_question')!=EXPECTED or q.get('question_type')!='算法手撕_Coding' or q.get('is_valid_for_library') is not True or '回溯' not in (q.get('tech_entities') or []): raise SystemExit('tagged source wording/taxonomy drift')
    compact=desc.read_text(encoding='utf-8').replace(' ','')
    if '手撕：最大为N的数字组合（hard）非hot100' not in compact: raise SystemExit('raw description token missing')
    raw_text=raw.read_text(encoding='utf-8').replace(' ','')
    if '手撕：最大为N的数字组合（hard）非hot100' not in raw_text: raise SystemExit('raw JSON provenance token missing')
    image=ROOT/f'note_img_txt/{NOTE_ID}.txt'
    if image.exists() and image.read_text(encoding='utf-8').strip(): raise SystemExit('image-text evidence exists; reassess before exclusion')
def main():
    validate_sources(); cp=ROOT/'data/questions/canonical_questions.jsonl'; qp=ROOT/'data/questions/questions.jsonl'; pp=ROOT/'review/progress.json'; ap=ROOT/'config/question_validity_audit.json'
    canon=read_jsonl(cp); questions=read_jsonl(qp); progress=read_json(pp); audit=read_json(ap); decisions=list(audit.get('decisions',[]))
    c=next((x for x in canon if x.get('canonical_id')==CID),None); qrows=[x for x in questions if x.get('question_id')==QID]
    if len(qrows)!=1: raise SystemExit(f'expected one Question row, got {len(qrows)}')
    q=qrows[0]
    if c is None:
        d=next((x for x in decisions if x.get('question_id')==QID),None)
        if q.get('canonical_id') is not None or q.get('is_valid_for_library') is not False or q.get('exclusion_reason')!='incomplete_or_unreadable' or not d or d.get('decision')!='exclude': raise SystemExit('already-retired state inconsistent')
        print('already retired fail-closed'); return 0
    if list(c.get('question_ids') or [])!=[QID] or int(c.get('frequency',0))!=1: raise SystemExit(f'expected singleton ownership, got {c.get("question_ids")}')
    if q.get('canonical_id')!=CID or q.get('is_valid_for_library') is not True or q.get('original_question')!=EXPECTED or q.get('source_note_id')!=NOTE_ID: raise SystemExit('active Question projection drift')
    candidate=ROOT/f'review/candidates/answers/{CID}.md'
    if candidate.exists(): raise SystemExit('candidate exists; do not discard staged/reviewed work')
    replacement={'source_note_id':q['source_note_id'],'source_question_index':q['source_question_index'],'question_id':QID,'original_question':q['original_question'],'decision':'exclude','exclusion_reason':'incomplete_or_unreadable','exclusion_note':EXPLANATION}
    ref=(q['source_note_id'],q['source_question_index'])
    for i,d in enumerate(decisions):
        if (d.get('source_note_id'),d.get('source_question_index'))==ref: decisions[i]=replacement; break
    else: decisions.append(replacement)
    canon=[x for x in canon if x.get('canonical_id')!=CID]
    before=len(progress.get('items',[])); progress['items']=[x for x in progress.get('items',[]) if x.get('canonical_id')!=CID]
    if len(progress['items'])!=before-1: raise SystemExit('expected one ReviewProgress item to retire')
    active=ROOT/f'review/answers/{CID}.md'; archived=ROOT/f'review/archive/answers/{CID}.md'
    if not active.exists(): raise SystemExit('active long-tail baseline Answer missing')
    archived.parent.mkdir(parents=True,exist_ok=True)
    if archived.exists():
        if archived.read_bytes()!=active.read_bytes(): raise SystemExit('existing archive differs from active Answer')
        active.unlink()
    else: shutil.move(str(active),str(archived))
    decisions.sort(key=lambda d:(str(d.get('source_note_id','')),int(d.get('source_question_index',0)))); audit['decisions']=decisions; audit['audited_at']=DATE; audit['include_count']=sum(1 for d in decisions if d.get('decision')=='include'); audit['exclude_count']=sum(1 for d in decisions if d.get('decision')=='exclude')
    write_json(ap,audit); write_jsonl(cp,sorted(canon,key=lambda x:x['canonical_id'])); progress['updated_at']=DATE; progress['items']=sorted(progress.get('items',[]),key=lambda x:x.get('canonical_id','')); write_json(pp,progress)
    print('Retired source-unrecoverable Batch 0054 max-N numeric-combination singleton'); return 0
if __name__=='__main__': raise SystemExit(main())
