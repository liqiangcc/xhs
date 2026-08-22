<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_2366a87ab109eca0a9aac3ebad1db2f9","version":1,"status":"draft","updated_at":"2026-08-23","quality_tier":"candidate","answer_type":"coding"} -->
# 矩阵螺旋输出：边界收缩遍历

## 核心结论

仓库原始面经只保留了“矩阵螺旋输出”，可以确定这是**对一个已有矩阵做螺旋遍历/输出**，但没有给出元素类型、起点、旋转方向、返回形式、空输入或不规则矩阵行为。因此这里把接口选择明确写出来：输入为矩形 `int[][]`，从左上角开始按顺时针螺旋顺序返回 `List<Integer>`；`null`、0 行、0 列返回空列表；`null` 行或 ragged matrix 抛 `IllegalArgumentException`。这些是候选 API 约定，不冒充题源原文。

实现维护 `top / bottom / left / right` 四条尚未输出区域的边界。每轮依次输出上边、右边、下边、左边，然后收缩边界。关键不是记模板，而是每次输出下边、左边前重新检查边界，避免单行或单列的最后一层被重复加入。每个元素只输出一次，所以时间复杂度 `O(m*n)`；除返回结果外，只使用四个边界变量，算法额外空间 `O(1)`，且不修改输入矩阵。

## 1 分钟版

用四个边界表示还没访问的矩形：`top=0`、`bottom=m-1`、`left=0`、`right=n-1`。

每轮按顺时针顺序做四段：

1. 从 `left` 到 `right` 输出 `top` 行，然后 `top++`；
2. 从 `top` 到 `bottom` 输出 `right` 列，然后 `right--`；
3. 如果 `top <= bottom`，从 `right` 到 `left` 输出 `bottom` 行，然后 `bottom--`；
4. 如果 `left <= right`，从 `bottom` 到 `top` 输出 `left` 列，然后 `left++`。

循环条件是 `top <= bottom && left <= right`。第三、第四段的二次判断非常重要：矩阵可能在收缩后只剩一行或一列，如果不判断就会重复输出。每个格子只进入结果一次，因此 `O(m*n)` 时间，除结果外 `O(1)` 额外空间。

## 3 分钟版

不变量是：**进入每一轮时，尚未输出的元素恰好位于闭区间矩形 `[top..bottom] x [left..right]`，矩形外所有元素已经按正确的顺时针顺序输出且没有重复。**

先输出上边界后，把 `top` 下移一行，这一行从未访问区中删除；再输出右边界并把 `right` 左移一列。此时原来的未访问矩形可能已经没有行，所以输出下边界前必须检查 `top <= bottom`。同理，输出完下边界后可能已经没有列，因此输出左边界前检查 `left <= right`。

四条边每次覆盖的都是当前未访问区域的外圈，而且收缩后不会再进入结果，因此不会漏元素也不会重复元素。循环终止时至少有一个方向的区间为空，未访问区域为空，所以所有 `m*n` 个元素都已经按选择的顺时针顺序输出。

题源没有说“顺时针、左上角起点”，这只是为了把“螺旋输出”落成可执行接口而采用的常规选择；如果面试官指定从其他角或逆时针，只需要改变四段的起始边与方向，不应该把本候选的接口选择说成原题已有条件。

## 关键细节

- **题源边界**：原文只有“矩阵螺旋输出（给15分钟，超时就叫停）”，能确认遍历已有矩阵，不能确认 API、方向、起点或数据范围。
- **不是矩阵生成题**：当前题源要求“输出”已有矩阵；不要因为“螺旋矩阵”这个名字就把它替换成生成 `n x n` 矩阵的另一类题。
- **候选 API**：矩形 `int[][]`；顺时针、左上角起步；返回 `List<Integer>`；null/空矩阵返回空列表；ragged/null-row 明确拒绝。
- **单行/单列最容易重复**：上边或右边收缩后，必须在走下边和左边前再次判断边界是否仍合法。
- **不修改输入**：算法只读每个单元格；随机夹具会在调用前后做深比较。
- **元素值无特殊要求**：遍历只依赖坐标，不比较或运算元素，因此重复值、负数和 `Integer.MIN_VALUE`/`MAX_VALUE` 都不影响正确性。
- **复杂度**：输出本身就必须产生 `m*n` 个元素，因此时间下界是 `Omega(m*n)`；实现访问每个元素一次，达到 `O(m*n)`。不计返回列表，额外空间是 `O(1)`。
- **形状验证成本**：候选先检查每行长度一致，这需要 `O(m)`；它不改变总的 `O(m*n)` 上界（非空矩阵中 `n >= 1`）。

## 原理机制

```java
import java.util.ArrayList;
import java.util.List;

public final class SpiralMatrixTraversal {
    private SpiralMatrixTraversal() {}

    public static List<Integer> spiralOrder(int[][] matrix) {
        List<Integer> result = new ArrayList<>();
        if (matrix == null || matrix.length == 0) {
            return result;
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
            return result;
        }

        int top = 0;
        int bottom = matrix.length - 1;
        int left = 0;
        int right = columns - 1;

        while (top <= bottom && left <= right) {
            for (int column = left; column <= right; column++) {
                result.add(matrix[top][column]);
            }
            top++;

            for (int row = top; row <= bottom; row++) {
                result.add(matrix[row][right]);
            }
            right--;

            if (top <= bottom) {
                for (int column = right; column >= left; column--) {
                    result.add(matrix[bottom][column]);
                }
                bottom--;
            }

            if (left <= right) {
                for (int row = bottom; row >= top; row--) {
                    result.add(matrix[row][left]);
                }
                left++;
            }
        }
        return result;
    }
}
```

可执行验证不只覆盖示例：固定用例覆盖 `null`、0 行、0 列、`1x1`、单行、单列、宽矩阵、高矩阵、方阵、一般矩形、重复值和 `int` 极值，以及 ragged/null-row 的接口策略。随后使用固定随机种子生成 **5000 个** `1..20 x 1..20` 矩阵，与一个独立实现的 `visited[][] + 方向转弯` oracle 做逐项差分；这个 oracle 不使用边界收缩逻辑，因此能降低“实现和测试犯同一个错”的风险。同时验证输入矩阵在调用前后完全一致。实际夹具输出：`PASS fixed=15 randomized=5000 oracle=visited-direction-walk input=unmodified`。

## 项目经验版

这是算法面试题，题源没有生产项目经历，因此不虚构项目案例。工程化时才需要进一步确认：矩阵是否可能巨大到不适合把全部结果放进一个 `List`、是否希望用 iterator/stream 按需输出、是否接受 ragged rows、元素类型是否泛型化，以及错误输入该抛异常还是返回状态。若面试场景只要求手撕算法，先把遍历不变量、边界重复问题和复杂度讲清楚更重要。

## 常见追问

- 问：为什么第三、第四段要再判断边界？答：前两段已经收缩过 `top` 和 `right`，剩余区域可能只剩一行或一列甚至为空；不重新判断就会把刚输出过的元素再输出一次。
- 问：`1 x n` 会怎样？答：第一段输出整行并 `top++`，之后 `top > bottom`，右、下、左都不会产生额外元素。
- 问：`m x 1` 会怎样？答：第一段输出顶部元素，第二段继续向下输出唯一一列；之后 `right < left`，下边和左边不会重复。
- 问：为什么是 `O(m*n)`？答：每个元素恰好加入结果一次，而输出 `m*n` 个元素本身就需要 `Omega(m*n)` 时间。
- 问：额外空间真是 `O(1)` 吗？答：如果不计必须返回的 `List`，算法控制状态只有四个边界和循环变量，是 `O(1)`；若把输出也计入空间，总空间当然是 `O(m*n)`。
- 问：能不能用 `visited[][]`？答：可以，逻辑也直观，但需要 `O(m*n)` 额外空间。当前边界法利用矩形结构，不需要 visited 标记。测试中的独立 oracle 故意用了 `visited[][]`，避免和被测实现同构。
- 问：如果面试官要求逆时针或从别的角开始？答：先确认顺序契约，再按对应的四条边和方向调整；题源本身没有给这个信息，所以当前方向只是候选 API 选择。
- 问：为什么说不是 Spiral Matrix II？答：题源是“矩阵螺旋输出”，语义是遍历已有矩阵；生成新矩阵是不同输入/输出合同，不能由熟悉的题名自行补出来。

## 易错点

- 把“螺旋输出”误成“生成螺旋矩阵”，导致回答了另一道题。
- 每轮无条件执行四条边，在单行/单列收口时重复元素。
- 收缩顺序和遍历使用了已经更新后的错误边界，造成漏元素或越界。
- 只测 `3x3`，没测 `1xn`、`mx1`、宽矩阵和高矩阵。
- 声称题源明确了顺时针、左上角或具体 Java 签名，而原始材料并没有这些信息。
- 把返回结果列表也忽略掉后含糊地说“空间 O(1)”；面试时应明确“除输出之外的额外空间 O(1)”。
