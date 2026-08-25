import java.util.Arrays;
import java.util.Random;

public final class MedianTwoSortedArraysTest {
    private static double reference(int[] a, int[] b) {
        int[] merged = new int[a.length + b.length];
        int i = 0, j = 0, k = 0;
        while (i < a.length || j < b.length) {
            if (j == b.length || (i < a.length && a[i] <= b[j])) merged[k++] = a[i++];
            else merged[k++] = b[j++];
        }
        int n = merged.length;
        if ((n & 1) == 1) return merged[n / 2];
        return ((long) merged[n / 2 - 1] + merged[n / 2]) / 2.0;
    }

    private static void check(int[] a, int[] b) {
        double expected = reference(a, b);
        double actual = MedianTwoSortedArrays.median(a, b);
        if (Double.compare(expected, actual) != 0) throw new AssertionError(Arrays.toString(a) + " / " + Arrays.toString(b) + " expected=" + expected + " actual=" + actual);
    }

    private static int[] randomSorted(Random random, int n) {
        int[] out = new int[n];
        for (int i = 0; i < n; i++) out[i] = random.nextInt(41) - 20;
        Arrays.sort(out);
        return out;
    }

    public static void main(String[] args) {
        check(new int[]{1,3}, new int[]{2});
        check(new int[]{1,2}, new int[]{3,4});
        check(new int[]{}, new int[]{1,2,3,4});
        check(new int[]{0,0}, new int[]{0,0});
        check(new int[]{-5,-3,-1}, new int[]{2,4,6,8});
        check(new int[]{Integer.MIN_VALUE}, new int[]{Integer.MAX_VALUE});
        check(new int[]{Integer.MAX_VALUE}, new int[]{Integer.MAX_VALUE});
        try { MedianTwoSortedArrays.median(new int[]{}, new int[]{}); throw new AssertionError("both empty must fail"); }
        catch (IllegalArgumentException expected) {}
        try { MedianTwoSortedArrays.median(null, new int[]{1}); throw new AssertionError("null must fail"); }
        catch (IllegalArgumentException expected) {}

        Random random = new Random(0x6fef2a66L);
        int cases = 5000;
        for (int t = 0; t < cases; t++) {
            int m = random.nextInt(21), n = random.nextInt(21);
            if (m + n == 0) n = 1;
            check(randomSorted(random, m), randomSorted(random, n));
        }
        System.out.println("PASS fixed=7 random-oracle=5000 odd-even=yes empty-side=yes duplicates=yes extremes=yes overflow-safe=yes invalid-empty-null=rejected");
    }
}
