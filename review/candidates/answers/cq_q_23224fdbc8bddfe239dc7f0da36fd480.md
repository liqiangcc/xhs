<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_23224fdbc8bddfe239dc7f0da36fd480","version":1,"status":"draft","updated_at":"2026-08-23","quality_tier":"candidate","answer_type":"coding"} -->
# 行、列分别有序的二维矩阵：从右上角 O(m+n) 判断 target 是否存在

## 核心结论

仓库原始面经保留下来的题意是：**二维数组每一行升序、每一列也升序，判断 target 是否存在**。原文没有规定 Java API、是否允许重复值、空矩阵或不规则矩阵如何处理，因此候选实现把这些部分明确标成接口选择，而不是冒充原题条件。

候选采用矩形 `int[][]`，把“升序”按**非递减**处理，因此重复值也合法；`null`、0 行、0 列返回 `false`；出现 `null` 行或各行长度不同则抛 `IllegalArgumentException`。算法从**右上角**开始：当前值等于 target 就成功；当前值大于 target 时删掉当前列；当前值小于 target 时删掉当前行。每一步至少排除一整行或一整列，所以最多移动 `m+n-1` 次，时间 `O(m+n)`、算法额外空间 `O(1)`，且不修改输入矩阵。

## 1 分钟版

把右上角元素看成当前未排除子矩阵的“分叉点”。它左边都不大于它、下面都不小于它：

1. `matrix[r][c] == target`：直接返回 `true`。
2. `matrix[r][c] > target`：这一列从当前行往下只会更大或相等，因此 target 不可能在当前列，`c--`。
3. `matrix[r][c] < target`：这一行从当前列往左只会更小或相等，因此 target 不可能在当前行，`r++`。

直到行越过底部或列越过左边界。整个过程只向左或向下走，最多走 `m+n-1` 步，所以是 `O(m+n)`；只用两个索引，额外空间 `O(1)`。

## 3 分钟版

设当前坐标是 `(r,c)`，尚未被排除的区域是行 `[r,m)`、列 `[0,c]`。右上角 `x = matrix[r][c]` 同时拥有两个方向上的单调信息：同一列向下不减，同一行向左不增。

若 `x > target`，则对所有 `i >= r` 都有 `matrix[i][c] >= x > target`，因此整列 `c` 都不可能命中，可以安全执行 `c--`。若 `x < target`，则对所有 `j <= c` 都有 `matrix[r][j] <= x < target`，因此整行 `r` 都不可能命中，可以安全执行 `r++`。这两个删除动作都不会丢掉一个可能的 target，因此“如果 target 还存在，它一定在当前未排除区域中”这个不变量一直成立。

终止时若没有命中，则 `r == m` 或 `c < 0`，未排除区域为空，于是 target 不存在。这个证明依赖的只是行、列非递减，并不要求元素互不相同。

候选没有直接使用“Search a 2D Matrix II”这个名字来补题，因为原始面经只写了行/列升序和查找 target；但在这组约束下，右上角（或对称地左下角）单调消元是可以由题意本身推出的。

## 关键细节

- **题源边界**：原文是“从行升序列升序的二维数组中判断 target 数是否存在”；未给数据范围、API、重复值或空输入约定。
- **候选的矩形 API**：使用 `int[][]`；`null`、0 行、0 列视为没有元素；`null` 行或 ragged matrix 明确拒绝。
- **重复值可用**：把“升序”解释为非递减。算法只使用 `>`、`<` 和 `==`，重复值不破坏消元证明。
- **为什么选右上角**：右上角同时具备“向左不增、向下不减”的可比较方向；左上角两个方向都只变大，单次比较不能决定排除哪一边。
- **不修改输入**：只读矩阵并移动索引；验证夹具会比较调用前后的深拷贝。
- **溢出无关**：算法不做元素加减乘除，只比较 `int`，因此 `Integer.MIN_VALUE` / `MAX_VALUE` 不会因为算术运算溢出。
- **复杂度**：最多向左 `n-1` 次、向下 `m-1` 次，加上初始位置的比较，总体 `O(m+n)`；额外状态只有 `row`、`column` 等常数变量。
- **若输入不满足单调前置条件**：候选不扫描验证排序性，因为那会改变接口成本；正确性契约要求调用方提供行列非递减矩阵。

## 原理机制

```java
public final class SearchSortedMatrix {
    private SearchSortedMatrix() {}

    public static boolean contains(int[][] matrix, int target) {
        if (matrix == null || matrix.length == 0) {
            return false;
        }
        if (matrix[0] == null) {
            throw new IllegalArgumentException("matrix rows must be non-null");
        }

        int columns = matrix[0].length;
        for (int row = 1; row < matrix.length; row++) {
            if (matrix[row] == null || matrix[row].length != columns) {
                throw new IllegalArgumentException(
                        "matrix must be rectangular with non-null rows");
            }
        }
        if (columns == 0) {
            return false;
        }

        int row = 0;
        int column = columns - 1;
        while (row < matrix.length && column >= 0) {
            int value = matrix[row][column];
            if (value == target) {
                return true;
            }
            if (value > target) {
                column--;
            } else {
                row++;
            }
        }
        return false;
    }
}
```

验证不是只跑一个教科书样例。固定用例覆盖 `null`、0 行、0 列、单元素、一行、一列、重复值、负数、`int` 极值、命中与未命中，并验证 ragged/null-row 按候选 API 拒绝。随后用固定随机种子生成 5000 个行列非递减矩阵，每个矩阵检查一个必然存在的 target 和一个任意 target，共 **10000 次**与独立的全矩阵线性扫描 oracle 做差分比较；同时验证输入矩阵没有被修改。实际夹具输出为 `PASS fixed=16 randomized=10000 oracle=full-scan input=unmodified`。

## 项目经验版

这是算法面试题，原始材料没有生产项目背景，因此不编造项目经验。工程接口如果要真正落地，需要另外确认：矩阵是否可能是稀疏/分块存储、是否允许 ragged rows、是否要验证单调前置条件、元素类型是否超过 `int`、以及错误输入是返回状态还是抛异常。那些都是接口层决策，不属于当前题源已经证明的事实。

## 常见追问

- 问：为什么从右上角开始，不从左上角？答：右上角左边都不大于它、下面都不小于它，比较一次就能排除一整行或一整列；左上角右边和下面都更大，当前值偏小时无法判断该往哪个方向排除。
- 问：如果当前值比 target 大，为什么能删整列？答：当前点以下同列元素都不小于当前值，因此也都大于 target；这一列在未处理区域里没有可能答案。
- 问：如果有重复值还成立吗？答：成立。非递减即可；大于时列下方是 `>= current > target`，小于时行左侧是 `<= current < target`。
- 问：复杂度为什么不是 `O(m*n)`？答：指针不会回头；列最多减 `n` 次，行最多增 `m` 次，不会访问每个格子。
- 问：能不能对每一行二分？答：可以得到大约 `O(m log n)`，但题目同时给了列有序这一额外结构，右上角消元能用到两维单调性并达到 `O(m+n)`。
- 问：如果矩阵不是矩形怎么办？答：原题没定义；当前候选显式选择“矩形矩阵”契约并拒绝 ragged/null-row，而不是悄悄给未定义语义。
- 问：如果输入没有按行列排序？答：那就违反算法前置条件，结果不保证正确；当前接口不额外做 `O(m*n)` 的排序性验证。

## 易错点

- 把题误答成普通滑动窗口，完全没有使用二维行列单调性。
- 选左上角后没有可证明的排除方向，最后退化成试探或回溯。
- 在 `current > target` 时错误地下移，或在 `current < target` 时错误左移。
- 用熟悉的 LeetCode 题名补出原文没有写的数据范围、API 或严格升序要求。
- 为了“防御性”先扫描整个矩阵验证单调性，却仍宣称查找本身只需 `O(m+n)` 的端到端成本。
- 忽略 0 行、0 列、重复值和 ragged matrix 的接口行为，使代码与口头契约不一致。
