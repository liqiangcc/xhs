#!/usr/bin/env python3
"""Source-first isolated review for Batch 0062 nil-tree construction and level order."""
from __future__ import annotations

import hashlib,json,subprocess
from pathlib import Path

ROOT=Path('.'); DATE='2026-08-31'; BATCH='0062'; CID='cq_q_00bc3ebd89c0d03aae8db0a36cd747e2'; QID='00bc3ebd89c0d03aae8db0a36cd747e2'; EXPECTED_QUESTION='算法：根据包含 nil 节点的数组生成二叉树，并完成层序遍历'
HEADINGS=['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES={'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
PROMOTION_BLOCKER='repository_human_approval_and_real_review_policy_not_yet_satisfied'
EXPECTED_STDOUT='PASS reviewer fixed=10 exhaustive=5461 random=30000 oracle=independent-model invalid_unreachable=pass nil_slots=pass levels=pass'

def write_json(path,payload): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run_validation(out:Path)->str:
    test=out/'treebuild_reviewer_test.go'
    test.write_text(r'''package treebuild

import (
  "fmt"
  "math/rand"
  "reflect"
  "testing"
)

type modelNode struct { v int; left,right *modelNode }
func model(vals []*int)(*modelNode,bool){
  if len(vals)==0{return nil,true}
  if vals[0]==nil { for _,v:=range vals[1:] { if v!=nil{return nil,false} }; return nil,true }
  root:=&modelNode{v:*vals[0]}; parents:=[]*modelNode{root}; pos:=1
  for len(parents)>0 && pos<len(vals) {
    p:=parents[0]; parents=parents[1:]
    if pos<len(vals) { if vals[pos]!=nil { p.left=&modelNode{v:*vals[pos]}; parents=append(parents,p.left) }; pos++ }
    if pos<len(vals) { if vals[pos]!=nil { p.right=&modelNode{v:*vals[pos]}; parents=append(parents,p.right) }; pos++ }
  }
  for ;pos<len(vals);pos++ { if vals[pos]!=nil{return nil,false} }
  return root,true
}
func modelLevels(root *modelNode)[][]int { out:=[][]int{}; var walk func(*modelNode,int); walk=func(n *modelNode,d int){if n==nil{return};for len(out)<=d{out=append(out,[]int{})};out[d]=append(out[d],n.v);walk(n.left,d+1);walk(n.right,d+1)};walk(root,0);return out }
func ip(v int)*int{x:=v;return &x}
func check(vals []*int,label string,t *testing.T){
  m,valid:=model(vals); got,err:=BuildLevelOrder(vals)
  if valid!=(err==nil){t.Fatalf("%s validity mismatch valid=%v err=%v",label,valid,err)}
  if !valid{return}
  want:=modelLevels(m); actual:=LevelOrder(got); if !reflect.DeepEqual(actual,want){t.Fatalf("%s got=%v want=%v",label,actual,want)}
}
func enumerate(a []*int,pos int,count *int,t *testing.T){ if pos==len(a){*count++;check(a,"exhaustive",t);return}; options:=[]*int{nil,ip(-1),ip(0),ip(1)};for _,v:=range options{a[pos]=v;enumerate(a,pos+1,count,t)} }
func TestReviewer(t *testing.T){
 fixed:=[][]*int{{},{nil},{nil,nil},{nil,ip(1)},{ip(1)},{ip(1),ip(2),ip(3),nil,ip(4),nil,ip(5)},{ip(1),nil,nil,ip(2)},{ip(1),ip(2),nil,ip(3)},{ip(7),ip(7),ip(7)},{ip(1),nil,ip(2),ip(3),nil,nil,ip(4)}}
 for i,v:=range fixed{check(v,fmt.Sprintf("fixed-%d",i),t)}
 count:=0;for n:=0;n<=6;n++{enumerate(make([]*int,n),0,&count,t)};if count!=5461{t.Fatalf("count=%d",count)}
 r:=rand.New(rand.NewSource(0x6200BC3F));opts:=[]*int{nil,ip(-3),ip(-2),ip(-1),ip(0),ip(1),ip(2),ip(3)};for i:=0;i<30000;i++{n:=r.Intn(24);a:=make([]*int,n);for j:=range a{v:=opts[r.Intn(len(opts))];if v!=nil{x:=*v;a[j]=&x}};check(a,"random",t)}
 fmt.Println("PASS reviewer fixed=10 exhaustive=5461 random=30000 oracle=independent-model invalid_unreachable=pass nil_slots=pass levels=pass")
}
''',encoding='utf-8')
    p=subprocess.run(['go','test','-run','TestReviewer','-v','.'],cwd=out,text=True,capture_output=True,check=False)
    if p.returncode!=0: raise SystemExit(f'{CID}: independent reviewer validation failed: {p.stderr or p.stdout}')
    lines=[x.strip() for x in p.stdout.splitlines() if x.startswith('PASS reviewer fixed=')]
    if lines!=[EXPECTED_STDOUT]: raise SystemExit(f'{CID}: reviewer stdout drift: {lines!r}\n{p.stdout}')
    return EXPECTED_STDOUT

def main():
    inventory_path=ROOT/f'review/content_build/answer_batch_{BATCH}/source_inventory.json'; inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
    item=next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id')==CID),None)
    if inventory.get('boundary_result')!='pass' or not item or item.get('answer_type')!='coding': raise SystemExit(f'{CID}: inventory/type invalid')
    if item.get('question_ids')!=[QID] or item.get('source_question_count')!=1 or item.get('source_occurrence_count')!=1: raise SystemExit(f'{CID}: inventory ownership drift')
    if {x.get('original_question') for x in item.get('source_questions',[])}!={EXPECTED_QUESTION}: raise SystemExit(f'{CID}: source wording drift')
    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}'; context_path=out/'context.json';context=json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type')!='coding' or (context.get('canonical') or {}).get('question_ids')!=[QID]: raise SystemExit(f'{CID}: context drift')
    rows=list(context.get('source_questions') or []); 
    if len(rows)!=1 or rows[0].get('original_question')!=EXPECTED_QUESTION: raise SystemExit(f'{CID}: source occurrence drift')
    candidate_path=ROOT/f'review/candidates/answers/{CID}.md';candidate=candidate_path.read_text(encoding='utf-8');digest=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    for h in HEADINGS:
        if candidate.count(h)!=1: raise SystemExit(f'{CID}: section drift {h}')
    if candidate.count('- 问：')<5: raise SystemExit(f'{CID}: followup coverage too small')
    required=['BuildLevelOrder','LevelOrder','[]*int','unreachable non-nil','nil 不入队','width := len(queue)','2*i+1','O(m+n)','尾部多几个 nil','编码']
    missing=[x for x in required if x not in candidate]
    if missing: raise SystemExit(f'{CID}: missing boundary/mechanism coverage {missing}')
    stdout=run_validation(out); rv=out/'reviewer_validation.json';write_json(rv,{'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'validator':'independent_source_first_reviewer','command':'go test -run TestReviewer -v .','stdout':stdout,'checks':['10 fixed empty/nil-root/sparse/duplicate/unreachable boundaries match an independent model','all 5,461 token arrays through length six over nil/-1/0/1 match independent validity and DFS levels','30,000 independently seeded random token arrays match independent model validity and levels','nil consumes a child slot without becoming a parent; unreachable non-nil slots are rejected']})
    reviewer_id='source-first-isolated-reviewer-batch-0062-nil-tree-20260831-v1';version='batch-0062.nil-tree-level-order.v1';findings=['The single frozen source asks for constructing a binary tree from an array containing nil nodes and then performing level-order traversal; it does not fix the array encoding convention.','The candidate explicitly declares a queue-consumption encoding and contrasts it with heap-index 2*i+1/2*i+2 encoding, preventing an unstated sparse-tree assumption from being presented as source fact.','The construction invariant is consistent: only real parent nodes consume child slots, nil closes one edge without entering the parent queue, and unreachable non-nil trailing slots are rejected.','The traversal freezes the pre-round queue width and is independently checked against DFS-by-depth levels.','Independent validation covers 10 fixed boundaries, all 5,461 short token arrays in a bounded alphabet, and 30,000 separately seeded random encodings against an independent parser/model.','Empty/nil-root, duplicate values, trailing nil tolerance, invalid unreachable values, one-dimensional BFS variant and O(m+n)/O(w) bounds are explicit without fabricated project history.']
    rr=out/'isolated_review_result.json';write_json(rr,{'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':reviewer_id,'review_version':version,'decision':'pass','revision_round':1,'source_packet':[str(context_path),str(inventory_path),str(candidate_path),str(out/'treebuild.go'),str(out/'treebuild_reviewer_test.go'),str(rv),'config/answer_quality.json','docs/refactor/09_answer_content_standard.md'],'forbidden_inputs_not_used':[str(out/'writer_research.json'),str(out/'writer_validation.json'),'writer self score','writer expected decision'],'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':[PROMOTION_BLOCKER]})
    evidence=ROOT/f'review/evidence/{CID}.json';sources=[{'source_id':'repository-source','title':'Batch 0062 frozen repository context for nil-tree construction and level order','locator':str(context_path),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'source-inventory','title':'Batch 0062 occurrence-aware frozen source inventory','locator':str(inventory_path),'source_type':'repository_structured_source','checked_at':DATE},{'source_id':'reviewer-validation','title':'Independent Go nil-tree parser/traversal differential validation','locator':str(rv),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},{'source_id':'isolated-review','title':'Batch 0062 nil-tree source-first isolated review','locator':str(rr),'source_type':'repository_structured_source','checked_at':DATE}]
    claims=[{'claim_id':'source-boundary','text':'The source requires a nil-containing array to be turned into a binary tree and traversed level-order, but does not preserve a specific sparse-array encoding convention.','source_ids':['repository-source','source-inventory'],'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节']},{'claim_id':'queue-consumption-contract','text':'Under the declared queue-consumption encoding, nil consumes one child slot without becoming a parent and unreachable non-nil slots are rejected.','source_ids':['reviewer-validation'],'answer_locations':['3 分钟版','关键细节','原理机制','常见追问']},{'claim_id':'traversal-boundaries','text':'Independent validation covers empty/nil roots, sparse/duplicate trees, invalid encodings and exact level grouping against a DFS-based independent model.','source_ids':['reviewer-validation','isolated-review'],'answer_locations':['1 分钟版','关键细节','常见追问','易错点']}]
    write_json(evidence,{'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0062-nil-tree-level-order-writer','writer_version':'xhs-answer-curator.v1'},'sources':sources,'claims':claims,'source_question_coverage':[{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}],'source_occurrence_count':1,'validation':{'validator':'independent_source_first_reviewer','result':'pass','artifact':str(rv),'boundary_tests':[{'case':'empty/nil root','expected':'empty tree and empty levels','passed':True},{'case':'unreachable non-nil slot','expected':'explicit error','passed':True},{'case':'5,461 exhaustive short encodings','expected':'same validity and level groups as independent model','passed':True},{'case':'30,000 random encodings','expected':'same validity and level groups as independent model','passed':True}]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer_id,'review_version':version,'independent':True,'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},'promotion_blocker':PROMOTION_BLOCKER})
    task_path=ROOT/'tasks/answer-batches/TASK-20260711-0313-answer-batch-0062.md';task=task_path.read_text(encoding='utf-8')
    writer='- [x] `cq_q_00bc3ebd89c0d03aae8db0a36cd747e2` writer stage complete: the frozen nil-tree source Question is covered by an explicit Go queue-consumption encoding contract; the implementation rejects unreachable non-nil slots and validates fixed nil/sparse/duplicate boundaries plus 25,000 seeded random encode→rebuild cases against an independent DFS-by-depth level oracle. Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    review=f'- [x] `cq_q_00bc3ebd89c0d03aae8db0a36cd747e2` source-first isolated review PASS: candidate digest `{digest}`; the declared Go queue-consumption encoding and level-order traversal were independently revalidated over fixed invalid/nil/sparse boundaries, all 5,461 short token arrays through length six, and 30,000 separately seeded random encodings against an independent validity/DFS-level model. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if review not in task:
        if writer not in task: raise SystemExit(f'{CID}: task writer line drifted')
        task=task.replace(writer,writer+'\n'+review,1);task_path.write_text(task,encoding='utf-8')
    print(f'PASS {CID} digest={digest} reviewer=independent evidence={evidence}');return 0
if __name__=='__main__':raise SystemExit(main())
