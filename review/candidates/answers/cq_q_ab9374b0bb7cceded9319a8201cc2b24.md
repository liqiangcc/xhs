<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_ab9374b0bb7cceded9319a8201cc2b24","version":1,"status":"draft","updated_at":"2026-08-27","answer_type":"coding","quality_tier":"candidate"} -->
# SQL：查询每门功课都不低于 60 分的学生姓名

## 核心结论

原始面试笔记只明确保留了“查询每门功课都不低于 60 分的学生姓名（SQL）”，没有保存真实表名、字段名、是否存在未选课学生、分数能否为 `NULL`、一名学生一门课是否可能有多条成绩等 schema 细节。本候选先声明一个最小可执行参考契约：

- `students(student_id, name)` 保存学生；
- `scores(student_id, course_id, score)` 保存成绩；
- `score` 非空；
- 一名学生至少有一条成绩时才可能进入结果；
- 一名学生只要存在任意一门成绩 `< 60` 就必须排除。

在这个契约下，最直接的写法是按学生分组，并用 `HAVING MIN(score) >= 60` 表达“该学生所有已记录课程的最低分都不低于 60”。

## 1 分钟版

```sql
SELECT s.name
FROM students AS s
JOIN scores AS sc
  ON sc.student_id = s.student_id
GROUP BY s.student_id, s.name
HAVING MIN(sc.score) >= 60;
```

- `JOIN` 先把学生和成绩关联起来。
- `GROUP BY` 把结果粒度收缩成“一名学生一组”。
- 如果一组里最小成绩都 `>= 60`，那么这一组的每门成绩自然都 `>= 60`。
- 使用 `INNER JOIN` 意味着没有任何成绩的学生不会返回；这是本候选显式选择的参考契约，不冒充来源要求。
- 若真实表允许 `score IS NULL`，要先定义 `NULL` 是否算“不及格/未知”，不能直接依赖 `MIN` 忽略 `NULL` 的行为。

## 3 分钟版

参考 schema：

```sql
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY,
    name       VARCHAR(100) NOT NULL
);

CREATE TABLE scores (
    student_id INTEGER NOT NULL,
    course_id  INTEGER NOT NULL,
    score      INTEGER NOT NULL,
    PRIMARY KEY (student_id, course_id)
);
```

查询：

```sql
SELECT s.name
FROM students AS s
JOIN scores AS sc
  ON sc.student_id = s.student_id
GROUP BY s.student_id, s.name
HAVING MIN(sc.score) >= 60;
```

为什么成立：

1. 对某个学生，把他的所有成绩记作集合 `S`。
2. 条件“每门课都不低于 60”就是 `∀x∈S, x >= 60`。
3. 在 `S` 非空且成绩非 `NULL` 的前提下，这与 `MIN(S) >= 60` 等价。
4. `INNER JOIN` 让没有成绩记录的学生不进入任何分组，所以不会因为“空集合上的全称命题”而被意外选中。

也可以用反证式 `NOT EXISTS` 写：

```sql
SELECT s.name
FROM students AS s
WHERE EXISTS (
    SELECT 1
    FROM scores AS sc
    WHERE sc.student_id = s.student_id
)
AND NOT EXISTS (
    SELECT 1
    FROM scores AS sc
    WHERE sc.student_id = s.student_id
      AND sc.score < 60
);
```

两种写法表达的是同一个参考契约：**至少有一条成绩，并且不存在低于 60 分的成绩**。若面试官要求“学生必须参加课程表中的全部课程”，那还需要课程总数/选课关系，单靠 `scores` 表不能证明“所有应修课程都已有成绩”。

## 关键细节

- **没有成绩的学生**：来源未说明。本候选采用“不返回”的口径，所以使用 `INNER JOIN`；若业务要把零门课程也视为满足条件，查询会不同。
- **`NULL` 分数**：`MIN` 会忽略 `NULL`。因此若 `score` 可空，必须先定义业务语义；不能在不说明的情况下把未知成绩当作通过。
- **多次考试/补考**：如果同一学生同一课程有多条记录，“每门功课”到底看最新成绩、最高成绩还是所有尝试，需要额外业务规则。本参考 schema 用 `(student_id, course_id)` 唯一键避免这个未定义维度。
- **姓名不唯一**：分组时使用 `student_id, name`，不能只按姓名分组，否则同名学生可能被错误合并。
- **边界值**：题目说“不低于 60”，所以 `60` 应包含，条件是 `>= 60`，不是 `> 60`。
- **排序**：来源没有要求输出顺序，因此正式答案不把 `ORDER BY` 当作必需条件。
- **索引**：真实库通常至少需要能高效按 `student_id` 访问成绩，例如索引以 `student_id` 开头；具体索引设计要结合数据量和执行计划，来源没有提供这些事实。

## 原理机制

这题本质是把一个“对每一条子记录都成立”的全称条件翻译成 SQL。

常见有两种等价思路：

- **聚合**：把每个学生的成绩收成一个组，用 `MIN(score) >= 60` 证明该组不存在更低值。
- **反存在**：直接写“没有任何 `score < 60` 的记录”，也就是 `NOT EXISTS`。

聚合写法短，适合题目已经在考 `GROUP BY / HAVING`；`NOT EXISTS` 更直接地表达“不存在反例”。真正需要先确认的不是语法，而是集合边界：哪些课程属于该学生、没有成绩算什么、`NULL` 算什么、补考如何处理。边界没定义，SQL 写得再漂亮也可能回答了另一个问题。

## 项目经验版

来源没有真实项目规模或表结构，不虚构执行计划和索引收益。落地时我会先确认成绩表的唯一键、补考模型和 `NULL` 规则，再在目标数据库上看 `EXPLAIN`。如果数据量很大，聚合方案和反连接方案谁更优取决于索引、选择性和数据库优化器，不能脱离真实 schema 直接宣称某一种一定更快。

## 常见追问

- 问：为什么 `HAVING AVG(score) >= 60` 不对？答：平均分不低于 60 不能保证每门都不低于 60，例如 `100` 和 `20` 的平均分就是 `60`。
- 问：为什么 `HAVING MIN(score) >= 60` 能表达“每门都及格”？答：在成绩集合非空且非 `NULL` 的前提下，最小值都达到 60，就不存在任何低于 60 的元素。
- 问：没有成绩的学生要不要返回？答：来源没保存这个口径。本候选明确不返回；若业务选择空集也算满足，需要改连接/存在性条件并写清楚。
- 问：如果同一门课有补考记录怎么办？答：先定义“课程最终成绩”的归并规则，再对每门课得到唯一有效成绩后做全称判断，不能直接把所有考试记录混在一起。
- 问：为什么不能只 `GROUP BY name`？答：姓名通常不是唯一标识，同名学生会被合并成同一组；应使用稳定学生主键。

## 易错点

- 用 `AVG(score) >= 60` 代替“每门都 >= 60”。
- 忘记 `60` 本身应该通过，误写成 `> 60`。
- 只按姓名分组，导致同名学生串组。
- 没定义零成绩学生的语义，却在 `LEFT JOIN` / `INNER JOIN` 之间随意切换。
- 忽略 `NULL` 会被 `MIN` 跳过，导致未知成绩被悄悄排除在判断之外。
- 题目没提供真实 schema，却把自定义表名、字段名、补考规则说成原题事实。
