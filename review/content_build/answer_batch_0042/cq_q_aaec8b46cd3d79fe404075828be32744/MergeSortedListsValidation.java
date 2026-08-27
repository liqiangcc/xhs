import java.util.*;

public final class MergeSortedListsValidation {
    static final class ListNode {
        final int val;
        ListNode next;
        ListNode(int val) { this.val = val; }
    }

    static ListNode mergeRecursive(ListNode a, ListNode b) {
        if (a == null) return b;
        if (b == null) return a;
        if (a.val <= b.val) {
            a.next = mergeRecursive(a.next, b);
            return a;
        }
        b.next = mergeRecursive(a, b.next);
        return b;
    }

    static ListNode mergeIterative(ListNode a, ListNode b) {
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        while (a != null && b != null) {
            if (a.val <= b.val) {
                tail.next = a;
                a = a.next;
            } else {
                tail.next = b;
                b = b.next;
            }
            tail = tail.next;
        }
        tail.next = (a != null) ? a : b;
        return dummy.next;
    }

    static ListNode build(int[] values, Set<ListNode> identities) {
        ListNode dummy = new ListNode(0), tail = dummy;
        for (int v : values) {
            ListNode n = new ListNode(v);
            identities.add(n);
            tail.next = n;
            tail = n;
        }
        return dummy.next;
    }

    static int[] toArrayAndCheck(ListNode head, Set<ListNode> originals, int expectedCount) {
        int[] out = new int[expectedCount];
        Set<ListNode> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        int i = 0;
        for (ListNode p = head; p != null; p = p.next) {
            if (!seen.add(p)) throw new AssertionError("cycle in merged list");
            if (!originals.contains(p)) throw new AssertionError("result contains a newly allocated data node");
            if (i >= expectedCount) throw new AssertionError("too many result nodes");
            out[i++] = p.val;
        }
        if (i != expectedCount) throw new AssertionError("node count mismatch: " + i + " != " + expectedCount);
        return out;
    }

    static int[] expected(int[] a, int[] b) {
        int[] x = new int[a.length + b.length];
        System.arraycopy(a, 0, x, 0, a.length);
        System.arraycopy(b, 0, x, a.length, b.length);
        Arrays.sort(x);
        return x;
    }

    static List<int[]> nondecreasing(int maxLen, int[] domain) {
        List<int[]> out = new ArrayList<>();
        out.add(new int[0]);
        for (int len = 1; len <= maxLen; len++) gen(out, new int[len], 0, 0, domain);
        return out;
    }

    static void gen(List<int[]> out, int[] cur, int index, int minDomainIndex, int[] domain) {
        if (index == cur.length) {
            out.add(cur.clone());
            return;
        }
        for (int i = minDomainIndex; i < domain.length; i++) {
            cur[index] = domain[i];
            gen(out, cur, index + 1, i, domain);
        }
    }

    static void checkCase(int[] a, int[] b) {
        int[] exp = expected(a, b);

        Set<ListNode> recIds = Collections.newSetFromMap(new IdentityHashMap<>());
        ListNode recA = build(a, recIds), recB = build(b, recIds);
        int[] rec = toArrayAndCheck(mergeRecursive(recA, recB), recIds, exp.length);
        if (!Arrays.equals(rec, exp)) throw new AssertionError("recursive mismatch " + Arrays.toString(a) + " + " + Arrays.toString(b));

        Set<ListNode> itIds = Collections.newSetFromMap(new IdentityHashMap<>());
        ListNode itA = build(a, itIds), itB = build(b, itIds);
        int[] it = toArrayAndCheck(mergeIterative(itA, itB), itIds, exp.length);
        if (!Arrays.equals(it, exp)) throw new AssertionError("iterative mismatch " + Arrays.toString(a) + " + " + Arrays.toString(b));
    }

    public static void main(String[] args) {
        List<int[]> lists = nondecreasing(4, new int[]{-2, -1, 0, 1, 2});
        int cases = 0;
        for (int[] a : lists) {
            for (int[] b : lists) {
                checkCase(a, b);
                cases++;
            }
        }
        checkCase(new int[]{Integer.MIN_VALUE, 0, Integer.MAX_VALUE}, new int[]{Integer.MIN_VALUE, Integer.MAX_VALUE});
        cases++;
        System.out.println("PASS cases=" + cases + " recursive=sorted+reuses-nodes iterative=sorted+reuses-nodes nulls+duplicates+extremes=covered");
    }
}
