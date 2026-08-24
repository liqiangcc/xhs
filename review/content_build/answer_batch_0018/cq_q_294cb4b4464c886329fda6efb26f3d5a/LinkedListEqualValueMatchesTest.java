import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class LinkedListEqualValueMatchesTest {
    private static int fixedChecks = 0;

    public static void main(String[] args) {
        check(new int[]{}, new int[]{}, List.of());
        check(new int[]{1, 2, 3}, new int[]{}, List.of());
        check(new int[]{}, new int[]{1, 2, 3}, List.of());
        check(new int[]{1, 2, 3}, new int[]{4, 5, 6}, List.of());
        check(new int[]{1, 2, 3}, new int[]{3, 4, 1}, List.of(
                new LinkedListEqualValueMatches.Match(0, 2, 1),
                new LinkedListEqualValueMatches.Match(2, 0, 3)));
        check(new int[]{2, 2}, new int[]{2, 2, 2}, List.of(
                new LinkedListEqualValueMatches.Match(0, 0, 2),
                new LinkedListEqualValueMatches.Match(0, 1, 2),
                new LinkedListEqualValueMatches.Match(0, 2, 2),
                new LinkedListEqualValueMatches.Match(1, 0, 2),
                new LinkedListEqualValueMatches.Match(1, 1, 2),
                new LinkedListEqualValueMatches.Match(1, 2, 2)));
        check(new int[]{-1, 0, -1}, new int[]{0, -1}, List.of(
                new LinkedListEqualValueMatches.Match(0, 1, -1),
                new LinkedListEqualValueMatches.Match(1, 0, 0),
                new LinkedListEqualValueMatches.Match(2, 1, -1)));

        Random random = new Random(0x294cb4b4L);
        int randomized = 5000;
        for (int iteration = 0; iteration < randomized; iteration++) {
            int[] left = randomValues(random, random.nextInt(31));
            int[] right = randomValues(random, random.nextInt(31));
            List<LinkedListEqualValueMatches.Match> expected = oracle(left, right);
            List<LinkedListEqualValueMatches.Match> actual = LinkedListEqualValueMatches.findAll(
                    LinkedListEqualValueMatches.fromValues(left),
                    LinkedListEqualValueMatches.fromValues(right));
            if (!actual.equals(expected)) {
                throw new AssertionError("randomized mismatch at iteration " + iteration
                        + " left=" + java.util.Arrays.toString(left)
                        + " right=" + java.util.Arrays.toString(right)
                        + " expected=" + expected + " actual=" + actual);
            }
        }

        System.out.println("PASS fixed=" + fixedChecks
                + " randomized=" + randomized
                + " oracle=nested-loop duplicateSemantics=cartesian-pairs order=left-then-right");
    }

    private static void check(
            int[] left,
            int[] right,
            List<LinkedListEqualValueMatches.Match> expected) {
        fixedChecks++;
        LinkedListEqualValueMatches.Node leftHead = LinkedListEqualValueMatches.fromValues(left);
        LinkedListEqualValueMatches.Node rightHead = LinkedListEqualValueMatches.fromValues(right);
        assertDisjoint(leftHead, rightHead);
        List<LinkedListEqualValueMatches.Match> actual = LinkedListEqualValueMatches.findAll(leftHead, rightHead);
        if (!actual.equals(expected)) {
            throw new AssertionError("fixed mismatch expected=" + expected + " actual=" + actual);
        }
    }

    private static void assertDisjoint(
            LinkedListEqualValueMatches.Node left,
            LinkedListEqualValueMatches.Node right) {
        java.util.IdentityHashMap<LinkedListEqualValueMatches.Node, Boolean> identities = new java.util.IdentityHashMap<>();
        for (LinkedListEqualValueMatches.Node node = left; node != null; node = node.next) {
            identities.put(node, Boolean.TRUE);
        }
        for (LinkedListEqualValueMatches.Node node = right; node != null; node = node.next) {
            if (identities.containsKey(node)) {
                throw new AssertionError("fixture lists unexpectedly intersect by node identity");
            }
        }
    }

    private static int[] randomValues(Random random, int size) {
        int[] values = new int[size];
        for (int i = 0; i < size; i++) {
            values[i] = random.nextInt(13) - 6;
        }
        return values;
    }

    private static List<LinkedListEqualValueMatches.Match> oracle(int[] left, int[] right) {
        List<LinkedListEqualValueMatches.Match> matches = new ArrayList<>();
        for (int i = 0; i < left.length; i++) {
            for (int j = 0; j < right.length; j++) {
                if (left[i] == right[j]) {
                    matches.add(new LinkedListEqualValueMatches.Match(i, j, left[i]));
                }
            }
        }
        return List.copyOf(matches);
    }
}
