<!-- xhs-answer: {"schema_version":"answer.v1","canonical_id":"cq_lru_cache_0ef78597","version":1,"status":"ready","updated_at":"2026-07-10"} -->
# 算法：实现 LRU Cache

## 核心结论

LRU Cache 用 HashMap O(1) 定位节点、双向链表 O(1) 删除和移动；链表头保存最近使用，尾部淘汰最久未使用。

## 1 分钟版

- get 命中后把节点移动到头部，未命中返回 -1。
- put 已存在则更新并移头；新增后超过容量则删除尾节点及 map 项。
- 使用 dummy head/tail 统一空链表和边界删除。

## 3 分钟版

不变量是 map 与链表节点一一对应，链表从新到旧有序；每次访问只删除并插入一个节点。 先声明输入约束和不变量，再逐步推导实现；最后给出复杂度、空值/极值用例和至少一个变体。

```java
import java.util.*;
class LRUCache {
    static class Node { int k,v; Node p,n; Node(int k,int v){this.k=k;this.v=v;} }
    private final int cap; private final Map<Integer,Node> map=new HashMap<>();
    private final Node head=new Node(0,0), tail=new Node(0,0);
    LRUCache(int capacity){cap=capacity; head.n=tail; tail.p=head;}
    int get(int key){Node x=map.get(key); if(x==null)return -1; moveFirst(x); return x.v;}
    void put(int key,int value){Node x=map.get(key); if(x!=null){x.v=value;moveFirst(x);return;} x=new Node(key,value);map.put(key,x);addFirst(x);if(map.size()>cap){Node old=tail.p;remove(old);map.remove(old.k);}}
    private void moveFirst(Node x){remove(x);addFirst(x);}
    private void addFirst(Node x){x.n=head.n;x.p=head;head.n.p=x;head.n=x;}
    private void remove(Node x){x.p.n=x.n;x.n.p=x.p;}
}
```

## 关键细节

- get 命中后把节点移动到头部，未命中返回 -1。
- put 已存在则更新并移头；新增后超过容量则删除尾节点及 map 项。
- 使用 dummy head/tail 统一空链表和边界删除。
- 容量必须大于 0；key/value 为 int 的基础题可用 -1 表示未命中。
- 复杂度：get/put 平均 O(1)，空间 O(capacity)

## 原理机制

正确性由循环/状态不变量保证；每次迭代只做保持不变量的局部更新，结束条件把局部结论扩展到完整输入。 LRU Cache 用 HashMap O(1) 定位节点、双向链表 O(1) 删除和移动；链表头保存最近使用，尾部淘汰最久未使用。
- 复杂度：get/put 平均 O(1)，空间 O(capacity)

## 项目经验版

算法训练映射：先口述不变量，再手写 Java 并用边界用例走查；算法训练不应被包装成虚构项目经历。

## 常见追问

- 问：为什么需要双向链表？答：已知节点时可 O(1) 找到前驱并删除，单链表不能直接做到。
- 问：并发怎么处理？答：基础实现非线程安全，可整锁、分段或使用成熟缓存库并定义淘汰近似语义。
- 问：LFU 怎么做？答：增加频次桶，每个频次内部再用双向链表维护最近使用。

## 易错点

- 不要只给代码而不解释不变量。
- 不要遗漏复杂度、空输入和变体。
- 淘汰时必须同时删除 map。
