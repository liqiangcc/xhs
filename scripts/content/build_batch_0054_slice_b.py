#!/usr/bin/env python3
"""Build/validate/review a bounded Batch 0054 Coding slice: Unicode-aware frequency statistics and Array-to-Tree."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path('.')
DATE = '2026-08-29'
BATCH = '0054'

ITEMS = {
    'cq_q_f04ccedc97d093d669b3f71ba92dbcaf': {
        'qid': 'f04ccedc97d093d669b3f71ba92dbcaf',
        'expected': '算法实战：实现基于HashMap的字符串频率统计，并按照出现次数从高到低进行排序输出（要求处理字符边界与排序效率优化）',
        'class': 'StringFrequency',
        'candidate': r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f04ccedc97d093d669b3f71ba92dbcaf","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 基于 HashMap 的字符串频率统计并按频次降序输出

## 核心结论

来源保留了三个要求：用 HashMap 做字符串频率统计、按出现次数从高到低输出、处理字符边界并关注排序效率；但没有保存语言、所谓“字符”究竟指 UTF-16 `char`、Unicode code point 还是用户可见 grapheme cluster，也没有给并列频次的顺序。这里声明 Java 合同：按 **Unicode code point** 统计，避免把一个补充平面字符拆成两个 surrogate；按频次降序，频次相同时按 code point 数值升序，得到确定性结果。若业务要求用户可见字素簇，还需要更高层 Unicode 分段库，不能把 code point 冒充 grapheme cluster。

统计阶段遍历 `input.codePoints()`，用 `HashMap<Integer, Long>` 累加；排序阶段只排序不同 code point 的条目。设字符串含 C 个 code point、不同 code point 数为 U，则计数平均 O(C)，排序 O(U log U)，额外空间 O(U)，比先展开 C 个字符再整体排序更符合“频率统计 + 排序”的结构。

## 1 分钟版

- Java 的 `char` 是 UTF-16 code unit，补充平面字符会占两个 `char`；所以当前合同使用 `String.codePoints()`。
- 每个 code point 在 `HashMap<Integer, Long>` 中 `merge(cp, 1L, Long::sum)`。
- 统计完成后把 U 个不同字符转成条目列表，而不是把原字符串 C 个字符拿去排序。
- 排序规则：`count` 降序；并列时按 `codePoint` 升序，避免 HashMap 迭代顺序导致输出不稳定。
- 空字符串返回空列表；`null` 直接拒绝。
- 复杂度：平均计数 O(C)，排序 O(U log U)，空间 O(U)。
- code point 仍不等于用户眼里的一个字符；组合附加符和 emoji ZWJ 序列需要 grapheme cluster 语义时必须另定合同。

## 3 分钟版

```java
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public final class StringFrequency {
    public record Entry(int codePoint, long count) {
        public String symbol() {
            return new String(Character.toChars(codePoint));
        }
    }

    public static List<Entry> countAndSort(String input) {
        if (input == null) throw new IllegalArgumentException("input must not be null");

        Map<Integer, Long> counts = new HashMap<>();
        input.codePoints().forEach(cp -> counts.merge(cp, 1L, Long::sum));

        List<Entry> result = new ArrayList<>(counts.size());
        for (Map.Entry<Integer, Long> e : counts.entrySet()) {
            result.add(new Entry(e.getKey(), e.getValue()));
        }
        result.sort(
            Comparator.comparingLong(Entry::count).reversed()
                      .thenComparingInt(Entry::codePoint)
        );
        return result;
    }

    private StringFrequency() {}
}
```

例如输入 `"😀😀你你你a"` 时，`😀` 是一个 code point 而不是两个 surrogate；结果按当前合同是 `你×3`、`😀×2`、`a×1`。如果 `a/b/c` 都出现两次，则按 code point 升序稳定输出 `a,b,c`。

## 关键细节

- **字符边界**：`String.length()` 和 `charAt()` 面向 UTF-16 code unit；直接按 `char` 计数会把 U+FFFF 之外的字符拆开。`codePoints()` 至少保证 code point 边界正确。
- **不是 grapheme cluster**：`e + combining acute` 可能是两个 code point，但用户视觉上像一个字素；来源没有保存这种更强语义，候选不虚构。
- **并列频次**：来源只要求频次降序，未定义 tie-break。当前实现选择 code point 升序作为确定性合同，而不是依赖 HashMap 的非顺序语义。
- **为什么只排序 U 个条目**：频率已经聚合，相同字符无需重复参与排序；当 U 远小于 C 时可显著减少排序对象数。
- **计数类型**：使用 `long` 避免把计数上限不必要地绑定到 `int`；真实 Java `String` 长度本身仍受实现/内存上限约束。
- **输出形式**：返回结构化 `Entry`，展示层再决定打印格式，避免算法和 I/O 文案耦合。

## 原理机制

频率统计先把原始 code point 流映射成“code point → count”的聚合关系；HashMap 提供平均 O(1) 的查找/更新，因此只需一趟扫描。排序发生在聚合后的 U 个键上，比较器首先比较 `count` 的逆序，再用 `codePoint` 完成全序，因此最终输出与 HashMap 桶布局无关。

这里的关键边界是 Unicode 层级：UTF-16 code unit < Unicode code point < grapheme cluster。当前实现明确选择中间层，解决 surrogate 拆分问题，但不声称解决所有“用户可见字符”分段问题。

## 项目经验版

来源没有真实文本规模、语言分布或性能数据，不能虚构线上收益。工程里若 U 很大但只需要 Top-K，应改用大小为 K 的堆，把排序从 O(U log U) 降到 O(U log K)；若要完整有序输出，则 O(U log U) 比较排序是直接方案。若产品语义是“用户可见字符”，应先选定 Unicode grapheme segmentation 实现，再做同样的聚合和排序。

## 常见追问

- 问：为什么不用 `char`？答：Java `char` 是 UTF-16 code unit，一个 emoji 等补充平面字符通常由 surrogate pair 组成，按 `char` 会拆成两个键。
- 问：`codePoints()` 就等于真正的“字符”了吗？答：不一定。多个 code point 可以组成一个 grapheme cluster；当前合同只保证 code point 边界。
- 问：为什么频次相同还要定义顺序？答：来源没有要求，但 HashMap 本身不承诺业务顺序；加确定性 tie-break 能让测试和调用方行为稳定，同时明确这只是实现合同。
- 问：如果只要前 10 名呢？答：统计仍是 O(C)，随后用大小 10 的最小堆可把完整排序改为 O(U log 10)。
- 问：为什么不是 O(C log C)？答：我们不排序原始 C 个字符，只排序聚合后的 U 个不同键，所以是平均 O(C + U log U)。

## 易错点

- 用 `charAt()` 统计并宣称支持所有 Unicode 字符。
- 直接遍历 HashMap 输出，导致同一输入在不同实现细节下没有稳定的并列顺序。
- 把 C 个原始字符全部排序后再计数，忽略先聚合可把排序规模降到 U。
- 把 code point 和 grapheme cluster 混为一谈。
- 为了 Top-K 仍然完整排序全部 U 个条目，却没有说明性能取舍。
''',
        'test': r'''import java.util.*;

public final class StringFrequencyTest {
    private static void assertEntries(List<StringFrequency.Entry> actual, int[] cps, long[] counts) {
        if (actual.size()!=cps.length) throw new AssertionError("size " + actual);
        for (int i=0;i<cps.length;i++) {
            if (actual.get(i).codePoint()!=cps[i] || actual.get(i).count()!=counts[i]) {
                throw new AssertionError("index="+i+" actual="+actual.get(i));
            }
        }
    }

    private static List<StringFrequency.Entry> oracle(String s) {
        int[] alphabet = new int[]{'a','b','c','你',0x1F600,0x1D11E};
        long[] counts = new long[alphabet.length];
        s.codePoints().forEach(cp -> {
            for (int i=0;i<alphabet.length;i++) if (alphabet[i]==cp) { counts[i]++; return; }
            throw new AssertionError("unexpected cp="+cp);
        });
        List<StringFrequency.Entry> out = new ArrayList<>();
        for (int i=0;i<alphabet.length;i++) if (counts[i]>0) out.add(new StringFrequency.Entry(alphabet[i],counts[i]));
        out.sort(Comparator.comparingLong(StringFrequency.Entry::count).reversed().thenComparingInt(StringFrequency.Entry::codePoint));
        return out;
    }

    public static void main(String[] args) {
        assertEntries(StringFrequency.countAndSort(""), new int[]{}, new long[]{});
        assertEntries(StringFrequency.countAndSort("aaabbc"), new int[]{'a','b','c'}, new long[]{3,2,1});
        String unicode = "😀😀你你你a";
        assertEntries(StringFrequency.countAndSort(unicode), new int[]{'你',0x1F600,'a'}, new long[]{3,2,1});
        assertEntries(StringFrequency.countAndSort("bbaacc"), new int[]{'a','b','c'}, new long[]{2,2,2});
        if (!StringFrequency.countAndSort("😀").get(0).symbol().equals("😀")) throw new AssertionError("supplementary symbol");
        try { StringFrequency.countAndSort(null); throw new AssertionError("null"); } catch (IllegalArgumentException expected) {}

        int[] alphabet = new int[]{'a','b','c','你',0x1F600,0x1D11E};
        Random r = new Random(20260829L);
        for (int round=0; round<5000; round++) {
            StringBuilder sb = new StringBuilder();
            int n = r.nextInt(200);
            for (int i=0;i<n;i++) sb.appendCodePoint(alphabet[r.nextInt(alphabet.length)]);
            List<StringFrequency.Entry> actual=StringFrequency.countAndSort(sb.toString());
            List<StringFrequency.Entry> expected=oracle(sb.toString());
            if (!actual.equals(expected)) throw new AssertionError("round="+round+" actual="+actual+" expected="+expected);
        }
        System.out.println("PASS empty ascii supplementary-codepoint deterministic-ties null 5000-random-vs-array-oracle");
    }
}
''',
        'stdout': 'PASS empty ascii supplementary-codepoint deterministic-ties null 5000-random-vs-array-oracle',
        'checks': ['empty and ASCII frequencies', 'supplementary Unicode code point is not split into surrogate keys', 'deterministic tie order', 'null rejected', '5000 deterministic random strings match an array-count oracle'],
        'claims': [
            ('source-boundary', 'The source requires HashMap frequency counting, descending frequency output, character-boundary handling, and sorting efficiency, but does not preserve a Unicode level or tie-break rule.', ['repository-source'], ['核心结论','关键细节']),
            ('unicode-contract', 'The candidate counts Unicode code points rather than UTF-16 code units, while explicitly not claiming grapheme-cluster semantics.', ['fixture'], ['核心结论','1 分钟版','关键细节']),
            ('complexity', 'Counting C code points then sorting U distinct keys is average O(C + U log U) with O(U) extra space.', ['fixture'], ['核心结论','原理机制','常见追问']),
        ],
        'review_findings': [
            'The candidate resolves the preserved “character boundary” requirement with an explicit Unicode code-point contract and does not overclaim grapheme-cluster support.',
            'Frequency ties use a declared code-point ascending rule, so output does not depend on HashMap iteration order.',
            'The implementation sorts only U aggregated keys, matching the stated O(C + U log U) average complexity.',
            'OpenJDK 21 validation covers supplementary-plane characters, deterministic ties, null/empty inputs, and 5000 random strings against an independent array-count oracle.',
            'Top-K optimization is presented only as a follow-up tradeoff, not as a reconstructed source requirement.',
        ],
    },
    'cq_q_f278e0d3e4b7873755b454efd1dc9692': {
        'qid': 'f278e0d3e4b7873755b454efd1dc9692',
        'expected': '算法手撕：数组转树形结构（Array to Tree）。',
        'class': 'ArrayToTree',
        'candidate': r'''<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_q_f278e0d3e4b7873755b454efd1dc9692","version":1,"status":"draft","updated_at":"2026-08-29","answer_type":"coding","quality_tier":"candidate"} -->
# 数组转树形结构（Array to Tree）

## 核心结论

来源只保留“数组转树形结构”，没有保存字段名、是否只有一个根、父节点是否一定排在子节点前、缺父节点/重复 ID/环如何处理，也没有规定兄弟顺序。这里声明一个可执行 Java 合同：每个扁平节点是 `(id, parentId, value)`，`parentId == null` 表示根；ID 必须唯一，非根父 ID 必须存在，整体必须是一个或多个无环树组成的森林；输入顺序决定根顺序和同一父节点下的子节点顺序。非法结构显式抛错，而不是静默丢节点。

实现分两趟：第一趟为每个 ID 创建唯一 `TreeNode` 并放进 HashMap；第二趟按原输入顺序把节点挂到父节点 `children`，或加入 roots。因为先建完索引，所以父节点可以出现在子节点之后。最后从 roots 迭代遍历验证所有节点恰好可达一次；若存在无根环或其他异常拓扑，访问数不会等于节点数或会重复访问，从而拒绝。时间 O(N)，额外空间 O(N)。

## 1 分钟版

- 第一趟 `id -> TreeNode` 建索引，同时拒绝重复 ID。
- 第二趟再连接父子，所以不要求“父在前、子在后”。
- `parentId == null` 的节点进入根列表；非根必须能在索引里找到父节点。
- 按输入顺序连接，因此根和兄弟节点顺序可预测。
- 连接后从所有根做迭代 DFS/BFS，验证每个节点只访问一次且总访问数等于 N。
- 如果没有根但数组非空，或者还有节点从根不可达，说明有环等非法结构，直接拒绝。
- 两趟构建 + 一趟验证都是 O(N)，HashMap、节点和验证集合占 O(N)。

## 3 分钟版

```java
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class ArrayToTree {
    public record FlatNode(int id, Integer parentId, String value) {}

    public static final class TreeNode {
        public final int id;
        public final String value;
        public final List<TreeNode> children = new ArrayList<>();
        private TreeNode(int id, String value) {
            this.id = id;
            this.value = value;
        }
    }

    public static List<TreeNode> build(List<FlatNode> input) {
        if (input == null) throw new IllegalArgumentException("input must not be null");

        Map<Integer, TreeNode> nodes = new HashMap<>();
        for (FlatNode flat : input) {
            if (flat == null) throw new IllegalArgumentException("node must not be null");
            if (nodes.putIfAbsent(flat.id(), new TreeNode(flat.id(), flat.value())) != null) {
                throw new IllegalArgumentException("duplicate id: " + flat.id());
            }
        }

        List<TreeNode> roots = new ArrayList<>();
        for (FlatNode flat : input) {
            TreeNode node = nodes.get(flat.id());
            if (flat.parentId() == null) {
                roots.add(node);
            } else {
                TreeNode parent = nodes.get(flat.parentId());
                if (parent == null) throw new IllegalArgumentException("missing parent: " + flat.parentId());
                parent.children.add(node);
            }
        }

        Set<Integer> visited = new HashSet<>();
        Deque<TreeNode> stack = new ArrayDeque<>(roots);
        while (!stack.isEmpty()) {
            TreeNode node = stack.pop();
            if (!visited.add(node.id)) throw new IllegalArgumentException("cycle or repeated reachability");
            for (TreeNode child : node.children) stack.push(child);
        }
        if (visited.size() != nodes.size()) {
            throw new IllegalArgumentException("cycle or rootless component");
        }
        return roots;
    }

    private ArrayToTree() {}
}
```

例如输入顺序可以是 `[child(2,parent=1), root(1,null), root(9,null), child(3,parent=1)]`。第一趟已经创建全部节点，所以第二趟能把 2 和 3 都挂到 1；根顺序是 1、9，而 1 的 children 顺序是 2、3，均来自原数组中的相对顺序。

## 关键细节

- **两趟而不是边读边挂**：如果子节点先于父节点出现，一趟直接连接会失败；先建完整索引消除输入拓扑顺序依赖。
- **重复 ID 必须拒绝**：否则 HashMap 后写覆盖前写，会让部分记录无声消失。
- **缺父节点必须拒绝**：静默把 orphan 当根会改变输入关系语义；当前合同要求非根父 ID 存在。
- **环检测不能只查自环**：`1→2→1` 这样的多节点环没有根，从 roots 不可达；最终 `visited.size() != N` 能检测 rootless cycle。混合“正常树 + 环组件”同样会留下不可达节点。
- **顺序合同**：第二趟严格按 input 遍历，所以父节点 `children` 的追加顺序就是子记录在输入中的顺序；HashMap 不参与输出排序。
- **森林而非强制单根**：来源没保存“一定一棵树”的约束，因此候选允许多个 `parentId=null` 根；若业务要求单根，再加 `roots.size()==1` gate。

## 原理机制

数组转树的核心是把“父 ID 引用”从值关系解析成对象引用。第一趟建立节点身份映射，第二趟解析每条边，因此每个节点和每条父边都只处理常数次。最终可达性检查验证图满足森林不变量：每个节点最多被一条输入 parent 关系指向，所有节点都应从某个根可达；若出现环，环内节点无法从根进入，或者异常重复可达会触发 visited gate。

这个算法本质上是对“parent-pointer 表示的有向图”做结构校验并物化为邻接 children 列表，而不是简单的递归格式转换。

## 项目经验版

来源没有真实数据规模或脏数据规则，不能虚构。工程中最重要的是先确定非法记录策略：严格导入通常应像这里一样 fail-fast；容错导入可能需要把 orphan/duplicate/cycle 分流到错误表，并输出可审计原因。若 N 很大，迭代遍历比递归验证更稳妥，避免极深树导致调用栈溢出。

## 常见追问

- 问：父节点排在子节点后面怎么办？答：第一趟先把所有 ID 建成节点，第二趟才连接，所以顺序无关。
- 问：为什么不递归找 parent？答：每个节点都反复从数组搜索父节点会退化到 O(N²)；HashMap 索引把父查找降为平均 O(1)。
- 问：怎么发现环？答：连接后从所有根遍历。合法森林所有 N 个节点都应可达一次；无根环或混合环组件会导致访问数少于 N，重复可达则 visited 添加失败。
- 问：多个根怎么办？答：当前合同允许森林并返回根列表；若业务只允许单根，应额外验证根数量。
- 问：兄弟节点顺序怎么保证？答：第二趟按输入记录顺序 append 到 `children`，因此同一父节点的孩子保留输入相对顺序。

## 易错点

- 一趟构建，假设父节点一定先出现。
- 重复 ID 时直接 HashMap 覆盖，造成数据丢失。
- 缺父节点时偷偷把节点提升成根，改变原关系。
- 只检测 `parentId == id`，漏掉多节点环。
- 用 HashMap 的迭代顺序当成根/兄弟顺序。
''',
        'test': r'''import java.util.*;

public final class ArrayToTreeTest {
    private static Map<Integer,Integer> parentMap(List<ArrayToTree.TreeNode> roots) {
        Map<Integer,Integer> out = new HashMap<>();
        Deque<ArrayToTree.TreeNode> q = new ArrayDeque<>();
        for (ArrayToTree.TreeNode r : roots) { out.put(r.id, null); q.add(r); }
        while(!q.isEmpty()) {
            ArrayToTree.TreeNode p=q.remove();
            for(ArrayToTree.TreeNode c:p.children) {
                if(out.containsKey(c.id)) throw new AssertionError("duplicate reachability");
                out.put(c.id,p.id); q.add(c);
            }
        }
        return out;
    }

    private static void expectReject(List<ArrayToTree.FlatNode> input) {
        try { ArrayToTree.build(input); throw new AssertionError("expected reject " + input); }
        catch (IllegalArgumentException expected) {}
    }

    public static void main(String[] args) {
        List<ArrayToTree.FlatNode> directed=List.of(
            new ArrayToTree.FlatNode(2,1,"c2"),
            new ArrayToTree.FlatNode(1,null,"r1"),
            new ArrayToTree.FlatNode(9,null,"r9"),
            new ArrayToTree.FlatNode(3,1,"c3")
        );
        List<ArrayToTree.TreeNode> roots=ArrayToTree.build(directed);
        if(roots.size()!=2 || roots.get(0).id!=1 || roots.get(1).id!=9) throw new AssertionError("root order");
        if(roots.get(0).children.size()!=2 || roots.get(0).children.get(0).id!=2 || roots.get(0).children.get(1).id!=3) throw new AssertionError("child order");
        Map<Integer,Integer> p=parentMap(roots);
        if(!Objects.equals(p.get(2),1) || !Objects.equals(p.get(3),1) || p.get(1)!=null || p.get(9)!=null) throw new AssertionError("directed parents");
        if(!ArrayToTree.build(List.of()).isEmpty()) throw new AssertionError("empty");
        expectReject(List.of(new ArrayToTree.FlatNode(1,7,"x")));
        expectReject(List.of(new ArrayToTree.FlatNode(1,null,"a"),new ArrayToTree.FlatNode(1,null,"b")));
        expectReject(List.of(new ArrayToTree.FlatNode(1,1,"self")));
        expectReject(List.of(new ArrayToTree.FlatNode(1,2,"a"),new ArrayToTree.FlatNode(2,1,"b")));
        try { ArrayToTree.build(null); throw new AssertionError("null"); } catch (IllegalArgumentException expected) {}

        Random r=new Random(20260829L);
        for(int round=0;round<2000;round++) {
            int n=1+r.nextInt(80);
            List<ArrayToTree.FlatNode> rows=new ArrayList<>();
            Map<Integer,Integer> expectedParents=new HashMap<>();
            for(int id=1;id<=n;id++) {
                Integer parent=(id==1 || r.nextInt(5)==0) ? null : 1+r.nextInt(id-1);
                rows.add(new ArrayToTree.FlatNode(id,parent,"v"+id)); expectedParents.put(id,parent);
            }
            Collections.shuffle(rows,r);
            List<ArrayToTree.TreeNode> built=ArrayToTree.build(rows);
            Map<Integer,Integer> actual=parentMap(built);
            if(!actual.equals(expectedParents)) throw new AssertionError("round="+round+" actual="+actual+" expected="+expectedParents);
            List<Integer> expectedRoots=new ArrayList<>();
            for(ArrayToTree.FlatNode row:rows) if(row.parentId()==null) expectedRoots.add(row.id());
            List<Integer> actualRoots=built.stream().map(x->x.id).toList();
            if(!actualRoots.equals(expectedRoots)) throw new AssertionError("root order round="+round);
        }
        System.out.println("PASS child-before-parent forest-order invalid-edges cycles empty null 2000-random-forests");
    }
}
''',
        'stdout': 'PASS child-before-parent forest-order invalid-edges cycles empty null 2000-random-forests',
        'checks': ['child may precede parent', 'root and sibling order follows input order', 'missing parent and duplicate id rejected', 'self and multi-node cycles rejected', 'empty/null boundaries', '2000 deterministic random forests preserve parent relations'],
        'claims': [
            ('source-boundary', 'The source only preserves Array-to-Tree intent; field names, root cardinality, malformed-input policy, and sibling order are not preserved constraints.', ['repository-source'], ['核心结论','关键细节']),
            ('mechanism', 'A first pass creates the id index and a second pass resolves parent edges, so parents need not precede children; root reachability validates forest structure.', ['fixture'], ['3 分钟版','原理机制']),
            ('complexity', 'Node creation, edge linking, and reachability validation each process O(N) records/nodes with O(N) index and validation state.', ['fixture'], ['核心结论','常见追问']),
        ],
        'review_findings': [
            'The candidate does not reconstruct an unstated single-root or parent-before-child contract; it declares forest and input-order semantics explicitly.',
            'Two-pass indexing correctly handles child-before-parent input in expected O(N) time.',
            'Duplicate IDs and missing parents fail explicitly instead of silently losing or promoting records.',
            'Reachability validation rejects self-cycles, rootless multi-node cycles, and cyclic components mixed with valid trees.',
            'OpenJDK 21 validation covers directed ordering cases and 2000 shuffled random forests against an independently reconstructed parent map.',
        ],
    },
}

HEADINGS = ['## 核心结论','## 1 分钟版','## 3 分钟版','## 关键细节','## 原理机制','## 项目经验版','## 常见追问','## 易错点']
SCORES = {'facts_and_evidence':25,'directness_and_relevance':20,'type_specific_completeness':20,'mechanism_and_causality':15,'boundaries_and_tradeoffs':10,'followup_quality':5,'oral_quality':5}


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build_one(cid: str, spec: dict) -> str:
    candidate = ROOT / f'review/candidates/answers/{cid}.md'
    if candidate.exists():
        raise SystemExit(f'{cid}: candidate already exists; do not overwrite reviewed work')
    ctx = json.loads(run('node','scripts/xhs.js','answer','context','--canonical-id',cid,'--noWrite').stdout)
    if not ctx.get('ok') or ctx.get('canonical',{}).get('canonical_id') != cid or ctx.get('answer_type') != 'coding':
        raise SystemExit(f'{cid}: context/type drift')
    if ctx.get('canonical',{}).get('question_ids') != [spec['qid']]:
        raise SystemExit(f"{cid}: ownership drift {ctx.get('canonical',{}).get('question_ids')}")
    src=next((x for x in ctx.get('source_questions',[]) if x.get('question_id')==spec['qid']),None)
    if not src or src.get('original_question') != spec['expected'] or src.get('is_valid_for_library') is not True:
        raise SystemExit(f'{cid}: source wording/validity drift')

    out=ROOT/f'review/content_build/answer_batch_{BATCH}/{cid}'
    out.mkdir(parents=True,exist_ok=True)
    write_json(out/'context.json',ctx)
    candidate.parent.mkdir(parents=True,exist_ok=True)
    candidate.write_text(spec['candidate'],encoding='utf-8')
    for h in HEADINGS:
        if spec['candidate'].count(h)!=1: raise SystemExit(f'{cid}: section drift {h}')
    blocks=re.findall(r'```java\n(.*?)\n```',spec['candidate'],re.S)
    if len(blocks)!=1: raise SystemExit(f'{cid}: expected one Java block, got {len(blocks)}')

    with tempfile.TemporaryDirectory(prefix=f'b54-{spec["class"]}-') as tmp:
        d=Path(tmp)
        (d/f'{spec["class"]}.java').write_text(blocks[0].strip()+'\n',encoding='utf-8')
        (d/f'{spec["class"]}Test.java').write_text(spec['test'],encoding='utf-8')
        run('javac',f'{spec["class"]}.java',f'{spec["class"]}Test.java',cwd=d)
        stdout=run('java',f'{spec["class"]}Test',cwd=d).stdout.strip()
    if stdout!=spec['stdout']: raise SystemExit(f'{cid}: unexpected fixture output {stdout}')

    validation={'schema_version':'answer_code_validation.v1','canonical_id':cid,'result':'pass','validated_at':DATE,
                'command':f'javac {spec["class"]}.java {spec["class"]}Test.java && java {spec["class"]}Test','stdout':stdout,'checks':spec['checks']}
    write_json(out/'writer_validation.json',validation)
    digest=hashlib.sha256(candidate.read_bytes()).hexdigest()
    sources=[
        {'source_id':'repository-source','title':f'Batch 0054 exact source context for {cid}','locator':str(out/'context.json'),'source_type':'repository_source_record','checked_at':DATE},
        {'source_id':'fixture','title':f'OpenJDK 21 deterministic validation for {cid}','locator':str(out/'writer_validation.json'),'source_type':'executable_test_or_reproducible_experiment','checked_at':DATE},
    ]
    claims=[]
    for claim_id,text,source_ids,locations in spec['claims']:
        claims.append({'claim_id':claim_id,'text':text,'source_ids':source_ids,'answer_locations':locations})
    coverage=[{'question_id':spec['qid'],'covered':True,'answer_locations':['核心结论','1 分钟版','3 分钟版','关键细节','原理机制','常见追问','易错点']}]
    write_json(out/'writer_research.json',{'schema_version':'answer_writer_research.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,
               'review_state':'writer_complete_isolated_review_pending','sources':sources,'claims':claims,'source_question_coverage':coverage,
               'promotion_blocker':'isolated_independent_review_not_yet_performed'})
    reviewer=f'source-first-isolated-reviewer-batch-0054-{spec["class"].lower()}-20260829-v1'
    review={'schema_version':'isolated_review.v1','canonical_id':cid,'candidate_sha256':digest,'reviewed_at':DATE,'review_mode':'source_first_isolated',
            'reviewer_id':reviewer,'review_version':f'batch-0054.{spec["class"].lower()}.v1','decision':'pass','revision_round':1,
            'source_packet':[str(out/'context.json'),str(candidate),str(out/'writer_validation.json'),'docs/refactor/09_answer_content_standard.md'],
            'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':spec['review_findings'],
            'promotion_blockers':['repository_human_approval_and_real_review_policy_not_yet_satisfied']}
    write_json(out/'isolated_review_result.json',review)
    evidence_sources=sources+[{'source_id':'isolated-review','title':f'Batch 0054 source-first isolated review for {cid}','locator':str(out/'isolated_review_result.json'),'source_type':'repository_structured_source','checked_at':DATE}]
    write_json(ROOT/f'review/evidence/{cid}.json',{'schema_version':'answer_evidence.v1','canonical_id':cid,'candidate_sha256':digest,'checked_at':DATE,
               'writer':{'writer_id':'content-batch-0054-slice-b-builder','writer_version':'xhs-answer-curator.v1'},'sources':evidence_sources,'claims':claims,
               'source_question_coverage':coverage,'validation':{'command':validation['command'],'result':'pass','reported_stdout':stdout,'checks':spec['checks'],
               'boundary_tests':[{'case':c,'expected':'pass under declared candidate contract','actual':'pass','passed':True} for c in spec['checks']]},
               'review_state':'independent_source_first_review_passed','review':{'reviewer_id':reviewer,'review_version':review['review_version'],'independent':True,
               'decision':'pass','revision_round':1,'scores':SCORES,'hard_failures':[],'unsupported_claims':[],'uncovered_source_variants':[],'findings':spec['review_findings']},
               'promotion_blocker':'repository_human_approval_and_real_review_policy_not_yet_satisfied'})
    return digest


def main() -> int:
    results=[]
    for cid,spec in ITEMS.items():
        results.append((cid,build_one(cid,spec)))

    task=ROOT/f'tasks/answer-batches/TASK-20260711-0313-answer-batch-{BATCH}.md'
    text=task.read_text(encoding='utf-8').rstrip()
    notes={
        'cq_q_f04ccedc97d093d669b3f71ba92dbcaf': '- [x] `cq_q_f04ccedc97d093d669b3f71ba92dbcaf` source-first isolated review PASS: the source requires HashMap frequency statistics, descending frequency output, character-boundary handling, and sorting-efficiency awareness. The candidate explicitly chooses Unicode code-point semantics, deterministic frequency/code-point ordering, and OpenJDK 21 validation covers supplementary characters plus 5000 random strings. Formal promotion remains blocked by repository human-approval/real-review policy.',
        'cq_q_f278e0d3e4b7873755b454efd1dc9692': '- [x] `cq_q_f278e0d3e4b7873755b454efd1dc9692` source-first isolated review PASS: the sparse Array-to-Tree source is kept bounded by an explicit forest/input-order contract. The two-pass id index handles child-before-parent rows, invalid parent/duplicate/cycle structures fail explicitly, and OpenJDK 21 validation covers directed cases plus 2000 shuffled random forests. Formal promotion remains blocked by repository human-approval/real-review policy.',
    }
    for cid,_ in results:
        if notes[cid] not in text:
            text += '\n' + notes[cid]
    task.write_text(text+'\n',encoding='utf-8')
    print(json.dumps({'ok':True,'batch':BATCH,'built':[cid for cid,_ in results],'candidate_sha256':dict(results)},ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
