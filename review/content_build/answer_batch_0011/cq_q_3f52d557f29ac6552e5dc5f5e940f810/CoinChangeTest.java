import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.List;

public final class CoinChangeTest {
    public static void main(String[] args) {
        assertEq(3, CoinChange.coinChange(new int[]{1, 2, 5}, 11), "official example 1");
        assertEq(-1, CoinChange.coinChange(new int[]{2}, 3), "official example 2");
        assertEq(0, CoinChange.coinChange(new int[]{1}, 0), "official example 3");
        assertEq(2, CoinChange.coinChange(new int[]{2, 5, 10, 1}, 3), "order-independent denominations");
        assertEq(-1, CoinChange.coinChange(new int[]{Integer.MAX_VALUE}, 10_000), "oversized denomination");

        int checked = 0;
        for (int mask = 1; mask < (1 << 5); mask++) {
            int[] coins = subset(mask);
            for (int amount = 0; amount <= 30; amount++) {
                int expected = bfsOracle(coins, amount);
                int actual = CoinChange.coinChange(coins, amount);
                if (expected != actual) {
                    throw new AssertionError("mismatch coins=" + java.util.Arrays.toString(coins)
                        + " amount=" + amount + " expected=" + expected + " actual=" + actual);
                }
                checked++;
            }
        }
        System.out.println("PASS exhaustive_cases=" + checked + " denominations_subsets=1..5 amount=0..30");
    }

    private static int[] subset(int mask) {
        List<Integer> values = new ArrayList<>();
        for (int i = 0; i < 5; i++) {
            if ((mask & (1 << i)) != 0) values.add(i + 1);
        }
        int[] out = new int[values.size()];
        for (int i = 0; i < out.length; i++) out[i] = values.get(i);
        return out;
    }

    private static int bfsOracle(int[] coins, int amount) {
        if (amount == 0) return 0;
        boolean[] seen = new boolean[amount + 1];
        ArrayDeque<Integer> queue = new ArrayDeque<>();
        queue.add(0);
        seen[0] = true;
        int depth = 0;
        while (!queue.isEmpty()) {
            int level = queue.size();
            depth++;
            for (int i = 0; i < level; i++) {
                int sum = queue.remove();
                for (int coin : coins) {
                    long nextLong = (long) sum + coin;
                    if (nextLong == amount) return depth;
                    if (nextLong <= 0 || nextLong > amount) continue;
                    int next = (int) nextLong;
                    if (!seen[next]) {
                        seen[next] = true;
                        queue.add(next);
                    }
                }
            }
        }
        return -1;
    }

    private static void assertEq(int expected, int actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
        }
    }
}
