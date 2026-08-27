import java.util.Arrays;

final class HeapSortWriterTest {
    private static void check(int[] input) {
        int[] actual = input.clone();
        Solution.sortDescending(actual);

        int[] expected = input.clone();
        Arrays.sort(expected);
        for (int i = 0, j = expected.length - 1; i < j; i++, j--) {
            int t = expected[i]; expected[i] = expected[j]; expected[j] = t;
        }
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError("input=" + Arrays.toString(input)
                + " actual=" + Arrays.toString(actual)
                + " expected=" + Arrays.toString(expected));
        }
    }

    private static void enumerate(int[] a, int index, int[] values) {
        if (index == a.length) {
            check(a);
            return;
        }
        for (int v : values) {
            a[index] = v;
            enumerate(a, index + 1, values);
        }
    }

    public static void main(String[] args) {
        check(new int[]{});
        check(new int[]{7});
        check(new int[]{3, 1, 2});
        check(new int[]{5, 5, 5, 5});
        check(new int[]{-1, 7, 0, -8, 7, Integer.MIN_VALUE, Integer.MAX_VALUE});
        check(new int[]{9, 8, 7, 6, 5});
        check(new int[]{1, 2, 3, 4, 5});

        int[] values = {-2, -1, 0, 1, 2};
        for (int len = 0; len <= 6; len++) {
            enumerate(new int[len], 0, values);
        }

        boolean threw = false;
        try {
            Solution.sortDescending(null);
        } catch (IllegalArgumentException expected) {
            threw = true;
        }
        if (!threw) throw new AssertionError("null must be rejected");

        System.out.println("PASS fixed-boundaries=7 exhaustive-arrays=19531 oracle=Arrays.sort+reverse null=rejected");
    }
}
