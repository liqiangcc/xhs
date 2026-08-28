import java.util.Arrays;

public final class MergeIntervalsTest {
    private static void expect(int[][] expected, int[][] actual, String label) {
        if (!Arrays.deepEquals(expected, actual)) {
            throw new AssertionError(label + " expected=" + Arrays.deepToString(expected)
                    + " actual=" + Arrays.deepToString(actual));
        }
    }

    private static int[][] copy(int[][] input) {
        int[][] out = new int[input.length][];
        for (int i = 0; i < input.length; i++) {
            out[i] = input[i].clone();
        }
        return out;
    }

    public static void main(String[] args) {
        expect(new int[0][], MergeIntervals.merge(null), "null");
        expect(new int[0][], MergeIntervals.merge(new int[0][]), "empty");
        expect(new int[][] {{1, 4}}, MergeIntervals.merge(new int[][] {{1, 4}}), "single");
        expect(new int[][] {{1, 6}, {8, 10}, {15, 18}},
                MergeIntervals.merge(new int[][] {{1, 3}, {2, 6}, {8, 10}, {15, 18}}),
                "standard");
        expect(new int[][] {{1, 5}}, MergeIntervals.merge(new int[][] {{1, 4}, {4, 5}}),
                "touching closed intervals");
        expect(new int[][] {{1, 10}}, MergeIntervals.merge(new int[][] {{2, 3}, {1, 10}, {4, 8}}),
                "containment");
        expect(new int[][] {{1, 8}}, MergeIntervals.merge(new int[][] {{5, 8}, {1, 3}, {2, 6}}),
                "chain");
        int[][] input = {{8, 10}, {1, 3}, {2, 6}};
        int[][] original = copy(input);
        MergeIntervals.merge(input);
        if (!Arrays.deepEquals(original, input)) {
            throw new AssertionError("input order/content must remain unchanged");
        }
        try {
            MergeIntervals.merge(new int[][] {{2, 1}});
            throw new AssertionError("invalid interval should be rejected");
        } catch (IllegalArgumentException expected) {
            // expected
        }
        System.out.println("PASS empty=ok standard=ok touching=merged containment=ok chain=ok input=unchanged invalid=rejected");
    }
}
