import java.util.*;

public final class IntegerBreak {
    public static long solve(int n) {
        if (n < 2 || n > 53) throw new IllegalArgumentException("n must be in [2, 53]");
        long[] dp = new long[n + 1];
        for (int i = 2; i <= n; i++) {
            for (int j = 1; j < i; j++) {
                long stop = (long) j * (i - j);
                long keep = (long) j * dp[i - j];
                dp[i] = Math.max(dp[i], Math.max(stop, keep));
            }
        }
        return dp[n];
    }

    static long brute(int remaining, boolean alreadySplit, Map<String, Long> memo) {
        String key = remaining + ":" + alreadySplit;
        if (memo.containsKey(key)) return memo.get(key);
        long best = alreadySplit ? remaining : Long.MIN_VALUE;
        for (int first = 1; first < remaining; first++) {
            long rest = brute(remaining - first, true, memo);
            best = Math.max(best, first * rest);
        }
        memo.put(key, best);
        return best;
    }

    static long formula(int n) {
        if (n == 2) return 1;
        if (n == 3) return 2;
        long product = 1;
        while (n > 4) { product *= 3; n -= 3; }
        return product * n;
    }

    public static void main(String[] args) {
        long[] small = {0,0,1,2,4,6,9,12,18,27,36};
        for (int n = 2; n <= 10; n++) if (solve(n) != small[n]) throw new AssertionError("small n=" + n);
        for (int n = 2; n <= 16; n++) {
            long brute = brute(n, false, new HashMap<>());
            if (solve(n) != brute) throw new AssertionError("brute mismatch n=" + n + " dp=" + solve(n) + " brute=" + brute);
        }
        for (int n = 2; n <= 53; n++) if (solve(n) != formula(n)) throw new AssertionError("formula mismatch n=" + n);
        if (solve(53) != 258_280_326L) throw new AssertionError("n=53 bound mismatch " + solve(53));
        try { solve(1); throw new AssertionError("n=1 must reject"); } catch (IllegalArgumentException expected) {}
        try { solve(54); throw new AssertionError("n=54 must reject"); } catch (IllegalArgumentException expected) {}
        System.out.println("PASS n=2..10 known n=2..16 brute n=2..53 math upper=258280326 invalid-range=rejected");
    }
}
