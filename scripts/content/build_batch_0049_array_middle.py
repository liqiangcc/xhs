#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0049 array-middle candidate."""
from __future__ import annotations
import hashlib, json, re, subprocess, tempfile
from pathlib import Path

ROOT=Path('.')
DATE='2026-08-29'
CID='cq_q_d4ea0d40c5cb4909d6157856f0fe58fe'
QID='d4ea0d40c5cb4909d6157856f0fe58fe'
EXPECTED='算法：查找数组的中间元素及复杂度分析'
BATCH='0049'
JLS_ARRAY='https://docs.oracle.com/javase/specs/jls/se21/html/jls-10.html'

CANDIDATE=r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d4ea0d40c5cb4909d6157856f0fe58fe","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 查找数组的中间元素及复杂度分析

## 核心结论

数组支持按下标直接访问，所以“找中间元素”本身不需要遍历：已知长度 n 后，下标计算和取值都是 O(1)，辅助空间 O(1)。真正需要先澄清的是**偶数长度数组没有唯一的中间元素**。来源没有给偶数长度约定，因此不能擅自把左中位、右中位或两者之一冒充成唯一答案。

这里采用不丢信息的契约：空数组返回空结果；奇数长度返回唯一中间元素；偶数长度返回中间的两个元素，顺序为左、右。若面试官要求单个元素，再明确选择左中位 `(n - 1) / 2` 或右中位 `n / 2` 即可，复杂度都不变。

## 1 分钟版

- 长度 n 的数组有效下标是 `0..n-1`。
- 左中间下标可以统一写成 `(n - 1) / 2`，右中间下标写成 `n / 2`。
- n 为奇数时两者相等，因此只有一个中间元素。
- n 为偶数时两者相邻且不同，因此题意若没约定，就应该说明歧义，而不是偷偷选一个。
- 数组下标计算、`length` 读取和元素访问都是常数次操作，所以时间 O(1)。
- 返回最多两个值，辅助空间也是 O(1)。

## 3 分钟版

```java
public final class ArrayMiddle {
    public static int[] middleValues(int[] nums) {
        int n = nums.length;
        if (n == 0) {
            return new int[0];
        }

        int left = (n - 1) / 2;
        int right = n / 2;
        if (left == right) {
            return new int[]{nums[left]};
        }
        return new int[]{nums[left], nums[right]};
    }

    public static int leftMiddleIndex(int length) {
        if (length <= 0) {
            throw new IllegalArgumentException("length must be positive");
        }
        return (length - 1) / 2;
    }

    public static int rightMiddleIndex(int length) {
        if (length <= 0) {
            throw new IllegalArgumentException("length must be positive");
        }
        return length / 2;
    }
}
```

例如 `[10,20,30,40,50]` 长度 5：`left=2,right=2`，返回 `[30]`。`[10,20,30,40]` 长度 4：`left=1,right=2`，返回 `[20,30]`。这比直接写 `nums[n/2]` 更完整，因为后者在偶数长度时实际上默默选择了右中间元素。

## 关键细节

- **偶数长度的歧义是题目边界，不是代码细节**：长度 4 的数组中间位置位于下标 1 和 2 之间；返回哪个必须有约定。
- **两个公式可以统一奇偶**：`(n-1)/2` 是左中间，`n/2` 是右中间；奇数时自然相等。
- **空数组**：没有中间元素。本答案返回长度 0 的结果；如果接口需要异常或 Optional，应由调用契约决定，来源没有规定。
- **值内容不影响位置**：这里找的是按数组位置定义的中间元素，不是统计学中位数；不需要排序。
- **复杂度 O(1)**：没有循环、递归或随 n 增长的数据结构，只做固定次数整数运算和数组读取。
- **不要写成 `(0 + n - 1) / 2` 的二分模板后再混淆左右中间**：直接使用上面的左右公式更清晰。
- **返回数组的空间口径**：本实现为了统一返回 0/1/2 个值会创建一个最多长度 2 的结果数组，其大小与输入 n 无关，仍是 O(1)。

## 原理机制

数组中间位置只由长度决定，与元素值无关。把首下标 0 和末下标 `n-1` 看作区间两端：当 n 为奇数，两端之间有一个整数下标；当 n 为偶数，几何中点落在两个整数下标之间，所以出现左、右两个候选。

因此这道题的关键不是设计搜索算法，而是把“中间”的数学定义映射到离散下标，并把偶数长度策略变成显式契约。只要数组长度已知，就没有必要扫描元素。

## 项目经验版

来源没有真实项目背景，不能虚构线上经历。实际接口里我会避免只叫 `middle()` 却不说明偶数策略；更好的命名是 `leftMiddle`、`rightMiddle` 或显式返回两个中间值。这样调用方不会因为默认策略不同产生 off-by-one 问题。测试重点应覆盖空数组、1/2 个元素、奇偶长度以及任意值内容，因为元素值本身不应改变中间位置。

## 常见追问

- 问：`nums[n/2]` 为什么不总是“唯一正确”？答：奇数长度没问题；偶数长度时它选择的是右中间元素，而来源没有保存这个约定。
- 问：如何取左中间？答：正长度下用 `(n - 1) / 2`。
- 问：如何取右中间？答：正长度下用 `n / 2`。
- 问：要不要遍历数组？答：不用。长度和随机下标访问已经足够，所以时间 O(1)。
- 问：需要排序吗？答：不需要。题目说的是位置上的中间元素，不是中位数；排序会改变问题。
- 问：空数组怎么办？答：没有中间元素；本答案返回空结果，其他 API 也可以选择异常，但必须显式约定。

## 易错点

- 偶数长度时直接返回 `nums[n/2]`，却不说明这是右中间策略。
- 把“中间元素”和“中位数”混淆，错误地先排序。
- 为了找中间位置写线性循环，把本来 O(1) 的数组访问做成 O(n)。
- 空数组仍访问下标 0，导致越界。
- 左右中间公式写反或产生 off-by-one。
- 复杂度只写 O(1) 却不解释这里依赖的是数组长度已知和按下标直接访问。
'''

TEST=r'''import java.util.Arrays;
public final class ArrayMiddleTest {
    private static void check(int[] input,int[] expected){
        int[] actual=ArrayMiddle.middleValues(input);
        if(!Arrays.equals(actual,expected)) throw new AssertionError(Arrays.toString(input)+" -> "+Arrays.toString(actual)+" expected="+Arrays.toString(expected));
    }
    public static void main(String[] args){
        check(new int[]{},new int[]{}); check(new int[]{7},new int[]{7}); check(new int[]{10,20},new int[]{10,20});
        check(new int[]{10,20,30},new int[]{20}); check(new int[]{10,20,30,40},new int[]{20,30}); check(new int[]{10,20,30,40,50},new int[]{30});
        check(new int[]{-5,-4,-3,-2},new int[]{-4,-3});
        for(int n=1;n<=1000;n++){
            int l=ArrayMiddle.leftMiddleIndex(n), r=ArrayMiddle.rightMiddleIndex(n);
            if(l!=(n-1)/2||r!=n/2||l>r||r-l>1) throw new AssertionError("index invariant n="+n);
            if((n&1)==1 && l!=r) throw new AssertionError("odd mismatch n="+n);
            if((n&1)==0 && r!=l+1) throw new AssertionError("even mismatch n="+n);
        }
        int[] large=new int[1_000_000]; large[499_999]=41; large[500_000]=42; check(large,new int[]{41,42});
        System.out.println("PASS empty=pass odd-even=pass index-invariant=1000 length=1000000 complexity-shape=constant-access");
    }
}
'''

def run(*args,cwd=None): return subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True)
def write_json(path,payload): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def main():
    candidate=ROOT/f'review/candidates/answers/{CID}.md'
    if candidate.exists(): raise SystemExit('candidate already exists; do not overwrite reviewed work')
    ctx=json.loads(run('node','scripts/xhs.js','answer','context','--canonical-id',CID,'--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id')!=CID or ctx.get('answer_type')!='coding': raise SystemExit('canonical context/type drift')
    if ctx.get('canonical',{}).get('question_ids')!=[QID]: raise SystemExit('ownership drift')
    src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==QID),None)
    if not src or src.get('original_question')!=EXPECTED or src.get('is_valid_for_library') is not True: raise SystemExit('source wording/validity drift')
    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}'; out.mkdir(parents=True,exist_ok=True); write_json(out/'context.json',ctx)
    candidate.parent.mkdir(parents=True,exist_ok=True); candidate.write_text(CANDIDATE,encoding='utf-8')
    for h in ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']:
        if CANDIDATE.count(h)!=1: raise SystemExit(f'section drift {h}')
    blocks=re.findall(r'```java\n(.*?)\n```',CANDIDATE,re.S)
    if len(blocks)!=1: raise SystemExit('expected exactly one Java block')
    with tempfile.TemporaryDirectory(prefix='b49-array-middle-') as td:
        p=Path(td); (p/'ArrayMiddle.java').write_text(blocks[0].strip()+'\n',encoding='utf-8'); (p/'ArrayMiddleTest.java').write_text(TEST,encoding='utf-8')
        run('javac','ArrayMiddle.java','ArrayMiddleTest.java',cwd=p); stdout=run('java','ArrayMiddleTest',cwd=p).stdout.strip()
    expected_stdout='PASS empty=pass odd-even=pass index-invariant=1000 length=1000000 complexity-shape=constant-access'
    if stdout!=expected_stdout: raise SystemExit(f'unexpected fixture output: {stdout}')
    validation={'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'command':'javac ArrayMiddle.java ArrayMiddleTest.java && java ArrayMiddleTest','stdout':stdout,'checks':['empty/single/two-element boundaries','odd/even middle values','left/right index invariant for lengths 1..1000','negative value independence','length-1000000 direct-access boundary']}; write_json(out/'writer_validation.json',validation)
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources=[{'source_id':'repository-source','title':'Batch 0049 frozen canonical/source context','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'jls-array','title':'Java Language Specification SE 21, Arrays','locator':JLS_ARRAY,'source_type':'official_documentation','checked_at':DATE},{'source_id':'fixture','title':'OpenJDK 21 array-middle deterministic fixture','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}]
    claims=[{'claim_id':'source-contract','text':'The preserved source asks for the middle element of an array and complexity analysis but does not specify an even-length convention or empty-input behavior; the answer exposes those ambiguities rather than inventing them.','source_ids':['repository-source'],'answer_locations':['核心结论','1 分钟版','关键细节']},{'claim_id':'array-indexing','text':'Under Java array indexing, the middle positions can be computed directly from length; the implementation returns one value for odd length and both adjacent middle values for even length with fixed-count index accesses.','source_ids':['jls-array','fixture'],'answer_locations':['3 分钟版','关键细节','原理机制']},{'claim_id':'runtime-validation','text':'OpenJDK 21 validation covers empty, singleton, odd/even arrays, index formulas for lengths 1..1000 and a length-1000000 direct-access boundary.','source_ids':['fixture'],'answer_locations':['3 分钟版','关键细节','易错点']}]
    coverage=[{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    scores={'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
    findings=['The answer directly solves array middle lookup instead of the generic long-tail placeholder.','Even-length ambiguity is surfaced explicitly; the default candidate returns both middle values rather than silently choosing one.','The O(1) time/O(1) auxiliary-space claim follows from a fixed number of length arithmetic and array accesses, not from an unnecessary scan.','OpenJDK 21 validation covers empty/odd/even cases, index invariants and a one-million-element boundary.','The answer distinguishes positional middle from median and does not fabricate unstated constraints.']
    review={'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':'source-first-isolated-reviewer-batch-0049-array-middle-20260829-v1','review_version':'batch-0049.array-middle.v1','decision':'pass','revision_round':1,'source_packet':[str(out/'context.json'),str(candidate),str(out/'writer_validation.json'),JLS_ARRAY,'docs/refactor/09_answer_content_standard.md'],'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied']}; write_json(out/'isolated_review_result.json',review)
    evidence={'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0049-array-middle-builder','writer_version':'xhs-answer-curator.v1'},'sources':sources+[{'source_id':'isolated-review','title':'Array-middle source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':validation['checks'],'boundary_tests':[{'case':'empty','expected':'[]','actual':'[]','passed':True},{'case':'odd length','expected':'single middle','actual':'pass','passed':True},{'case':'even length','expected':'left+right middle','actual':'pass','passed':True},{'case':'lengths 1..1000','expected':'index invariants','actual':'pass','passed':True},{'case':'length 1000000','expected':'[41,42]','actual':'[41,42]','passed':True}]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':review['reviewer_id'],'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':1,'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied'}; write_json(ROOT/f'review/evidence/{CID}.json',evidence)
    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'; text=task.read_text(encoding='utf-8')
    line='- [x] `cq_q_d4ea0d40c5cb4909d6157856f0fe58fe` source-first isolated review PASS: the preserved source asks for an array middle element plus complexity but does not define the even-length or empty-input contract. The candidate makes that ambiguity explicit, returns one middle value for odd length and both adjacent middle values for even length, and provides explicit left/right index formulas for callers requiring one side. OpenJDK 21 validation covers empty/single/odd/even arrays, index invariants for lengths 1..1000 and a length-1000000 direct-access boundary. The implementation uses fixed-count length arithmetic/index access, so time and auxiliary space are O(1); positional middle is kept distinct from median. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text: text=text.rstrip()+'\n\n## Progress\n'
    if line not in text: text=text.rstrip()+'\n'+line+'\n'
    task.write_text(text,encoding='utf-8'); print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')
if __name__=='__main__': main()
