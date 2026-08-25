import java.util.Arrays;

public final class StockProfitDp {
    private static final long NEG = Long.MIN_VALUE / 4;

    public static long maxProfitOne(int[] prices) {
        requirePrices(prices);
        long hold = NEG;
        long cash = 0;
        for (int price : prices) {
            long oldHold = hold;
            hold = Math.max(oldHold, -(long) price);
            cash = Math.max(cash, oldHold + price);
        }
        return cash;
    }

    public static long maxProfitUnlimited(int[] prices) {
        requirePrices(prices);
        long hold = NEG;
        long cash = 0;
        for (int price : prices) {
            long oldHold = hold;
            long oldCash = cash;
            hold = Math.max(oldHold, oldCash - price);
            cash = Math.max(oldCash, oldHold + price);
        }
        return cash;
    }

    public static long maxProfitAtMostK(int[] prices, int k) {
        requirePrices(prices);
        if (k < 0) throw new IllegalArgumentException("k must be >= 0");
        if (k == 0 || prices.length < 2) return 0;
        if (k >= prices.length / 2) return maxProfitUnlimited(prices);
        long[] buy = new long[k + 1];
        long[] sell = new long[k + 1];
        Arrays.fill(buy, NEG);
        for (int price : prices) {
            long[] oldBuy = buy.clone();
            long[] oldSell = sell.clone();
            for (int t = 1; t <= k; t++) {
                buy[t] = Math.max(oldBuy[t], oldSell[t - 1] - price);
                sell[t] = Math.max(oldSell[t], oldBuy[t] + price);
            }
        }
        return sell[k];
    }

    private static void requirePrices(int[] prices) {
        if (prices == null) throw new IllegalArgumentException("prices must not be null");
        for (int price : prices) if (price < 0) throw new IllegalArgumentException("price must be non-negative");
    }
}
