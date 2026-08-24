import java.util.ArrayList;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;

public final class ReorderListTest {
    public static void main(String[] args) {
        check(new int[]{1}, new int[]{1}, "single");
        check(new int[]{1, 2}, new int[]{1, 2}, "two");
        check(new int[]{1, 2, 3}, new int[]{1, 3, 2}, "odd-three");
        check(new int[]{1, 2, 3, 4}, new int[]{1, 4, 2, 3}, "official-even");
        check(new int[]{1, 2, 3, 4, 5}, new int[]{1, 5, 2, 4, 3}, "official-odd");
        check(new int[]{7, 7, 7, 7, 7, 7}, new int[]{7, 7, 7, 7, 7, 7}, "duplicate-values-identity-sensitive");

        int exhaustive = 0;
        for (int n = 1; n <= 64; n++) {
            int[] values = new int[n];
            for (int i = 0; i < n; i++) values[i] = i + 1;
            check(values, oracle(values), "oracle-n=" + n);
            exhaustive++;
        }
        System.out.println("PASS deterministic_cases=6 oracle_lengths=" + exhaustive + " max_length=64");
    }

    private static void check(int[] input, int[] expected, String label) {
        ReorderList.ListNode head = build(input);
        List<ReorderList.ListNode> originalNodes = nodes(head);
        int[] originalValues = originalNodes.stream().mapToInt(node -> node.val).toArray();

        ReorderList.reorderList(head);

        List<ReorderList.ListNode> reorderedNodes = nodesNoCycle(head, originalNodes.size(), label);
        if (reorderedNodes.size() != originalNodes.size()) {
            throw new AssertionError(label + ": node count changed");
        }
        Set<ReorderList.ListNode> originalIdentity = Collections.newSetFromMap(new IdentityHashMap<>());
        originalIdentity.addAll(originalNodes);
        Set<ReorderList.ListNode> reorderedIdentity = Collections.newSetFromMap(new IdentityHashMap<>());
        reorderedIdentity.addAll(reorderedNodes);
        if (!originalIdentity.equals(reorderedIdentity)) {
            throw new AssertionError(label + ": nodes were replaced or lost");
        }
        for (int i = 0; i < originalNodes.size(); i++) {
            if (originalNodes.get(i).val != originalValues[i]) {
                throw new AssertionError(label + ": a node value was modified");
            }
        }

        int[] actual = reorderedNodes.stream().mapToInt(node -> node.val).toArray();
        if (!java.util.Arrays.equals(expected, actual)) {
            throw new AssertionError(label + ": expected=" + java.util.Arrays.toString(expected)
                + " actual=" + java.util.Arrays.toString(actual));
        }
    }

    private static ReorderList.ListNode build(int[] values) {
        ReorderList.ListNode dummy = new ReorderList.ListNode(0);
        ReorderList.ListNode tail = dummy;
        for (int value : values) {
            tail.next = new ReorderList.ListNode(value);
            tail = tail.next;
        }
        return dummy.next;
    }

    private static List<ReorderList.ListNode> nodes(ReorderList.ListNode head) {
        List<ReorderList.ListNode> out = new ArrayList<>();
        for (ReorderList.ListNode node = head; node != null; node = node.next) out.add(node);
        return out;
    }

    private static List<ReorderList.ListNode> nodesNoCycle(ReorderList.ListNode head, int expectedCount, String label) {
        List<ReorderList.ListNode> out = new ArrayList<>();
        Set<ReorderList.ListNode> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        for (ReorderList.ListNode node = head; node != null; node = node.next) {
            if (!seen.add(node)) throw new AssertionError(label + ": cycle detected");
            out.add(node);
            if (out.size() > expectedCount) throw new AssertionError(label + ": unexpected extra node");
        }
        return out;
    }

    private static int[] oracle(int[] input) {
        int[] out = new int[input.length];
        int left = 0;
        int right = input.length - 1;
        int index = 0;
        while (left <= right) {
            out[index++] = input[left++];
            if (left <= right) out[index++] = input[right--];
        }
        return out;
    }
}
