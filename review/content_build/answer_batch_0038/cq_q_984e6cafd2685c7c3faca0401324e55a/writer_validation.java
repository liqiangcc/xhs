import java.util.*;

class writer_validation {
    static long rob(int[] nums) {
        if (nums == null || nums.length == 0) return 0L;
        long prev2 = 0L;
        long prev1 = 0L;
        for (int money : nums) {
            long take = prev2 + (long) money;
            long skip = prev1;
            long cur = Math.max(skip, take);
            prev2 = prev1;
            prev1 = cur;
        }
        return prev1;
    }

    static long brute(int[] a) {
        if (a == null || a.length == 0) return 0L;
        return brute(a, 0, false);
    }

    static long brute(int[] a, int i, boolean previousTaken) {
        if (i == a.length) return 0L;
        long skip = brute(a, i + 1, false);
        if (previousTaken) return skip;
        long take = (long) a[i] + brute(a, i + 1, true);
        return Math.max(skip, take);
    }

    static void enumerate(int[] a, int i, int[] values, long[] count) {
        if (i == a.length) {
            long got = rob(a), expected = brute(a);
            if (got != expected) throw new AssertionError("mismatch " + Arrays.toString(a) + " got=" + got + " expected=" + expected);
            count[0]++;
            return;
        }
        for (int v : values) {
            a[i] = v;
            enumerate(a, i + 1, values, count);
        }
    }

    public static void main(String[] args) {
        if (rob(null) != 0L) throw new AssertionError("null");
        if (rob(new int[0]) != 0L) throw new AssertionError("empty");
        if (rob(new int[]{2,7,9,3,1}) != 12L) throw new AssertionError("classic");
        if (rob(new int[]{2,1,1,2}) != 4L) throw new AssertionError("non-greedy");
        if (rob(new int[]{-5,-1,-9}) != 0L) throw new AssertionError("negative-skip-all");
        if (rob(new int[]{Integer.MAX_VALUE,0,Integer.MAX_VALUE}) != 4294967294L) throw new AssertionError("long-sum");

        int[] values = {-1,0,1,2};
        long[] exhaustive = {0};
        for (int n = 0; n <= 8; n++) enumerate(new int[n], 0, values, exhaustive);

        Random rnd = new Random(0x984e6cafL);
        int randomized = 2000;
        for (int t = 0; t < randomized; t++) {
            int n = rnd.nextInt(15);
            int[] a = new int[n];
            for (int i = 0; i < n; i++) a[i] = rnd.nextInt(201) - 100;
            long got = rob(a), expected = brute(a);
            if (got != expected) throw new AssertionError("random mismatch " + Arrays.toString(a) + " got=" + got + " expected=" + expected);
        }
        System.out.println("PASS deterministic=6 exhaustive=" + exhaustive[0] + " randomized=" + randomized + " oracle=nonadjacent-subset-bruteforce negative=skip-all return=long");
    }
}
