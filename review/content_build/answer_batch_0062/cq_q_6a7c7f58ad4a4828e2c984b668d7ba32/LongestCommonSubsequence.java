import java.util.Objects;

public final class LongestCommonSubsequence {
    private LongestCommonSubsequence() {}

    public static int lcsLength(String first, String second) {
        if (first == null || second == null) {
            throw new IllegalArgumentException("inputs must be non-null");
        }
        String rows = first;
        String cols = second;
        if (rows.length() < cols.length()) {
            String tmp = rows;
            rows = cols;
            cols = tmp;
        }
        int[] dp = new int[cols.length() + 1];
        for (int i = 1; i <= rows.length(); i++) {
            int prevDiag = 0;
            for (int j = 1; j <= cols.length(); j++) {
                int oldUp = dp[j];
                if (rows.charAt(i - 1) == cols.charAt(j - 1)) {
                    dp[j] = prevDiag + 1;
                } else {
                    dp[j] = Math.max(dp[j], dp[j - 1]);
                }
                prevDiag = oldUp;
            }
        }
        return dp[cols.length()];
    }
}
