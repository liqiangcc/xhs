import java.util.ArrayList;
import java.util.Arrays;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Random;

public final class OddEvenMonotonicListSortTest {
    private static int fixedChecks;

    public static void main(String[] args) {
        fixedCases();
        randomizedDifferential();
        System.out.println("PASS fixed=" + fixedChecks + " randomized=5000 oracle=full-sort identity=preserved");
    }

    private static void fixedCases() {
        check(new int[] {}, new int[] {});
        check(new int[] {7}, new int[] {7});
        check(new int[] {1, 2}, new int[] {1, 2});
        check(new int[] {3, 1}, new int[] {1, 3});
        check(new int[] {1, 8, 3, 6, 5, 4, 7, 2}, new int[] {1,2,3,4,5,6,7,8});
        check(new int[] {1, 4, 2, 4, 4, 2, 5}, new int[] {1,2,2,4,4,4,5});
        check(new int[] {-5, 4, -1, 2, 3, 0}, new int[] {-5,-1,0,2,3,4});
        check(new int[] {2, 2, 2, 2, 2}, new int[] {2,2,2,2,2});
        check(new int[] {Integer.MIN_VALUE, Integer.MAX_VALUE, 0, -1, Integer.MAX_VALUE},
              new int[] {Integer.MIN_VALUE, -1, 0, Integer.MAX_VALUE, Integer.MAX_VALUE});
    }

    private static void randomizedDifferential() {
        Random random = new Random(0x22931D19L);
        for (int round = 0; round < 5000; round++) {
            int n = random.nextInt(61);
            int oddCount = (n + 1) / 2;
            int evenCount = n / 2;
            int[] odd = new int[oddCount];
            int[] evenAscending = new int[evenCount];
            for (int i = 0; i < oddCount; i++) odd[i] = random.nextInt(41) - 20;
            for (int i = 0; i < evenCount; i++) evenAscending[i] = random.nextInt(41) - 20;
            Arrays.sort(odd);
            Arrays.sort(evenAscending);

            int[] input = new int[n];
            int oi = 0;
            int ei = evenCount - 1;
            for (int i = 0; i < n; i++) {
                input[i] = ((i & 1) == 0) ? odd[oi++] : evenAscending[ei--];
            }

            int[] expected = input.clone();
            Arrays.sort(expected);
            assertSort(input, expected);
        }
    }

    private static void check(int[] input, int[] expected) {
        assertSort(input, expected);
        fixedChecks++;
    }

    private static void assertSort(int[] input, int[] expected) {
        OddEvenMonotonicListSort.Node head = build(input);
        IdentityHashMap<OddEvenMonotonicListSort.Node, Boolean> before = identities(head);
        OddEvenMonotonicListSort.Node sorted = OddEvenMonotonicListSort.sort(head);
        int[] actual = valuesAndValidateAcyclic(sorted, input.length);
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError("expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
        }
        IdentityHashMap<OddEvenMonotonicListSort.Node, Boolean> after = identities(sorted);
        if (before.size() != after.size() || !before.keySet().equals(after.keySet())) {
            throw new AssertionError("node identity set changed");
        }
    }

    private static OddEvenMonotonicListSort.Node build(int[] values) {
        OddEvenMonotonicListSort.Node head = null;
        OddEvenMonotonicListSort.Node tail = null;
        for (int value : values) {
            OddEvenMonotonicListSort.Node node = new OddEvenMonotonicListSort.Node(value);
            if (head == null) head = node;
            else tail.next = node;
            tail = node;
        }
        return head;
    }

    private static IdentityHashMap<OddEvenMonotonicListSort.Node, Boolean> identities(OddEvenMonotonicListSort.Node head) {
        IdentityHashMap<OddEvenMonotonicListSort.Node, Boolean> ids = new IdentityHashMap<>();
        OddEvenMonotonicListSort.Node current = head;
        while (current != null) {
            if (ids.put(current, Boolean.TRUE) != null) {
                throw new AssertionError("cycle detected while collecting identities");
            }
            current = current.next;
        }
        return ids;
    }

    private static int[] valuesAndValidateAcyclic(OddEvenMonotonicListSort.Node head, int expectedLength) {
        List<Integer> values = new ArrayList<>();
        IdentityHashMap<OddEvenMonotonicListSort.Node, Boolean> seen = new IdentityHashMap<>();
        OddEvenMonotonicListSort.Node current = head;
        while (current != null) {
            if (seen.put(current, Boolean.TRUE) != null) throw new AssertionError("cycle detected");
            values.add(current.value);
            current = current.next;
            if (values.size() > expectedLength) throw new AssertionError("unexpected extra nodes");
        }
        if (values.size() != expectedLength) throw new AssertionError("node count changed");
        int[] out = new int[values.size()];
        for (int i = 0; i < out.length; i++) out[i] = values.get(i);
        return out;
    }
}
