import java.util.ArrayList;
import java.util.List;

public final class CoinChange123 {
    public record Combination(int oneCent, int twoCent, int threeCent) {}

    private static final int[] ENUM_COINS = {3, 2, 1};

    public static List<Combination> combinations(int n) {
        if (n < 0) {
            return List.of();
        }
        List<Combination> result = new ArrayList<>();
        collect(n, 0, new int[3], result);
        return result;
    }

    private static void collect(int remaining, int index, int[] counts, List<Combination> out) {
        if (index == ENUM_COINS.length - 1) {
            counts[index] = remaining; // 最后一种是 1 分硬币
            out.add(new Combination(counts[2], counts[1], counts[0]));
            return;
        }

        int coin = ENUM_COINS[index];
        for (int count = 0; count * coin <= remaining; count++) {
            counts[index] = count;
            collect(remaining - count * coin, index + 1, counts, out);
        }
        counts[index] = 0;
    }

    public static long countWaysDp(int n) {
        if (n < 0) {
            return 0L;
        }
        long[] dp = new long[n + 1];
        dp[0] = 1L;
        for (int coin : new int[] {1, 2, 3}) {
            for (int amount = coin; amount <= n; amount++) {
                dp[amount] = Math.addExact(dp[amount], dp[amount - coin]);
            }
        }
        return dp[n];
    }
}
