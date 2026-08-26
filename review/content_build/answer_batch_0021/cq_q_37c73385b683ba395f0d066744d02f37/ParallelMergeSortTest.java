import java.util.Arrays;
import java.util.Random;

public final class ParallelMergeSortTest {
    public static void main(String[] args) {
        check(new int[]{}, 4, 8);
        check(new int[]{7}, 2, 1);
        check(new int[]{3, 1, 2, 1, -5, Integer.MAX_VALUE, Integer.MIN_VALUE}, 3, 2);
        check(new int[]{5, 4, 3, 2, 1}, 1, 2);

        Random rnd = new Random(20260826L);
        int cases = 0;
        for (int n = 0; n <= 1024; n += 17) {
            for (int p : new int[]{1, 2, 3, 4, 8}) {
                int[] a = new int[n];
                for (int i = 0; i < n; i++) a[i] = rnd.nextInt(101) - 50;
                check(a, p, Math.max(1, n / 8));
                cases++;
            }
        }

        try {
            ParallelMergeSort.sort(null, 2, 8);
            throw new AssertionError("null");
        } catch (NullPointerException expected) {
        }
        try {
            ParallelMergeSort.sort(new int[]{1}, 0, 8);
            throw new AssertionError("parallelism");
        } catch (IllegalArgumentException expected) {
        }
        try {
            ParallelMergeSort.sort(new int[]{1}, 2, 0);
            throw new AssertionError("threshold");
        } catch (IllegalArgumentException expected) {
        }

        System.out.println("PASS oracle_cases=" + cases + " edges=empty,single,duplicates,extremes descending p=1..8 invalid-args=reject");
    }

    private static void check(int[] input, int p, int threshold) {
        int[] actual = input.clone();
        int[] expected = input.clone();
        Arrays.sort(expected);
        ParallelMergeSort.sort(actual, p, threshold);
        if (!Arrays.equals(actual, expected)) {
            throw new AssertionError(
                "mismatch p=" + p + " threshold=" + threshold +
                " expected=" + Arrays.toString(expected) +
                " actual=" + Arrays.toString(actual)
            );
        }
    }
}
