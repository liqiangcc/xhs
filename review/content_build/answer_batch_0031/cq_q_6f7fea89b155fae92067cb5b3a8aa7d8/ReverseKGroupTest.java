import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Random;

public final class ReverseKGroupTest {
    private record Built(ReverseKGroup.ListNode head, List<ReverseKGroup.ListNode> nodes) {}

    private static Built build(int n) {
        List<ReverseKGroup.ListNode> nodes = new ArrayList<>();
        ReverseKGroup.ListNode head = null, tail = null;
        for (int i = 0; i < n; i++) {
            var node = new ReverseKGroup.ListNode(i);
            nodes.add(node);
            if (head == null) head = node; else tail.next = node;
            tail = node;
        }
        return new Built(head, nodes);
    }

    private static List<Integer> reference(int n, int k) {
        List<Integer> out = new ArrayList<>();
        for (int start = 0; start < n; start += k) {
            int end = Math.min(n, start + k);
            if (end - start == k) for (int i = end - 1; i >= start; i--) out.add(i);
            else for (int i = start; i < end; i++) out.add(i);
        }
        return out;
    }

    private static void check(int n, int k) {
        Built built = build(n);
        var result = ReverseKGroup.reverseKGroup(built.head(), k);
        List<Integer> values = new ArrayList<>();
        IdentityHashMap<ReverseKGroup.ListNode, Boolean> seen = new IdentityHashMap<>();
        for (var cur = result; cur != null; cur = cur.next) {
            if (seen.put(cur, Boolean.TRUE) != null) throw new AssertionError("cycle detected n=" + n + " k=" + k);
            values.add(cur.val);
            if (values.size() > n) throw new AssertionError("too many nodes");
        }
        if (!values.equals(reference(n, k))) throw new AssertionError("order mismatch n=" + n + " k=" + k + " actual=" + values);
        if (seen.size() != built.nodes().size()) throw new AssertionError("node count/identity lost");
        for (var node : built.nodes()) if (!seen.containsKey(node)) throw new AssertionError("original node identity missing");
    }

    public static void main(String[] args) {
        check(0, 1);
        check(1, 1);
        check(5, 2);
        check(5, 3);
        check(3, 5);
        check(6, 3);
        try { ReverseKGroup.reverseKGroup(null, 0); throw new AssertionError("k=0 must fail"); }
        catch (IllegalArgumentException expected) {}

        Random random = new Random(0x6f7fea89L);
        int cases = 3000;
        for (int t = 0; t < cases; t++) check(random.nextInt(31), 1 + random.nextInt(10));
        System.out.println("PASS fixed=6 random-oracle=3000 identity=preserved cycle=none incomplete-tail=unchanged invalid-k=rejected");
    }
}
