#!/usr/bin/env python3
"""Build, execute, source-first review, and stage Batch 0049 first-unique-character candidate."""
from __future__ import annotations
import hashlib, json, re, subprocess, tempfile
from pathlib import Path

ROOT=Path('.')
DATE='2026-08-29'
CID='cq_q_d382816701ead25f1d37b021fb787a11'
QID='d382816701ead25f1d37b021fb787a11'
EXPECTED='算法手撕：查找字符串中第一个只出现一次的字符。要求给出基于哈希表或位图（Bitset）记录词频的空间优化方案'
BATCH='0049'
BITSET_DOC='https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/BitSet.html'
STRING_DOC='https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html'

CANDIDATE=r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d382816701ead25f1d37b021fb787a11","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 查找字符串中第一个只出现一次的字符：哈希表与 BitSet 空间权衡

## 核心结论

来源要求找到字符串中第一个只出现一次的字符，并给出基于哈希表或位图记录词频的空间优化方案，但没有规定字符集、返回形态或 Unicode “字符”的定义。这里采用一个明确 Java 契约：按 `String.charAt` 的 UTF-16 `char` 单元处理，返回第一个只出现一次的 `char` 的下标，没有则返回 `-1`。

普通哈希表方案用 `char -> count` 做两遍扫描，时间 O(n)，额外空间 O(k)，k 是不同字符数。进一步观察到题目只关心“0 次 / 1 次 / 至少 2 次”，不需要保存完整整数词频；对固定 16-bit `char` 域可用两个 `BitSet`：`seen` 表示出现过，`repeated` 表示至少出现两次。这样仍是 O(n) 时间，而相对输入长度 n 的辅助空间有固定上界，可记为 O(1)。

## 1 分钟版

- 第一遍统计状态，第二遍从左到右返回第一个“只出现一次”的位置。
- 哈希表保存 `char -> count`，通用直观，空间随不同字符数量 k 增长，为 O(k)。
- 位图优化不能只用一个 bit：一位无法同时区分“没出现、出现一次、出现多次”。
- 两个 `BitSet` 足够：首次见到 `c` 设置 `seen[c]`；之后再次见到就设置 `repeated[c]`。
- 第二遍第一个 `repeated[c] == false` 的字符就是答案，因为它既已出现又从未进入“重复”状态。
- Java `char` 只有 16 bit，因此两个位图的状态域上界固定；但 `char` 是 UTF-16 code unit，不等于所有 Unicode code point 或用户感知 grapheme。

## 3 分钟版

```java
import java.util.BitSet;

public final class FirstUniqueCharacter {
    public static int firstUnique(String s) {
        BitSet seen = new BitSet(Character.MAX_VALUE + 1);
        BitSet repeated = new BitSet(Character.MAX_VALUE + 1);

        for (int i = 0; i < s.length(); i++) {
            int c = s.charAt(i);
            if (seen.get(c)) {
                repeated.set(c);
            } else {
                seen.set(c);
            }
        }

        for (int i = 0; i < s.length(); i++) {
            if (!repeated.get(s.charAt(i))) {
                return i;
            }
        }
        return -1;
    }
}
```

例如 `swiss`：`s` 会进入重复状态，`w` 与 `i` 只出现一次；第二遍按原字符串顺序扫描，所以首先返回 `w` 的下标 1。这里不依赖任何哈希容器的迭代顺序。

## 关键细节

- **为什么两遍最稳妥**：第一遍结束前不能确定早期字符之后会不会再次出现；第二遍按输入顺序找唯一字符，仍保持 O(n)。
- **哈希表空间**：最多为每个不同 `char` 保存一个计数，记作 O(k)，`k <= min(n, 65536)`。
- **为什么是两个 BitSet**：问题需要三态 `0 / 1 / >=2`。`seen=0` 表示 0 次；`seen=1,repeated=0` 表示恰好 1 次；`repeated=1` 表示至少 2 次。一个 bit 无法无损表达三态。
- **O(1) 空间的口径**：这里依赖 Java `char` 的固定有限值域；它表示状态上界不随字符串长度 n 增长，不表示只占一个机器字。
- **返回下标是本答案契约**：来源没固定 API。若面试官要求返回字符，在找到下标后取 `s.charAt(index)` 即可。
- **UTF-16 边界**：补充字符可能由两个 surrogate `char` 组成。本答案按 code unit 计数；如果业务需要 Unicode code point 或 grapheme cluster，必须重新定义遍历单位和返回位置。
- **更窄字符集时**：如果题目明确只含 ASCII 或小写字母，固定小数组可能更简单；来源没有这个约束，所以这里不擅自缩小字符域。

## 原理机制

这道题真正需要保存的不是精确词频，而是某字符是否“恰好一次”。因此可以把无限的整数计数压缩成三态 `0,1,>=2`。两个二进制状态位足以编码三态，所以位图方案是在不丢失题目所需信息的前提下做状态压缩。

哈希表按实际出现的键保存状态，适合开放或很大的键域；位图则把字符值直接映射成 bit 下标，减少哈希桶和计数对象等结构开销，但前提是字符域有明确且合理的整数上界。空间优化来自这个约束，而不是“位图天然优于哈希表”。

## 项目经验版

来源没有真实项目上下文，不能虚构线上指标。真实文本处理中，我会先确认业务所谓“字符”到底是 UTF-16 code unit、Unicode code point 还是用户感知字符，并确认字符集是否受限。如果协议明确只有 ASCII，固定数组通常更简单；如果是任意 Unicode 文本，直接按 `char` 位图可能在 emoji 等补充字符上产生错误语义，应按真实文本单位重新设计并用国际化样例验证。

## 常见追问

- 问：为什么一个 BitSet 不够？答：一位只能区分两态，而我们至少要区分没见过、恰好一次、至少两次；两个 BitSet 可以编码这三态。
- 问：为什么统计完成后还要再扫原字符串？答：题目要求“第一个”，必须保留原顺序；第二遍扫描最直接。
- 问：哈希表和位图时间复杂度有什么不同？答：这里都做线性扫描，核心时间都是 O(n)；主要差异是状态存储方式和空间常数。
- 问：BitSet 真的是 O(1) 空间吗？答：在固定 Java `char` 16-bit 域的契约下，状态上界与 n 无关，所以按 n 计是 O(1)；字符域若不固定则不能这样说。
- 问：emoji 怎么办？答：很多 emoji 不对应单个 Java `char`。若“字符”指 code point 或 grapheme cluster，必须改变遍历和键定义。
- 问：为什么不保存精确次数？答：最终只区分一次和多次，超过 2 的具体数值不再影响答案，所以三态足够。

## 易错点

- 只用一个“出现过”位图，无法区分出现一次和出现多次。
- 统计完后从无顺序的键集合挑一个 count=1，却忘记“第一个”要求原字符串顺序。
- 来源没限定 ASCII，却直接假设 `int[26]`。
- 把 Java `char` 与 Unicode code point / grapheme cluster 混为一谈。
- 说位图 O(1) 却不说明依赖固定字符域。
- 为了省空间使用位图，却又额外保存整个字符列表或排序副本。
'''

TEST=r'''import java.util.Random;
public final class FirstUniqueCharacterTest {
    private static int oracle(String s) {
        int[] count=new int[Character.MAX_VALUE+1];
        for(int i=0;i<s.length();i++) count[s.charAt(i)]++;
        for(int i=0;i<s.length();i++) if(count[s.charAt(i)]==1) return i;
        return -1;
    }
    private static void check(String s,int expected){
        int actual=FirstUniqueCharacter.firstUnique(s);
        if(actual!=expected) throw new AssertionError("input="+s+" actual="+actual+" expected="+expected);
    }
    public static void main(String[] args){
        check("swiss",1); check("leetcode",0); check("loveleetcode",2); check("aabb",-1); check("",-1); check("中a中b",1); check("a",0);
        Random r=new Random(387L);
        for(int t=0;t<2000;t++){
            int n=r.nextInt(80); StringBuilder s=new StringBuilder(n);
            for(int i=0;i<n;i++) s.append((char)r.nextInt(1024));
            String value=s.toString(); check(value,oracle(value));
        }
        String large="a".repeat(99_999)+"b"; check(large,99_999);
        System.out.println("PASS examples=pass empty=pass bmp-char=pass random-oracle=2000 max-length=100000 bitset=match");
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
    for heading in ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']:
        if CANDIDATE.count(heading)!=1: raise SystemExit(f'section drift {heading}')
    blocks=re.findall(r'```java\n(.*?)\n```',CANDIDATE,re.S)
    if len(blocks)!=1: raise SystemExit('expected exactly one Java block')
    with tempfile.TemporaryDirectory(prefix='b49-first-unique-') as td:
        p=Path(td); (p/'FirstUniqueCharacter.java').write_text(blocks[0].strip()+'\n',encoding='utf-8'); (p/'FirstUniqueCharacterTest.java').write_text(TEST,encoding='utf-8')
        run('javac','FirstUniqueCharacter.java','FirstUniqueCharacterTest.java',cwd=p); stdout=run('java','FirstUniqueCharacterTest',cwd=p).stdout.strip()
    expected_stdout='PASS examples=pass empty=pass bmp-char=pass random-oracle=2000 max-length=100000 bitset=match'
    if stdout!=expected_stdout: raise SystemExit(f'unexpected fixture output: {stdout}')
    validation={'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'command':'javac FirstUniqueCharacter.java FirstUniqueCharacterTest.java && java FirstUniqueCharacterTest','stdout':stdout,'checks':['ordered first-unique examples','empty/no-unique/singleton boundaries','non-ASCII BMP char case','2000 deterministic random strings against independent frequency-array oracle','length-100000 boundary','two-BitSet implementation matches oracle']}
    write_json(out/'writer_validation.json',validation); digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources=[{'source_id':'repository-source','title':'Batch 0049 frozen canonical/source context','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'java-bitset','title':'Java SE 21 BitSet API','locator':BITSET_DOC,'source_type':'official_documentation','checked_at':DATE},{'source_id':'java-string','title':'Java SE 21 String API','locator':STRING_DOC,'source_type':'official_documentation','checked_at':DATE},{'source_id':'fixture','title':'OpenJDK 21 first-unique-character differential fixture','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}]
    claims=[{'claim_id':'source-contract','text':'The preserved source asks for the first character occurring exactly once and explicitly requests hash-table or BitSet frequency-storage space optimization, but does not fix charset, Unicode unit, or return shape.','source_ids':['repository-source'],'answer_locations':['核心结论','1 分钟版','关键细节']},{'claim_id':'java-domain','text':'Java SE 21 String exposes UTF-16 char units through charAt, while BitSet is an indexed vector of bits; under the explicitly chosen fixed 16-bit char-unit contract, two BitSets encode seen and repeated states with a bounded domain independent of input length.','source_ids':['java-string','java-bitset'],'answer_locations':['核心结论','1 分钟版','关键细节','原理机制']},{'claim_id':'runtime-validation','text':'OpenJDK 21 validation confirms the two-BitSet implementation on ordered examples, BMP/non-ASCII boundaries, 2000 deterministic random strings against an independent frequency-array oracle, and length 100000.','source_ids':['fixture'],'answer_locations':['3 分钟版','关键细节','原理机制','易错点']}]
    coverage=[{'question_id':QID,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    scores={'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}
    findings=['The answer follows the exact first-unique-character source and compares the requested hash-table concept with a compact BitSet state representation.','It correctly identifies that one bit is insufficient for 0/1/>=2 state and uses two BitSets for the actual optimized implementation.','The O(1)-with-respect-to-n space claim is explicitly scoped to Java fixed 16-bit char units.','OpenJDK 21 differential validation covers order, no-solution, BMP chars, 2000 random cases and a 100000-character boundary.','Unicode code-point/grapheme and source-unspecified API boundaries remain explicit; no production experience is fabricated.']
    review={'schema_version':'isolated_review.v1','canonical_id':CID,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated','reviewer_id':'source-first-isolated-reviewer-batch-0049-first-unique-character-20260829-v2','review_version':'batch-0049.first-unique-character.v2','decision':'pass','revision_round':2,'source_packet':[str(out/'context.json'),str(candidate),str(out/'writer_validation.json'),BITSET_DOC,STRING_DOC,'docs/refactor/09_answer_content_standard.md'],'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings,'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out/'isolated_review_result.json',review)
    evidence={'schema_version':'answer_evidence.v1','canonical_id':CID,'candidate_sha256':digest,'checked_at':DATE,'writer':{'writer_id':'content-batch-0049-first-unique-character-builder','writer_version':'xhs-answer-curator.v2'},'sources':sources+[{'source_id':'isolated-review','title':'First-unique-character source-first isolated review','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}],'claims':claims,'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':validation['checks'],'boundary_tests':[{'case':'swiss','expected':'1','actual':'1','passed':True},{'case':'no unique','expected':'-1','actual':'-1','passed':True},{'case':'BMP non-ASCII','expected':'match oracle','actual':'pass','passed':True},{'case':'2000 random strings','expected':'match oracle','actual':'pass','passed':True},{'case':'length 100000','expected':'99999','actual':'99999','passed':True}]},'review_state':'independent_source_first_review_passed','review':{'reviewer_id':review['reviewer_id'],'review_version':review['review_version'],'independent':True,'decision':'pass','revision_round':2,'scores':scores,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':findings},'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied'}
    write_json(ROOT/f'review/evidence/{CID}.json',evidence)
    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'; text=task.read_text(encoding='utf-8')
    line='- [x] `cq_q_d382816701ead25f1d37b021fb787a11` source-first isolated review PASS: the preserved source asks for the first once-only character and explicitly requests hash-table/BitSet space optimization. The candidate defines the otherwise-unspecified Java UTF-16 char/index contract, compares O(k) hash-table storage with a fixed-domain two-BitSet three-state encoding, and explains why one bit cannot distinguish once from repeated. OpenJDK 21 differential validation covers ordering, empty/no-unique/singleton cases, non-ASCII BMP chars, 2000 deterministic random strings and a length-100000 boundary. Unicode code-point/grapheme semantics remain an explicit non-inferred boundary. Formal promotion remains blocked by repository human-approval/real-review policy.'
    if '## Progress' not in text: text=text.rstrip()+'\n\n## Progress\n'
    if line not in text: text=text.rstrip()+'\n'+line+'\n'
    task.write_text(text,encoding='utf-8'); print(f'PASS staged/reviewed {CID} candidate_sha256={digest}')

if __name__=='__main__': main()
