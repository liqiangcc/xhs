<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_b655c9eceddfe5380a88f0023b9ab8c5","version":1,"status":"draft","updated_at":"2026-08-28","answer_type":"coding","quality_tier":"candidate"} -->
# K 个一组翻转链表：从尾部开始分组的 ACM 写法

## 核心结论

来源明确保留了三个关键信息：链表按 `K` 个一组翻转、**分组要从尾节点一侧开始计算**、并要求 ACM 模式包含 `ListNode` 与输入输出；但没有保存具体输入格式、`K<=0` 的异常约定以及不足 `K` 个节点如何处理。这里采用一个可执行合同：从链表尾部向前划分完整的 `K` 节点组，每个完整组内部翻转；如果总长度 `n` 不能整除 `K`，最前面的 `n % K` 个节点保持原顺序。ACM 输入约定为第一行 `n k`，随后读取 `n` 个整数，输出变换后的节点值，以空格分隔。

关键转换是：不需要真的从尾指针反向操作单链表。先遍历得到长度 `n`，计算 `prefix = n % k`。这 `prefix` 个头部节点正是“从尾部每 `k` 个一组”后剩余的不完整组，因此先跳过它们；剩余后缀长度一定是 `k` 的整数倍，再从左到右执行普通的 `k` 组翻转即可。这样仍是 `O(n)` 时间、`O(1)` 额外链表空间。

## 1 分钟版

- 先算链表长度 `n`，得到 `prefix = n % k`。
- 因为分组从尾部开始，所以不足 `k` 个的余数一定落在**头部**，这 `prefix` 个节点不翻转。
- 跳过头部余数后，剩余节点数能被 `k` 整除；对后缀逐组做标准原地链表反转。
- 每组反转后把“前一段尾部 → 当前组新头”和“当前组新尾 → 下一组起点”重新连接。
- 示例：`1→2→3→4→5, k=2`。从尾部分组是 `[2,3] [4,5]`，头部 `1` 保留，结果 `1→3→2→5→4`。
- 总共只进行常数次线性遍历，所以时间 `O(n)`，除节点本身外额外空间 `O(1)`。

## 3 分钟版

```java
import java.io.BufferedInputStream;
import java.io.IOException;

public final class Main {
    static final class ListNode {
        int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    static ListNode reverseFromTailGroups(ListNode head, int k) {
        if (k <= 0) {
            throw new IllegalArgumentException("k must be positive");
        }
        if (head == null || k == 1) {
            return head;
        }

        int n = 0;
        for (ListNode p = head; p != null; p = p.next) {
            n++;
        }

        int prefix = n % k;
        ListNode dummy = new ListNode(0);
        dummy.next = head;

        ListNode previousTail = dummy;
        ListNode groupStart = head;
        for (int i = 0; i < prefix; i++) {
            previousTail = groupStart;
            groupStart = groupStart.next;
        }

        while (groupStart != null) {
            ListNode nextGroup = groupStart;
            for (int i = 0; i < k; i++) {
                nextGroup = nextGroup.next;
            }

            ListNode prev = nextGroup;
            ListNode current = groupStart;
            for (int i = 0; i < k; i++) {
                ListNode next = current.next;
                current.next = prev;
                prev = current;
                current = next;
            }

            previousTail.next = prev;
            previousTail = groupStart;
            groupStart = nextGroup;
        }
        return dummy.next;
    }

    public static void main(String[] args) throws Exception {
        FastScanner in = new FastScanner();
        int n = in.nextInt();
        int k = in.nextInt();
        if (n < 0) {
            throw new IllegalArgumentException("n must be non-negative");
        }

        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        for (int i = 0; i < n; i++) {
            tail.next = new ListNode(in.nextInt());
            tail = tail.next;
        }

        ListNode result = reverseFromTailGroups(dummy.next, k);
        StringBuilder out = new StringBuilder();
        for (ListNode p = result; p != null; p = p.next) {
            if (out.length() > 0) out.append(' ');
            out.append(p.val);
        }
        System.out.println(out);
    }

    static final class FastScanner {
        private final BufferedInputStream in = new BufferedInputStream(System.in);
        private final byte[] buffer = new byte[1 << 16];
        private int ptr = 0, len = 0;

        private int read() throws IOException {
            if (ptr >= len) {
                len = in.read(buffer);
                ptr = 0;
                if (len < 0) return -1;
            }
            return buffer[ptr++];
        }

        int nextInt() throws IOException {
            int c;
            do {
                c = read();
                if (c < 0) throw new IllegalArgumentException("unexpected end of input");
            } while (c <= ' ');
            int sign = 1;
            if (c == '-') { sign = -1; c = read(); }
            int value = 0;
            while (c > ' ') {
                if (c < '0' || c > '9') throw new IllegalArgumentException("invalid integer token");
                value = value * 10 + (c - '0');
                c = read();
            }
            return value * sign;
        }
    }
}
```

以 `1→2→3→4→5, k=2` 为例，`n=5`，所以 `prefix=1`。先让 `previousTail` 和 `groupStart` 越过节点 `1`，再翻转 `[2,3]` 和 `[4,5]`。每次组内反转时把 `prev` 初始设为 `nextGroup`，因此组尾在反转过程中已经直接接到下一段；最后只需要让 `previousTail.next` 指向当前组的新头。

## 关键细节

- **“从尾部开始分组”不等于“从尾向前遍历单链表”**：单链表没有前驱指针。长度取模可以把尾部分组转换成“跳过头部余数后，从左到右翻完整组”。
- **余数位置不同**：普通“从头 K 个一组”会把不足 `K` 个的余数留在尾部；本题从尾部分组，所以余数留在头部。这是变形题最容易写错的地方。
- **`n < k`**：此时 `prefix=n`，没有完整组，链表原样返回。
- **`n % k == 0`**：`prefix=0`，从头开始每 `k` 个翻转，与普通 K 组翻转结果相同。
- **`k=1`**：每个节点本身就是完整组，原链表直接返回。
- **ACM 输入输出**：来源只说“ACM 模式”，没有保存平台格式。本答案的 `n k + n 个整数` 是明确的示例合同；真实平台若格式不同，只替换解析/打印层，核心链表算法不变。
- **节点身份**：算法只改 `next` 指针，不新建业务节点，因此节点值和节点对象集合都保持不变。

## 原理机制

设链表长度为 `n = q*k + r`，其中 `0 <= r < k`。如果从尾部向前每次取 `k` 个节点，那么一定能取出恰好 `q` 个完整组，剩下的 `r` 个节点只能位于链表最前端。因此问题等价于：保留前 `r` 个节点不动，然后把后面的 `q*k` 个节点按从左到右的连续 `k` 段分别反转。

组内反转维护三个关键指针：`current` 是尚未反转的当前节点，`prev` 是已经反转好的前缀头，`next` 暂存原来的后继。把 `prev` 初始设成下一组起点 `nextGroup`，可以让当前组翻完后，新尾天然连接下一段；而旧的 `groupStart` 在翻转后恰好成为当前组的新尾，用它更新 `previousTail` 就能继续处理下一组。

## 项目经验版

来源没有真实项目经历，不能虚构线上链表处理经验。工程实现时我会把“分组方向”“不足 K 个如何处理”“K 的合法范围”和“输入格式”先写成测试合同，因为这些边界比反转三指针本身更容易造成错误。若数据规模特别大，当前实现仍只使用常数级指针空间；如果输入本身来自数组，当然也可以先按数组索引从尾部分组，但那是利用了额外随机访问能力，不是单链表原地解法的必要条件。

## 常见追问

- 问：为什么不能直接套普通 K 个一组翻转？答：普通版本的余数在尾部不翻，本题从尾部划分完整组，余数应该在头部不翻；先用 `n % k` 找到头部余数后才能复用普通组反转。
- 问：一定要反转链表两次才能从尾部分组吗？答：不需要。先计算长度就能知道头部需要跳过多少节点，之后仍然正向原地处理。
- 问：为什么组内 `prev` 初始化成 `nextGroup`？答：这样反转第一条指针时就同时建立了当前组新尾到下一段的连接，减少额外的尾连接步骤。
- 问：如果 `n=8, k=3` 呢？答：`prefix=2`，头部两个节点保持不变，后面 `[3..5]`、`[6..8]` 两个完整组分别翻转。
- 问：如果题目要求不足 K 个的头部余数也翻转怎么办？答：那是另一个合同；可以单独反转前 `n%k` 个节点，但不能把这个规则默认加到当前来源里。
- 问：ACM 模式为什么还要把算法拆成方法？答：`main` 只负责 I/O，`reverseFromTailGroups` 保留纯算法边界，便于单元测试和替换不同平台输入格式。

## 易错点

- 把尾部分组写成普通头部分组，导致不完整组留错位置。
- 为了“从尾开始”先整体反转，再分组、再整体反转，却没有证明连接关系，容易产生额外错误。
- 组内反转后忘记连接前一段与当前新头，或者忘记更新当前组的新尾。
- 没处理 `n<k`、`k=1`、空链表等边界。
- 来源没有具体 ACM 输入格式，却把自己假设的 `n k` 格式说成原题固定格式。
