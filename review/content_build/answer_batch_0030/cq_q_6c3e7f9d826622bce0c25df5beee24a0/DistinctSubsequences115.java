public final class DistinctSubsequences115 {
    private static final long LIMIT = (long) Integer.MAX_VALUE + 1;

    public static int numDistinct(String s, String t) {
        if (s == null || t == null) throw new IllegalArgumentException("s/t must not be null");
        if (t.length() > s.length()) return 0;
        long[] dp = new long[t.length() + 1];
        dp[0] = 1;
        for (int i = 0; i < s.length(); i++) {
            int upper = Math.min(t.length(), i + 1);
            for (int j = upper; j >= 1; j--) {
                if (s.charAt(i) == t.charAt(j - 1)) {
                    dp[j] = Math.min(LIMIT, dp[j] + dp[j - 1]);
                }
            }
        }
        if (dp[t.length()] > Integer.MAX_VALUE) throw new ArithmeticException("result exceeds official 32-bit contract");
        return (int) dp[t.length()];
    }
}
