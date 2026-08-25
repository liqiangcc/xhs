public final class LongestCommonSubstring {
    private LongestCommonSubstring() {}

    public record Result(int length, String substring) {}

    public static Result solve(String a, String b) {
        if (a == null || b == null) throw new IllegalArgumentException("inputs must be non-null");
        if (b.length() > a.length()) {
            Result swapped = solve(b, a);
            return new Result(swapped.length(), swapped.substring());
        }
        int[] dp = new int[b.length() + 1];
        int best = 0;
        int endExclusive = 0;
        for (int i = 1; i <= a.length(); i++) {
            for (int j = b.length(); j >= 1; j--) {
                if (a.charAt(i - 1) == b.charAt(j - 1)) {
                    dp[j] = dp[j - 1] + 1;
                    if (dp[j] > best) {
                        best = dp[j];
                        endExclusive = i;
                    }
                } else {
                    dp[j] = 0;
                }
            }
        }
        return new Result(best, a.substring(endExclusive - best, endExclusive));
    }
}
