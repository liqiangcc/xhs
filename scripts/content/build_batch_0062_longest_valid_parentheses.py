#!/usr/bin/env python3
"""Build the source-bounded Batch 0062 longest-valid-parentheses candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT=Path('.')
DATE='2026-08-31'
BATCH='0062'
CID='cq_q_6c5a986936f3d831fd8dc544ccd71910'
QIDS=['6c5a986936f3d831fd8dc544ccd71910','7c79cd047d29e5f6cafd84e396f0de8f']
EXPECTED_VARIANTS={'算法手撕：最长有效括号（Longest Valid Parentheses）。','算法手撕：最长有效括号（Longest Valid Parentheses）- 动态规划/栈 Hard。'}
EXPECTED_STDOUT='PASS fixed=12 random=30000 oracle=dp invalid=rejected empty=0 nested=6 reset=preserved'

CANDIDATE=r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_6c5a986936f3d831fd8dc544ccd71910","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 最长有效括号（Longest Valid Parentheses）：栈 / 动态规划

## 核心结论

来源明确是“最长有效括号”，其中一个原题还写了“动态规划/栈”。这里先声明一个可执行契约：输入非 `null`、且只包含 `'('` 和 `')'` 的 Java `String`，返回其中**最长连续有效括号子串的字符长度**；空串返回 `0`，`null` 或出现其他字符时抛 `IllegalArgumentException`。主实现用“下标栈 + 边界哨兵”，时间 `O(n)`、额外空间最坏 `O(n)`；动态规划可以作为等价的另一种 `O(n)` 解法。

## 1 分钟版

- 这是“最长**连续**有效括号”，不是最长括号子序列，所以需要知道当前有效区间的左边界。
- 栈里放 `'('` 的下标，并先压入哨兵 `-1`，表示当前可用连续区间左边界之前的位置。
- 遇到 `'('` 就压下标；遇到 `')'` 先弹一次：如果栈空，说明这个右括号无法匹配，把它的下标压回去作为新的断点；如果栈不空，当前有效长度就是 `i - stack.peek()`。
- 哨兵/断点是关键：它既处理从 `0` 开始的有效串，也让 `")()())"` 这类前缀非法后还能重新计算后续连续区间。
- 动态规划也能做：令 `dp[i]` 表示“以 `i` 结尾的最长有效括号长度”，根据 `s[i-1]` 是 `'('` 还是 `')'` 分两种转移。

## 3 分钟版

栈解法可以直接写成可编译 Java：

```java
import java.util.ArrayDeque;
import java.util.Deque;

public final class LongestValidParentheses {
    private LongestValidParentheses() {}

    public static int longestValidParentheses(String s) {
        if (s == null) {
            throw new IllegalArgumentException("input must be non-null");
        }
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(-1);
        int best = 0;

        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '(') {
                stack.push(i);
            } else if (ch == ')') {
                stack.pop();
                if (stack.isEmpty()) {
                    stack.push(i);
                } else {
                    best = Math.max(best, i - stack.peek());
                }
            } else {
                throw new IllegalArgumentException("only '(' and ')' are allowed");
            }
        }
        return best;
    }
}
```

为什么长度是 `i - stack.peek()`？处理一个可以匹配的 `')'` 后，栈顶不是“当前匹配的左括号”，而是**当前有效连续区间之前最近的未匹配边界**：可能是更早的 `'('` 下标，也可能是非法 `')'` 的断点。因此从 `stack.peek() + 1` 到 `i` 整段都是当前可确认的连续有效区间。

动态规划的状态是 `dp[i] = 以 i 位置结尾的最长有效括号长度`。只有 `s[i] == ')'` 时可能大于 0：

```text
1) ...()  且 s[i - 1] == '(':
   dp[i] = 2 + dp[i - 2]

2) ...))  且 s[i - 1] == ')':
   previous = dp[i - 1]
   j = i - previous - 1
   如果 j >= 0 且 s[j] == '(':
       dp[i] = previous + 2 + dp[j - 1]
```

第二种情况里的 `j` 是“前一个有效后缀之前，可能与当前 `')'` 配对的字符”。如果 `j - 1` 前面还有一个有效段，还要把 `dp[j-1]` 接上，这一步最容易漏。

## 关键细节

- **连续性**：返回的是最长有效括号**子串**长度，不能跳过中间字符。
- **哨兵不变量**：栈底/栈顶在匹配完成后保留的是当前连续有效段左边界之前的断点；初始断点为 `-1`。
- **非法右括号会重置边界**：当 `')'` 弹空栈时，把当前下标压回去，后面的合法串从这个位置之后重新开始。
- **不能只数配对数量**：`"())()"` 虽然有两对括号，但最长连续有效区间只有 `2`，不能得到 `4`。
- **DP 的第二个分支**：若前一个字符是 `')'`，必须跨过 `dp[i-1]` 再检查更左边是否有 `'('`，并把更前面的有效后缀拼接上。
- **输入边界**：来源没有规定非法字符和 `null`；这里把它们定义为调用错误，避免把“忽略非法字符”冒充成原题要求。

## 原理机制

这题本质是在一条字符序列上寻找“最长连续、括号平衡且任何前缀都不过度右闭合”的区间。栈解法不需要显式保存每个区间，只保留两类信息：尚未匹配的 `'('` 下标，以及最近一次无法匹配的 `')'` 断点。每当一个 `')'` 成功匹配后，当前下标到栈顶断点之间就是一个完整的连续有效后缀，所以能立刻计算长度。

DP 解法换了一个观察角度：只记录“以每个位置结尾”的最优长度。`"()"` 型转移直接向左接前一个后缀；`"...))"` 型转移则先跨过已经有效的后缀，再尝试找到它前面的 `'('` 与当前 `')'` 形成外层配对。两种方法都利用了同一个连续区间结构，只是一个维护边界，一个维护后缀长度。

## 项目经验版

来源没有真实项目场景，不能虚构线上使用经历。实际工程里如果输入是普通文本而不是题目保证的纯括号串，我会先明确非法字符语义：是整段报错、把非法字符当断点，还是先做词法过滤。不同语义会改变最长连续区间定义；本答案选择“非法字符直接报错”，只是为了让题目契约可验证。

## 常见追问

- 问：为什么栈一开始要放 `-1`？答：这样当有效串从下标 `0` 开始时，长度可以直接算成 `i - (-1)`；同时它代表“当前合法连续区间之前的位置”。
- 问：为什么遇到无法匹配的 `')'` 要把它的下标压栈？答：它会切断连续有效区间，后续合法串必须从它后面重新开始，所以它成为新的边界哨兵。
- 问：为什么不能只把 `'('` 下标压栈，不放断点？答：那样在栈清空后就不知道后续合法区间的左边界，会把非法前缀错误算进去。
- 问：DP 为什么要看 `i - dp[i-1] - 1`？答：`dp[i-1]` 是紧邻当前字符之前的完整有效后缀，当前右括号若想把它包起来，配对左括号只能在这个后缀之前一个位置。
- 问：栈和 DP 怎么选？答：只求长度时两者都是 `O(n)`；栈更直观地维护边界，DP 更适合展示状态转移。来源同时提到“动态规划/栈”，面试时最好能解释两者。
- 问：能做到 `O(1)` 空间吗？答：可以进一步用左右两次扫描计数处理纯括号串，但需要解释扫描方向如何补偿未匹配左括号；这不是当前主实现的契约。

## 易错点

- 把“最长有效括号子串”做成可以跳字符的子序列问题。
- 栈里只保存 `'('`，却忘了初始 `-1` 和非法 `')'` 断点。
- 遇到 `')'` 后直接用当前 `'('` 的下标算长度，漏掉前面已连接起来的有效段。
- DP 在 `"...))"` 分支只加 `dp[i-1] + 2`，忘记检查真正可配对的左括号位置以及 `dp[j-1]`。
- 用“总配对数 × 2”代替最长**连续**区间。
- 原题没规定非法字符，却默默忽略它们，改变连续区间语义。
'''

JAVA_IMPL=r'''import java.util.ArrayDeque;
import java.util.Deque;

public final class LongestValidParentheses {
    private LongestValidParentheses() {}

    public static int longestValidParentheses(String s) {
        if (s == null) throw new IllegalArgumentException("input must be non-null");
        Deque<Integer> stack = new ArrayDeque<>();
        stack.push(-1);
        int best = 0;
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            if (ch == '(') {
                stack.push(i);
            } else if (ch == ')') {
                stack.pop();
                if (stack.isEmpty()) stack.push(i);
                else best = Math.max(best, i - stack.peek());
            } else {
                throw new IllegalArgumentException("only '(' and ')' are allowed");
            }
        }
        return best;
    }
}
'''

JAVA_TEST=r'''import java.util.Random;
public final class LongestValidParenthesesWriterTest {
  private static final Random RNG=new Random(0x62006C5AL);
  private static int oracle(String s){int[] dp=new int[s.length()]; int best=0; for(int i=1;i<s.length();i++){if(s.charAt(i)!=')') continue; if(s.charAt(i-1)=='('){dp[i]=2+(i>=2?dp[i-2]:0);}else{int previous=dp[i-1]; int j=i-previous-1; if(j>=0&&s.charAt(j)=='(') dp[i]=previous+2+(j>=1?dp[j-1]:0);} best=Math.max(best,dp[i]);} return best;}
  private static void check(String s,int expected,String label){int actual=LongestValidParentheses.longestValidParentheses(s); if(actual!=expected) throw new AssertionError(label+" expected="+expected+" actual="+actual+" s="+s);}
  private static String random(int max){int n=RNG.nextInt(max+1); StringBuilder sb=new StringBuilder(n); for(int i=0;i<n;i++) sb.append(RNG.nextBoolean()?'(':')'); return sb.toString();}
  public static void main(String[] args){
    check("",0,"empty"); check("(",0,"left"); check(")",0,"right"); check("()",2,"pair"); check("(()",2,"partial"); check(")()())",4,"reset"); check("()(())",6,"nested-connect"); check("((()))",6,"nested"); check("()(()",2,"broken-tail"); check("())()",2,"separated"); check("(()())",6,"mixed"); check("())(())",4,"post-break");
    boolean nullThrew=false,invalidThrew=false; try{LongestValidParentheses.longestValidParentheses(null);}catch(IllegalArgumentException expected){nullThrew=true;} try{LongestValidParentheses.longestValidParentheses("()a");}catch(IllegalArgumentException expected){invalidThrew=true;} if(!nullThrew||!invalidThrew) throw new AssertionError("input contract not enforced");
    for(int i=0;i<30000;i++){String s=random(60); check(s,oracle(s),"random-"+i);} System.out.println("PASS fixed=12 random=30000 oracle=dp invalid=rejected empty=0 nested=6 reset=preserved");
  }
}
'''


def write_json(path:Path,payload:object)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main()->int:
    inventory_path=ROOT/f'review/content_build/answer_batch_{BATCH}/source_inventory.json'; inventory=json.loads(inventory_path.read_text(encoding='utf-8'))
    if inventory.get('boundary_result')!='pass': raise SystemExit('batch 0062 source inventory is not passing')
    item=next((x for x in inventory.get('canonicals',[]) if x.get('canonical_id')==CID),None)
    if not item or item.get('answer_type')!='coding': raise SystemExit(f'{CID}: missing/non-coding inventory row')
    if sorted(item.get('question_ids') or [])!=sorted(QIDS): raise SystemExit(f'{CID}: ownership drift')
    if {x.get('original_question') for x in item.get('source_questions',[])}!=EXPECTED_VARIANTS: raise SystemExit(f'{CID}: source wording drift')
    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{CID}'; context_path=out/'context.json'; context=json.loads(context_path.read_text(encoding='utf-8'))
    if not context.get('ok') or context.get('answer_type')!='coding': raise SystemExit(f'{CID}: context/type drift')
    if sorted((context.get('canonical') or {}).get('question_ids') or [])!=sorted(QIDS): raise SystemExit(f'{CID}: context ownership drift')
    if {x.get('original_question') for x in context.get('source_questions',[])}!=EXPECTED_VARIANTS: raise SystemExit(f'{CID}: context source variants drift')
    candidate_path=ROOT/f'review/candidates/answers/{CID}.md'; candidate_path.parent.mkdir(parents=True,exist_ok=True); candidate_path.write_text(CANDIDATE,encoding='utf-8'); digest=hashlib.sha256(candidate_path.read_bytes()).hexdigest()
    impl=out/'LongestValidParentheses.java'; test=out/'LongestValidParenthesesWriterTest.java'; impl.write_text(JAVA_IMPL,encoding='utf-8'); test.write_text(JAVA_TEST,encoding='utf-8')
    proc=subprocess.run(['bash','-lc','javac LongestValidParentheses.java LongestValidParenthesesWriterTest.java && java LongestValidParenthesesWriterTest'],cwd=out,text=True,capture_output=True,check=False)
    if proc.returncode!=0: raise SystemExit(f'{CID}: writer validation failed: {proc.stderr or proc.stdout}')
    stdout=proc.stdout.strip()
    if stdout!=EXPECTED_STDOUT: raise SystemExit(f'{CID}: stdout drift {stdout!r}')
    for p in out.glob('*.class'): p.unlink()
    validation=out/'writer_validation.json'; write_json(validation,{'schema_version':'answer_code_validation.v1','canonical_id':CID,'result':'pass','validated_at':DATE,'validator':'batch_0062_longest_valid_parentheses_writer_fixture','command':'javac LongestValidParentheses.java LongestValidParenthesesWriterTest.java && java LongestValidParenthesesWriterTest','stdout':stdout,'checks':['12 fixed empty/unmatched/nested/reset/separated boundaries','null and non-parenthesis characters rejected by explicit contract','30,000 seeded random parentheses strings up to length 60 match independent DP oracle']})
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':CID,'checked_at':DATE,'review_state':'writer_complete_isolated_review_pending','candidate_sha256':digest,'sources':[{'source_id':'repository-source','title':'Batch 0062 frozen repository context for longest valid parentheses','locator':str(context_path),'source_type':'repository_source_record','checked_at':DATE},{'source_id':'writer-fixture','title':'Longest-valid-parentheses stack differential validation','locator':str(validation),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE}],'claims':[{'claim_id':'source-boundary','text':'Both frozen source variants ask for longest valid parentheses; one explicitly calls out dynamic programming/stack, while neither fixes Java API or invalid-input semantics.','source_ids':['repository-source'],'answer_locations':['核心结论','1 分钟版','3 分钟版']},{'claim_id':'stack-behavior','text':'Under the declared pure-parentheses Java contract, the sentinel/index-stack implementation matches an independent DP oracle over fixed edge cases and 30,000 random inputs.','source_ids':['writer-fixture'],'answer_locations':['3 分钟版','关键细节','原理机制','常见追问']}],'source_question_coverage':[{'question_id':qid,'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问']} for qid in QIDS],'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    task_path=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'; task=task_path.read_text(encoding='utf-8').rstrip(); line=f'- [x] `{CID}` writer stage complete: both frozen longest-valid-parentheses source Questions are covered by an explicit Java continuous-substring contract with stack and DP reasoning; the stack implementation passes 12 fixed boundaries plus 30,000 seeded random strings against an independent DP oracle. Independent source-first review is still pending, so this is not a promotion or PASS claim.'
    if line not in task: task_path.write_text(task+'\n'+line+'\n',encoding='utf-8')
    print(EXPECTED_STDOUT); return 0

if __name__=='__main__': raise SystemExit(main())
