import java.util.Arrays;
import java.util.List;

public final class ThreeSumTest {
    private ThreeSumTest() {}

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    private static void requireTriples(int[] input, String expected) {
        int[] before = input == null ? null : Arrays.copyOf(input, input.length);
        List<List<Integer>> actual = ThreeSum.threeSum(input);
        require(actual.toString().equals(expected), "expected " + expected + " but was " + actual);
        if (input != null) require(Arrays.equals(input, before), "threeSum must not mutate caller input");
    }

    public static void main(String[] args) {
        requireTriples(null, "[]");
        requireTriples(new int[] {}, "[]");
        requireTriples(new int[] {-1, 0, 1, 2, -1, -4}, "[[-1, -1, 2], [-1, 0, 1]]");
        requireTriples(new int[] {0, 0, 0, 0}, "[[0, 0, 0]]");
        requireTriples(new int[] {Integer.MIN_VALUE, Integer.MAX_VALUE, 1, -1, 0}, "[[-2147483648, 1, 2147483647], [-1, 0, 1]]");
        require(ThreeSum.threeSumTarget(new int[] {1, 2, 3}, 6).toString().equals("[[1, 2, 3]]"), "target variant must not use zero-target early exit");
    }
}
