import java.util.Arrays;
import java.util.Random;

public final class MedianOfThreeSortedArraysTest {
    private static int fixedCases;
    private static int randomizedCases;

    private static void assertMedian(int[] a, int[] b, int[] c, double expected) {
        int[] aBefore = a.clone();
        int[] bBefore = b.clone();
        int[] cBefore = c.clone();
        double actual = MedianOfThreeSortedArrays.median(a, b, c);
        if (Double.compare(actual, expected) != 0) {
            throw new AssertionError("expected=" + expected + " actual=" + actual
                    + " a=" + Arrays.toString(a)
                    + " b=" + Arrays.toString(b)
                    + " c=" + Arrays.toString(c));
        }
        if (!Arrays.equals(a, aBefore) || !Arrays.equals(b, bBefore) || !Arrays.equals(c, cBefore)) {
            throw new AssertionError("input arrays were modified");
        }
        fixedCases++;
    }

    private static double oracle(int[] a, int[] b, int[] c) {
        int[] all = new int[a.length + b.length + c.length];
        int offset = 0;
        System.arraycopy(a, 0, all, offset, a.length);
        offset += a.length;
        System.arraycopy(b, 0, all, offset, b.length);
        offset += b.length;
        System.arraycopy(c, 0, all, offset, c.length);
        Arrays.sort(all);
        int left = (all.length - 1) / 2;
        int right = all.length / 2;
        return ((long) all[left] + all[right]) / 2.0;
    }

    private static int[] randomSorted(Random random) {
        int length = random.nextInt(21);
        int[] values = new int[length];
        for (int i = 0; i < length; i++) {
            values[i] = random.nextInt(2001) - 1000;
        }
        Arrays.sort(values);
        return values;
    }

    private static void randomCheck() {
        Random random = new Random(20260822L);
        for (int round = 0; round < 5000; round++) {
            int[] a = randomSorted(random);
            int[] b = randomSorted(random);
            int[] c = randomSorted(random);
            if (a.length + b.length + c.length == 0) {
                c = new int[]{random.nextInt(2001) - 1000};
            }
            double expected = oracle(a, b, c);
            double actual = MedianOfThreeSortedArrays.median(a, b, c);
            if (Double.compare(actual, expected) != 0) {
                throw new AssertionError("random mismatch expected=" + expected + " actual=" + actual);
            }
            randomizedCases++;
        }
    }

    private static void assertThrows(Runnable action, Class<? extends Throwable> type) {
        try {
            action.run();
            throw new AssertionError("expected " + type.getSimpleName());
        } catch (Throwable failure) {
            if (!type.isInstance(failure)) {
                throw new AssertionError("expected " + type.getSimpleName() + " but got " + failure, failure);
            }
        }
    }

    public static void main(String[] args) {
        assertMedian(new int[]{1}, new int[]{2}, new int[]{3}, 2.0);
        assertMedian(new int[]{1, 4}, new int[]{2, 5}, new int[]{3, 6}, 3.5);
        assertMedian(new int[]{}, new int[]{1, 2}, new int[]{3}, 2.0);
        assertMedian(new int[]{}, new int[]{}, new int[]{42}, 42.0);
        assertMedian(new int[]{-5, -1}, new int[]{0, 4}, new int[]{2, 9}, 1.0);
        assertMedian(new int[]{1, 1, 1}, new int[]{1, 1}, new int[]{1}, 1.0);
        assertMedian(new int[]{Integer.MIN_VALUE}, new int[]{Integer.MAX_VALUE}, new int[]{}, -0.5);
        assertMedian(new int[]{Integer.MAX_VALUE}, new int[]{Integer.MAX_VALUE}, new int[]{}, (double) Integer.MAX_VALUE);
        assertMedian(new int[]{Integer.MIN_VALUE}, new int[]{Integer.MIN_VALUE}, new int[]{}, (double) Integer.MIN_VALUE);
        assertMedian(new int[]{-10, -3, 7}, new int[]{-8, 0, 9}, new int[]{-7, 2, 20}, 0.0);

        assertThrows(() -> MedianOfThreeSortedArrays.median(null, new int[]{1}, new int[]{2}), NullPointerException.class);
        assertThrows(() -> MedianOfThreeSortedArrays.median(new int[]{}, new int[]{}, new int[]{}), IllegalArgumentException.class);

        randomCheck();
        System.out.println("PASS fixed=" + fixedCases + " randomized=" + randomizedCases
                + " oracle=combined-sort input_immutable=true overflow_safe_average=true");
    }
}
