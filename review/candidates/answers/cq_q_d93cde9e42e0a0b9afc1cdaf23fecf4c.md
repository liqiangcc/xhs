<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_d93cde9e42e0a0b9afc1cdaf23fecf4c","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 四个嫌疑犯只有一人说真话：D 没有说谎

## 核心结论

原始面经正文能恢复完整条件：A 说“B 干的”，B 说“D 干的”，C 说“不是我干的”，D 说“B 在说谎”，并且四人中只有一个人说真话。枚举真正的作案者 A/B/C/D，分别计算四句话的真假，只有“C 是作案者”时恰好一人说真话；此时 A 假、B 假、C 假、D 真。因此题目问“谁没有说谎”，答案是 **D**；同时可推出作案者是 **C**。

这道题不应该只看当前结构化 Question 的摘要，因为摘要把四句话丢掉了；答案必须回到同一 source note 的原始正文恢复谓词，再做逻辑推导。这样才能避免把另一道经典“四人说谎题”的条件误套进来。

## 1 分钟版

- 把“作案者是谁”作为 4 个候选状态：A、B、C、D。
- 对每个状态计算四个布尔表达式：
  - A：`culprit == B`
  - B：`culprit == D`
  - C：`culprit != C`
  - D：“B 在说谎”，也就是 `!(culprit == D)`
- 统计四句话中 `true` 的数量，只保留 `trueCount == 1` 的状态。
- culprit=A 时 C、D 都真；culprit=B 时 A、C、D 真；culprit=C 时只有 D 真；culprit=D 时 B、C 真。
- 唯一满足条件的是 culprit=C，所以说真话的人是 D。
- 搜索空间固定只有 4 个，复杂度 O(1)；如果泛化到 n 个嫌疑人和任意谓词，就是 O(n²) 级别的直接枚举（n 个候选 × n 条陈述）。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.List;

public final class SuspectTruthPuzzle {
    enum Person { A, B, C, D }

    public record Solution(Person culprit, Person truthful) {}

    public static List<Solution> solve() {
        List<Solution> solutions = new ArrayList<>();
        for (Person culprit : Person.values()) {
            boolean a = culprit == Person.B; // A: B 干的
            boolean b = culprit == Person.D; // B: D 干的
            boolean c = culprit != Person.C; // C: 不是 C 自己干的
            boolean d = !b;                  // D: B 在说谎

            boolean[] statements = {a, b, c, d};
            int trueCount = 0;
            Person truthful = null;
            for (int i = 0; i < statements.length; i++) {
                if (statements[i]) {
                    trueCount++;
                    truthful = Person.values()[i];
                }
            }
            if (trueCount == 1) {
                solutions.add(new Solution(culprit, truthful));
            }
        }
        return solutions;
    }
}
```

运行结果只有一组：`culprit=C, truthful=D`。

这里最容易写错的是 D 的话。D 没有直接说“不是 D 干的”，而是说“B 在说谎”。B 的命题是“D 干的”，所以 D 的命题严格等价于“B 的命题为假”，即 `culprit != D`。在代码里用 `d = !b` 最不容易把语义改坏。

## 关键细节

- **先恢复原题**：当前结构化 Question 只有摘要，完整 A/B/C/D 四句话存在同一 source note 的正文；本答案以正文为 source-first 事实边界。
- **真话对象**：题目问“谁没有说谎”，即哪条 statement 为 true；不是直接问“谁是作案者”。不过唯一解同时推出 truthful=D、culprit=C。
- **D 的逻辑**：`D says B lies` 是对 B 命题取反；B 命题是 `culprit == D`，所以 D 命题是 `culprit != D`。
- **只有一个真话**：必须是“恰好 1 个 true”，不能写成“至少 1 个”。
- **不能假设每个非作案者都说真话/作案者必说谎**：原题只给四句具体陈述和真话数量，没有给这种角色规则。
- **唯一性**：四个 culprit 候选全部枚举后只有一组满足 `trueCount == 1`，因此结论不是任选一种可能。
- **复杂度**：本题规模固定，实际常数时间；泛化时以候选状态数乘陈述数计算。

## 原理机制

这是一个有限约束满足问题。未知变量只有 `culprit ∈ {A,B,C,D}`，每句话是这个变量上的布尔谓词，额外约束是四个谓词真值之和等于 1。把自然语言先翻译为布尔表达式，再枚举变量域，可以让推导既可读又可执行验证。

四种状态的真值表是：

| 作案者 | A: B干的 | B: D干的 | C: 不是C | D: B说谎 | 真话数 |
|---|---:|---:|---:|---:|---:|
| A | 假 | 假 | 真 | 真 | 2 |
| B | 真 | 假 | 真 | 真 | 3 |
| C | 假 | 假 | 假 | 真 | 1 |
| D | 假 | 真 | 真 | 假 | 2 |

因此只剩 C 这一行，而这一行唯一为真的列是 D。

## 项目经验版

来源没有真实项目场景，不能虚构。工程上遇到类似“规则组合”问题时，我会先把自然语言规则转成显式谓词并写出可枚举的小状态空间；规则多时再考虑 SAT/SMT、规则引擎或约束求解器。关键不是工具名字，而是保证每条规则的语义和否定关系可追踪，尤其避免把“某人说另一人说谎”错误简化成对作案者身份的直接判断。

## 常见追问

- 问：为什么 D 的话等价于 `culprit != D`？答：B 说“D 干的”，其命题是 `culprit == D`；D 说“B 在说谎”，就是对 B 的命题取反。
- 问：如果条件改成“只有一个人说假话”呢？答：约束从 `trueCount == 1` 改成 `trueCount == 3`，必须重新枚举；不能复用当前 D/C 结论。
- 问：为什么不直接手算？答：四种状态手算很快；代码化的价值是把自然语言谓词固定下来，并能机械验证“恰好一真”和唯一解，避免漏行。
- 问：能不能根据“C 说不是自己”直接判断？答：不能。C 的真假取决于 culprit，但还必须同时满足其他三句话和“只有一真”的全局约束。
- 问：题目只问谁说真话，为什么还枚举作案者？答：每句话真假都依赖真正的作案者；枚举这个唯一未知变量是最小完整状态空间。

## 易错点

- 只根据摘要回答，没有回到原始面经正文恢复四句话。
- 把 D 的话误写成“D 不是作案者”而没有说明它来自对 B 命题取反；虽然本题逻辑等价，但推导链会丢失。
- 把“只有一个人是真话”实现成 `trueCount >= 1`。
- 把“谁没说谎”和“谁是作案者”混为同一问题；本题答案分别是 D 和 C。
- 默认“作案者必然说谎”之类题目没有给出的额外规则。
