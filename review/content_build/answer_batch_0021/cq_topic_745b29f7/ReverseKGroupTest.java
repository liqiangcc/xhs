import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public final class ReverseKGroupTest {
    private static List<ReverseKGroup.ListNode> makeNodes(int n) {
        List<ReverseKGroup.ListNode> nodes = new ArrayList<>();
        for (int i = 0; i < n; i++) nodes.add(new ReverseKGroup.ListNode(1000 + i));
        for (int i = 0; i + 1 < n; i++) nodes.get(i).next = nodes.get(i + 1);
        return nodes;
    }

    private static List<ReverseKGroup.ListNode> oracle(List<ReverseKGroup.ListNode> input, int k) {
        List<ReverseKGroup.ListNode> expected = new ArrayList<>();
        for (int start = 0; start < input.size(); start += k) {
            int end = Math.min(start + k, input.size());
            if (end - start == k) {
                for (int i = end - 1; i >= start; i--) expected.add(input.get(i));
            } else {
                for (int i = start; i < end; i++) expected.add(input.get(i));
            }
        }
        return expected;
    }

    private static List<ReverseKGroup.ListNode> collect(ReverseKGroup.ListNode head, int expectedSize) {
        List<ReverseKGroup.ListNode> out = new ArrayList<>();
        Set<ReverseKGroup.ListNode> seen = new HashSet<>();
        for (ReverseKGroup.ListNode p = head; p != null; p = p.next) {
            if (!seen.add(p)) throw new AssertionError("cycle detected");
            out.add(p);
            if (out.size() > expectedSize) throw new AssertionError("output longer than input");
        }
        if (out.size() != expectedSize) throw new AssertionError("node count drifted: " + out.size() + " vs " + expectedSize);
        return out;
    }

    private static void check(int n, int k) {
        List<ReverseKGroup.ListNode> input = makeNodes(n);
        int[] originalValues = input.stream().mapToInt(x -> x.value).toArray();
        List<ReverseKGroup.ListNode> expected = oracle(input, k);
        ReverseKGroup.ListNode actualHead = ReverseKGroup.reverseKGroup(n == 0 ? null : input.get(0), k);
        List<ReverseKGroup.ListNode> actual = collect(actualHead, n);
        if (!actual.equals(expected)) throw new AssertionError("identity order mismatch n=" + n + " k=" + k);
        if (!new HashSet<>(actual).equals(new HashSet<>(input))) throw new AssertionError("node identity set changed n=" + n + " k=" + k);
        for (int i = 0; i < input.size(); i++) {
            if (input.get(i).value != originalValues[i]) throw new AssertionError("node value mutated n=" + n + " k=" + k);
        }
    }

    public static void main(String[] args) {
        for (int n = 0; n <= 40; n++) {
            for (int k = 1; k <= 12; k++) check(n, k);
        }
        try {
            ReverseKGroup.reverseKGroup(null, 0);
            throw new AssertionError("k=0 must be rejected by declared contract");
        } catch (IllegalArgumentException expected) {}
        try {
            ReverseKGroup.reverseKGroup(null, -3);
            throw new AssertionError("negative k must be rejected by declared contract");
        } catch (IllegalArgumentException expected) {}
        System.out.println("PASS lengths=0..40 k=1..12 oracle=identity-order nodes=preserved values=preserved cycle=none invalid-k=reject");
    }
}
