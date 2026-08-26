# Answer Batch 0021 — K-Group Linked-List Relation Review

## Source-first facts

- `37b42623861093a397be5bff1ee3fad6`: 算法手撕：LeetCode 25 - K 个一组翻转链表。给定一个链表，每 k 个节点一组进行翻转，请返回翻转后的链表
- `47f6e217cc684f406d6472441b015c41`: 算法手撕：K 个一组翻转链表（Reverse Nodes in k-Group）。
- Existing target companion `74dcc97230485151dd50aa5d7664cc0c`: 算法：k个一组翻转链表

The raw source notes independently preserve “LC 25 / K 个一组翻转链表” and “k个一组翻转链表”. No historical merge/remediation record was used to reach the relation conclusion. All three current Questions ask the same coding problem boundary: reverse a singly linked list in groups of k and return the resulting list. The LC25 wording identifies the standard problem but does not introduce a distinct output, data model, or algorithmic objective relative to the existing target Canonical.

## Decision

Relation: `same` between `37b42623861093a397be5bff1ee3fad6` and target bridge `47f6e217cc684f406d6472441b015c41`. Preserve `cq_topic_745b29f7` as the survivor because it already owns two independently recovered k-group Questions. Retire singleton duplicate `cq_q_37b42623861093a397be5bff1ee3fad6` through the reviewed Select → Decide → Apply path. Consolidation must invalidate/rebuild the survivor Answer against all three current source Questions; this relation decision does not itself promote an Answer.
