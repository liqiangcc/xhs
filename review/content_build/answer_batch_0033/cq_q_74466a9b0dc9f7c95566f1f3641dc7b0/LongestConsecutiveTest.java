import java.util.Arrays;

public final class LongestConsecutiveTest {
    static int oracle(int[] nums) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        if (nums.length == 0) return 0;
        int[] copy = nums.clone();
        Arrays.sort(copy);
        int best = 1;
        int current = 1;
        for (int i = 1; i < copy.length; i++) {
            if (copy[i] == copy[i - 1]) continue;
            if ((long) copy[i] == (long) copy[i - 1] + 1L) {
                current++;
            } else {
                current = 1;
            }
            if (current > best) best = current;
        }
        return best;
    }

    static void check(int[] input, int expected) {
        int[] before = input.clone();
        int actual = LongestConsecutive.solve(input);
        if (actual != expected) {
            throw new AssertionError(Arrays.toString(input) + " actual=" + actual + " expected=" + expected);
        }
        if (!Arrays.equals(input, before)) throw new AssertionError("input mutated");
    }

    static long exhaustive(int maxLen, int[] alphabet) {
        long checked = 0;
        for (int n = 0; n <= maxLen; n++) {
            int total = 1;
            for (int i = 0; i < n; i++) total *= alphabet.length;
            for (int mask = 0; mask < total; mask++) {
                int t = mask;
                int[] a = new int[n];
                for (int i = 0; i < n; i++) {
                    a[i] = alphabet[t % alphabet.length];
                    t /= alphabet.length;
                }
                int expected = oracle(a);
                int[] before = a.clone();
                int actual = LongestConsecutive.solve(a);
                if (actual != expected || !Arrays.equals(a, before)) {
                    throw new AssertionError("exhaustive mismatch " + Arrays.toString(a) + " actual=" + actual + " expected=" + expected);
                }
                checked++;
            }
        }
        return checked;
    }

    public static void main(String[] args) {
        check(new int[]{100,4,200,1,3,2}, 4);
        check(new int[]{0,3,7,2,5,8,4,6,0,1}, 9);
        check(new int[]{1,2,0,1}, 3);
        check(new int[]{Integer.MIN_VALUE, Integer.MIN_VALUE + 1, Integer.MAX_VALUE}, 2);
        check(new int[]{Integer.MAX_VALUE - 1, Integer.MAX_VALUE, Integer.MIN_VALUE}, 2);
        check(new int[]{5,5,5}, 1);
        long checked = exhaustive(7, new int[]{-2,-1,0,1,2});
        if (checked != 97656L) throw new AssertionError("unexpected exhaustive count " + checked);
        boolean nullThrown = false;
        try { LongestConsecutive.solve(null); } catch (IllegalArgumentException e) { nullThrown = true; }
        if (!nullThrown) throw new AssertionError("null input must be rejected");
        System.out.println("PASS fixed=6 exhaustive=97656 null=rejected input=unmodified int-boundaries=safe");
    }
}
