import java.util.Arrays;

public final class CoinChange {
    private CoinChange() {}

    public static int coinChange(int[] coins, int amount) {
        if (coins == null) {
            throw new IllegalArgumentException("coins must not be null");
        }
        if (amount < 0) {
            throw new IllegalArgumentException("amount must be non-negative");
        }

        int unreachable = amount + 1;
        int[] dp = new int[amount + 1];
        Arrays.fill(dp, unreachable);
        dp[0] = 0;

        for (int current = 1; current <= amount; current++) {
            for (int coin : coins) {
                if (coin > 0 && coin <= current) {
                    dp[current] = Math.min(dp[current], dp[current - coin] + 1);
                }
            }
        }
        return dp[amount] == unreachable ? -1 : dp[amount];
    }
}
