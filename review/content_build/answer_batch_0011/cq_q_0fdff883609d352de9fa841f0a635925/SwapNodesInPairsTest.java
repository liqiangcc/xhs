import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Set;

public final class SwapNodesInPairsTest {
    public static void main(String[] args) {
        deterministic();
        generatedOracle();
        System.out.println("PASS deterministic_cases=6 oracle_lengths=65 max_length=64");
    }

    static void deterministic() {
        check(new int[]{}, new int[]{});
        check(new int[]{1}, new int[]{1});
        check(new int[]{1, 2}, new int[]{2, 1});
        check(new int[]{1, 2, 3}, new int[]{2, 1, 3});
        check(new int[]{1, 2, 3, 4}, new int[]{2, 1, 4, 3});
        check(new int[]{7, 7, 7, 7, 7}, new int[]{7, 7, 7, 7, 7});
    }

    static void generatedOracle() {
        for (int n = 0; n <= 64; n++) {
            SwapNodesInPairs.ListNode[] nodes = new SwapNodesInPairs.ListNode[n];
            for (int i = 0; i < n; i++) {
                nodes[i] = new SwapNodesInPairs.ListNode(i % 5);
            }
            for (int i = 0; i + 1 < n; i++) {
                nodes[i].next = nodes[i + 1];
            }
            SwapNodesInPairs.ListNode head = n == 0 ? null : nodes[0];
            List<SwapNodesInPairs.ListNode> actual = collect(SwapNodesInPairs.swapPairs(head), n);
            List<SwapNodesInPairs.ListNode> expected = new ArrayList<>();
            for (int i = 0; i < n; i += 2) {
                if (i + 1 < n) {
                    expected.add(nodes[i + 1]);
                    expected.add(nodes[i]);
                } else {
                    expected.add(nodes[i]);
                }
            }
            if (actual.size() != expected.size()) fail("size n=" + n);
            for (int i = 0; i < n; i++) {
                if (actual.get(i) != expected.get(i)) fail("identity order n=" + n + " i=" + i);
            }
            Set<SwapNodesInPairs.ListNode> identities = Collections.newSetFromMap(new IdentityHashMap<>());
            identities.addAll(actual);
            if (identities.size() != n) fail("identity set/cycle n=" + n);
        }
    }

    static void check(int[] input, int[] expectedValues) {
        SwapNodesInPairs.ListNode[] nodes = new SwapNodesInPairs.ListNode[input.length];
        for (int i = 0; i < input.length; i++) {
            nodes[i] = new SwapNodesInPairs.ListNode(input[i]);
        }
        for (int i = 0; i + 1 < input.length; i++) {
            nodes[i].next = nodes[i + 1];
        }
        SwapNodesInPairs.ListNode head = input.length == 0 ? null : nodes[0];
        List<SwapNodesInPairs.ListNode> actual = collect(SwapNodesInPairs.swapPairs(head), input.length);
        if (actual.size() != expectedValues.length) fail("deterministic size");
        for (int i = 0; i < expectedValues.length; i++) {
            if (actual.get(i).val != expectedValues[i]) fail("deterministic value");
        }
        Set<SwapNodesInPairs.ListNode> original = Collections.newSetFromMap(new IdentityHashMap<>());
        original.addAll(Arrays.asList(nodes));
        Set<SwapNodesInPairs.ListNode> returned = Collections.newSetFromMap(new IdentityHashMap<>());
        returned.addAll(actual);
        if (!original.equals(returned)) fail("deterministic identity set");
    }

    static List<SwapNodesInPairs.ListNode> collect(SwapNodesInPairs.ListNode head, int expectedMax) {
        List<SwapNodesInPairs.ListNode> out = new ArrayList<>();
        Set<SwapNodesInPairs.ListNode> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        for (SwapNodesInPairs.ListNode p = head; p != null; p = p.next) {
            if (!seen.add(p)) fail("cycle");
            out.add(p);
            if (out.size() > expectedMax + 1) fail("too many nodes");
        }
        return out;
    }

    static void fail(String message) {
        throw new AssertionError(message);
    }
}
