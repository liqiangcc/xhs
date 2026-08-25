import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class CartMerger {
    public record CartLine(String skuId, int quantity) {}

    public static List<CartLine> merge(
            List<CartLine> accountCart,
            List<CartLine> guestCart,
            int maxPerSku) {
        if (accountCart == null || guestCart == null) {
            throw new IllegalArgumentException("carts must not be null");
        }
        if (maxPerSku <= 0) {
            throw new IllegalArgumentException("maxPerSku must be > 0");
        }

        Map<String, Integer> merged = new LinkedHashMap<>();
        addAll(merged, accountCart, maxPerSku);
        addAll(merged, guestCart, maxPerSku);

        List<CartLine> result = new ArrayList<>(merged.size());
        for (Map.Entry<String, Integer> entry : merged.entrySet()) {
            result.add(new CartLine(entry.getKey(), entry.getValue()));
        }
        return result;
    }

    private static void addAll(
            Map<String, Integer> merged,
            List<CartLine> cart,
            int maxPerSku) {
        for (CartLine line : cart) {
            if (line == null || line.skuId() == null || line.skuId().isBlank()) {
                throw new IllegalArgumentException("skuId must not be blank");
            }
            if (line.quantity() <= 0) {
                throw new IllegalArgumentException("quantity must be > 0");
            }
            int current = merged.getOrDefault(line.skuId(), 0);
            long sum = (long) current + line.quantity();
            merged.put(line.skuId(), (int) Math.min(maxPerSku, sum));
        }
    }
}
