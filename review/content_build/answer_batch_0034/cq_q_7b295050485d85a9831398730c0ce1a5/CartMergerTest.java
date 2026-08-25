import java.util.ArrayList;
import java.util.List;

public final class CartMergerTest {
    private static CartMerger.CartLine line(String sku, int qty) { return new CartMerger.CartLine(sku, qty); }
    private static void eq(Object actual, Object expected, String name) {
        if (!actual.equals(expected)) throw new AssertionError(name + " expected=" + expected + " actual=" + actual);
    }
    private static void throwsIAE(Runnable r, String name) {
        try { r.run(); throw new AssertionError(name + " expected IllegalArgumentException"); }
        catch (IllegalArgumentException expected) { }
    }
    public static void main(String[] args) {
        var account = new ArrayList<>(List.of(line("A",2), line("B",1)));
        var guest = new ArrayList<>(List.of(line("A",3), line("C",4)));
        eq(CartMerger.merge(account, guest, 5), List.of(line("A",5), line("B",1), line("C",4)), "cross-cart merge/order/cap");
        eq(account, List.of(line("A",2), line("B",1)), "account input unchanged");
        eq(guest, List.of(line("A",3), line("C",4)), "guest input unchanged");
        eq(CartMerger.merge(List.of(line("A",1),line("A",2)), List.of(), 10), List.of(line("A",3)), "duplicate within one cart");
        eq(CartMerger.merge(List.of(), List.of(line("X",Integer.MAX_VALUE)), 7), List.of(line("X",7)), "large quantity saturation");
        eq(CartMerger.merge(List.of(), List.of(), 3), List.of(), "empty carts");
        throwsIAE(() -> CartMerger.merge(null, List.of(), 3), "null cart");
        throwsIAE(() -> CartMerger.merge(List.of(), List.of(), 0), "invalid cap");
        throwsIAE(() -> CartMerger.merge(List.of(line("",1)), List.of(), 3), "blank sku");
        throwsIAE(() -> CartMerger.merge(List.of(line("A",0)), List.of(), 3), "non-positive quantity");
        System.out.println("PASS cart-merge aggregate duplicates cap ordering immutable-input validation overflow-safe");
    }
}
