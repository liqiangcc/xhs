import java.math.BigInteger;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

public final class CoinChangeCombinations {
    public static BigInteger countCombinations(int amount, int[] coins) {
        if (amount < 0 || coins == null) {
            throw new IllegalArgumentException("amount must be non-negative and coins must be non-null");
        }

        Set<Integer> seen = new HashSet<>();
        for (int coin : coins) {
            if (coin <= 0 || !seen.add(coin)) {
                throw new IllegalArgumentException("coin values must be positive and distinct");
            }
        }

        BigInteger[] dp = new BigInteger[amount + 1];
        Arrays.fill(dp, BigInteger.ZERO);
        dp[0] = BigInteger.ONE;

        for (int coin : coins) {
            for (int sum = coin; sum <= amount; sum++) {
                dp[sum] = dp[sum].add(dp[sum - coin]);
            }
        }
        return dp[amount];
    }
}
