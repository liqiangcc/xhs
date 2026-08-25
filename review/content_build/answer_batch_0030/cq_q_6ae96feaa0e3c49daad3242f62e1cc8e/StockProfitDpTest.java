import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

public final class StockProfitDpTest {
    public static void main(String[] args) {
        checkExamples();
        checkInvalid();
        long arrays = exhaustiveCrossCheck(6, 4);
        System.out.println("PASS examples=yes invalid=yes exhaustive-arrays=" + arrays + " one=yes unlimited=yes k=yes");
    }

    private static void checkExamples() {
        eq(5, StockProfitDp.maxProfitOne(new int[]{7,1,5,3,6,4}), "one standard");
        eq(7, StockProfitDp.maxProfitUnlimited(new int[]{7,1,5,3,6,4}), "unlimited standard");
        eq(7, StockProfitDp.maxProfitAtMostK(new int[]{7,1,5,3,6,4}, 2), "k standard");
        eq(0, StockProfitDp.maxProfitOne(new int[]{7,6,4,3,1}), "one falling");
        eq(0, StockProfitDp.maxProfitUnlimited(new int[]{}), "empty");
        eq(0, StockProfitDp.maxProfitAtMostK(new int[]{5}, 9), "singleton");
        eq(4, StockProfitDp.maxProfitAtMostK(new int[]{1,2,3,4,5}, 1), "k1 rising");
        eq(4, StockProfitDp.maxProfitAtMostK(new int[]{1,2,3,4,5}, 99), "large k rising");
    }

    private static void checkInvalid() {
        throwsIAE(() -> StockProfitDp.maxProfitOne(null));
        throwsIAE(() -> StockProfitDp.maxProfitUnlimited(new int[]{1,-1,2}));
        throwsIAE(() -> StockProfitDp.maxProfitAtMostK(new int[]{1,2}, -1));
    }

    private static long exhaustiveCrossCheck(int maxLength, int valueKinds) {
        long count = 0;
        for (int n = 0; n <= maxLength; n++) {
            long total = 1;
            for (int i = 0; i < n; i++) total *= valueKinds;
            for (long mask = 0; mask < total; mask++) {
                int[] prices = decode(mask, n, valueKinds);
                long one = brute(prices, 1);
                long unlimited = brute(prices, n / 2 + 1);
                eq(one, StockProfitDp.maxProfitOne(prices), "one " + Arrays.toString(prices));
                eq(unlimited, StockProfitDp.maxProfitUnlimited(prices), "unlimited " + Arrays.toString(prices));
                for (int k = 0; k <= 4; k++) {
                    eq(brute(prices, k), StockProfitDp.maxProfitAtMostK(prices, k), "k=" + k + " " + Arrays.toString(prices));
                }
                count++;
            }
        }
        return count;
    }

    private static int[] decode(long code, int n, int base) {
        int[] a = new int[n];
        for (int i = 0; i < n; i++) {
            a[i] = (int) (code % base);
            code /= base;
        }
        return a;
    }

    private static long brute(int[] prices, int k) {
        return Math.max(0, dfs(prices, 0, false, 0, k, new HashMap<>()));
    }

    private static long dfs(int[] prices, int day, boolean holding, int completed, int k, Map<String, Long> memo) {
        if (day == prices.length) return holding ? Long.MIN_VALUE / 8 : 0;
        String key = day + ":" + holding + ":" + completed + ":" + k;
        Long cached = memo.get(key);
        if (cached != null) return cached;
        long best = dfs(prices, day + 1, holding, completed, k, memo);
        if (!holding && completed < k) {
            long tail = dfs(prices, day + 1, true, completed, k, memo);
            if (tail > Long.MIN_VALUE / 16) best = Math.max(best, tail - prices[day]);
        } else if (holding && completed < k) {
            long tail = dfs(prices, day + 1, false, completed + 1, k, memo);
            if (tail > Long.MIN_VALUE / 16) best = Math.max(best, tail + prices[day]);
        }
        memo.put(key, best);
        return best;
    }

    private static void eq(long expected, long actual, String label) {
        if (expected != actual) throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
    }

    private static void throwsIAE(Runnable r) {
        try { r.run(); throw new AssertionError("expected IllegalArgumentException"); }
        catch (IllegalArgumentException expected) { }
    }
}
