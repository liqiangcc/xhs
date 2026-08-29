import java.math.BigInteger;

public final class UniqueBsts {
    private UniqueBsts() {}

    public static BigInteger countUniqueBsts(int n) {
        if (n < 0) throw new IllegalArgumentException("n must be >= 0");
        BigInteger[] dp = new BigInteger[n + 1];
        dp[0] = BigInteger.ONE;
        for (int nodes = 1; nodes <= n; nodes++) {
            BigInteger total = BigInteger.ZERO;
            for (int left = 0; left < nodes; left++) {
                int right = nodes - 1 - left;
                total = total.add(dp[left].multiply(dp[right]));
            }
            dp[nodes] = total;
        }
        return dp[n];
    }
}
