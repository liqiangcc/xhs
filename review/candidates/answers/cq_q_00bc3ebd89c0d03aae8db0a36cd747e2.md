<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_00bc3ebd89c0d03aae8db0a36cd747e2","version":1,"status":"draft","updated_at":"2026-08-31","answer_type":"coding","quality_tier":"candidate"} -->
# 根据包含 nil 节点的数组生成二叉树，并完成层序遍历

## 核心结论

题面只说“包含 nil 节点的数组生成二叉树并层序遍历”，但没有说明数组编码规则；这里必须先把 `nil` 的语义说清楚。本答案采用常见的**按非 nil 父节点逐个消费左右孩子槽位的层序编码**，并用 Go 表达：输入 `[]*int`，第 0 项是根；随后从队列头部依次取非 nil 父节点，每个父节点最多消费两个后续槽位，`nil` 表示该孩子缺失。若队列已空但后面还有非 nil 值，则该值不可达，输入视为非法。构树后再做标准 BFS，输出 `[][]int`，每层一个切片。

## 1 分钟版

- 先定义编码契约：数组不是简单的“下标 `2i+1/2i+2` 完全二叉树公式”，而是按层序队列给每个真实父节点依次消费左、右两个孩子槽位。
- 空数组返回空树；首元素是 `nil` 时只有后续全为 `nil` 才接受，否则存在不可达非 nil 节点，返回错误。
- 构树时维护父节点队列；遇到非 nil 子槽就创建节点并入队，遇到 nil 只表示该方向没有孩子。
- 队列耗尽后检查剩余输入，任何非 nil 都说明编码非法；尾部多余 nil 可以忽略。
- 层序遍历再用一个 BFS 队列，每轮先冻结当前队列长度，消费恰好这一层并把孩子加入下一层。
- 构树和遍历都只线性访问可达节点/输入槽：时间 `O(m+n)`；构树队列和遍历队列的峰值空间都与树宽有关。

## 3 分钟版

```go
package treebuild

import "fmt"

type Node struct {
    Val         int
    Left, Right *Node
}

func BuildLevelOrder(vals []*int) (*Node, error) {
    if len(vals) == 0 {
        return nil, nil
    }
    if vals[0] == nil {
        for _, v := range vals[1:] {
            if v != nil {
                return nil, fmt.Errorf("unreachable non-nil node after nil root")
            }
        }
        return nil, nil
    }

    root := &Node{Val: *vals[0]}
    queue := []*Node{root}
    next := 1
    for len(queue) > 0 && next < len(vals) {
        parent := queue[0]
        queue = queue[1:]

        if next < len(vals) {
            if vals[next] != nil {
                parent.Left = &Node{Val: *vals[next]}
                queue = append(queue, parent.Left)
            }
            next++
        }
        if next < len(vals) {
            if vals[next] != nil {
                parent.Right = &Node{Val: *vals[next]}
                queue = append(queue, parent.Right)
            }
            next++
        }
    }
    for ; next < len(vals); next++ {
        if vals[next] != nil {
            return nil, fmt.Errorf("unreachable non-nil node at slot %d", next)
        }
    }
    return root, nil
}

func LevelOrder(root *Node) [][]int {
    if root == nil {
        return [][]int{}
    }
    result := make([][]int, 0)
    queue := []*Node{root}
    for len(queue) > 0 {
        width := len(queue)
        level := make([]int, 0, width)
        for i := 0; i < width; i++ {
            node := queue[0]
            queue = queue[1:]
            level = append(level, node.Val)
            if node.Left != nil {
                queue = append(queue, node.Left)
            }
            if node.Right != nil {
                queue = append(queue, node.Right)
            }
        }
        result = append(result, level)
    }
    return result
}
```

例如 `[1,2,3,nil,4,nil,5]`：根为 1；给父节点 1 消费 2、3；给父节点 2 消费 nil、4；给父节点 3 消费 nil、5。得到的层序结果是 `[[1],[2,3],[4,5]]`。这里的 `nil` 会占用一个孩子槽，但自身不会入父节点队列。

## 关键细节

- **先确认编码，不要猜**：另一种常见约定是完全二叉树数组下标公式 `left=2*i+1/right=2*i+2`。它和这里的“非 nil 父节点队列消费”在稀疏树上可能得到不同结果，必须由题目或接口契约决定。
- **nil 不入队**：`nil` 只占一个孩子槽；如果把 nil 也当父节点继续消费两个槽，就会把后续位置整体错位。
- **不可达输入**：例如 `[1,nil,nil,2]` 中根的两个孩子都为空，父队列已经耗尽，末尾 2 无法挂到任何节点，所以本契约返回错误而不是静默丢弃。
- **nil 根**：`[nil]` 或 `[nil,nil,nil]` 表示空树；`[nil,1]` 非法，因为 1 没有可达父节点。
- **层边界**：遍历时必须在每轮开始保存 `width := len(queue)`，然后只消费这 `width` 个节点；不能边 append 子节点边把它们也算进当前层。
- **重复值**：节点身份由位置/指针决定，不由值决定；两个值相同的节点仍需分别输出。
- **复杂度**：若输入槽数为 `m`、可达节点数为 `n`，构树 `O(m)`、遍历 `O(n)`；队列峰值是当前树宽度 `O(w)`，输出本身占 `O(n)`。

## 原理机制

构树过程本质上是在恢复一棵按 BFS 序列化的树。父节点队列保存“还有孩子槽待消费的真实节点”；每弹出一个父节点，就从输入游标顺序读取最多两个槽。非 nil 子节点成为新的待处理父节点，nil 只关闭对应的一条边。这个不变量保证输入游标单调前进且每个真实父节点恰好拥有左右两个槽位的解释机会。

遍历阶段是另一个 BFS：队列在一轮开始时恰好保存当前层节点，冻结长度后消费这些节点并把它们的非 nil 孩子追加到队尾，因此下一轮队列恰好对应下一层。

## 项目经验版

来源没有真实业务格式或线上序列化协议，不能虚构“项目里就是这种编码”。工程落地时最重要的是把编码写进接口契约并做 round-trip 测试：例如 JSON 中究竟用 `null`、缺字段还是稀疏数组表达空孩子；非法不可达槽位是拒绝、告警还是兼容忽略，都应由协议定义，而不是在构树函数里猜。

## 常见追问

- 问：为什么不能直接用 `2*i+1` 和 `2*i+2`？答：那对应另一种完全二叉树下标编码；当前答案声明的是“只给真实父节点消费孩子槽”的层序序列化，稀疏树上两者语义不同。
- 问：`nil` 节点为什么不进入队列？答：它表示边不存在，不是一个真实父节点；若入队会错误消耗后续孩子槽。
- 问：为什么 `[1,nil,nil,2]` 要报错？答：根已经没有任何真实孩子，父节点队列耗尽，2 没有可挂载的位置；本契约选择显式拒绝数据损坏。
- 问：尾部多几个 nil 怎么办？答：它们不引入不可达真实节点，本契约允许忽略；若协议要求严格最短编码，也可以改成拒绝，关键是先定义。
- 问：层序遍历怎么区分每一层？答：每轮开始冻结当前队列长度，只处理这些旧节点；本轮新增孩子留给下一轮。
- 问：如果只要一维 BFS 结果呢？答：构树不变，遍历时不需要冻结层长度或创建 `level`，按出队顺序直接追加到一个切片即可。

## 易错点

- 没说明数组编码规则，就默认 `2*i+1/2*i+2` 或默认队列消费。
- 把 nil 槽也加入父节点队列，导致后续孩子整体错位。
- 父队列耗尽后直接忽略剩余非 nil 输入，掩盖非法编码。
- BFS 中不冻结当前层长度，把下一层节点混入当前层。
- 用节点值判断是否重复，错误丢失值相同但位置不同的节点。
