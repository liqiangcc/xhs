import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;

public final class LRUCacheWriterTest {
    private static final Random RNG = new Random(0x62009E1CL);

    private static final class Oracle extends LinkedHashMap<Integer, Integer> {
        private final int capacity;
        Oracle(int capacity) { super(16, 0.75f, true); this.capacity = capacity; }
        @Override protected boolean removeEldestEntry(Map.Entry<Integer, Integer> eldest) {
            return size() > capacity;
        }
    }

    private static void eq(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        boolean zero = false;
        try { new LRUCache(0); } catch (IllegalArgumentException expected) { zero = true; }
        if (!zero) throw new AssertionError("capacity=0 must be rejected");

        LRUCache c = new LRUCache(2);
        eq(null, c.get(99), "miss");
        c.put(1, 10); c.put(2, 20);
        eq(10, c.get(1), "get-refresh");
        c.put(3, 30);
        eq(null, c.get(2), "evict-lru-after-get");
        eq(10, c.get(1), "keep-refreshed");
        eq(30, c.get(3), "keep-new");
        c.put(1, 11);
        eq(11, c.get(1), "update-value");
        c.put(4, 40);
        eq(null, c.get(3), "update-refreshes-recency");
        eq(2, c.size(), "size-capacity");

        LRUCache one = new LRUCache(1);
        one.put(7, 70); eq(70, one.get(7), "capacity1-hit");
        one.put(8, 80); eq(null, one.get(7), "capacity1-evict"); eq(80, one.get(8), "capacity1-new");

        int operations = 0;
        for (int scenario = 0; scenario < 100; scenario++) {
            int capacity = 1 + RNG.nextInt(8);
            LRUCache actual = new LRUCache(capacity);
            Oracle oracle = new Oracle(capacity);
            for (int step = 0; step < 500; step++) {
                int key = RNG.nextInt(16);
                if (RNG.nextInt(100) < 55) {
                    int value = RNG.nextInt();
                    actual.put(key, value);
                    oracle.put(key, value);
                } else {
                    eq(oracle.get(key), actual.get(key), "random-get-" + scenario + '-' + step);
                }
                if (actual.size() != oracle.size()) {
                    throw new AssertionError("size drift scenario=" + scenario + " step=" + step);
                }
                operations++;
            }
            for (int key = 0; key < 16; key++) {
                eq(oracle.get(key), actual.get(key), "final-key-" + scenario + '-' + key);
            }
        }
        if (operations != 50000) throw new AssertionError("unexpected operation count " + operations);
        System.out.println("PASS fixed=14 random_ops=50000 oracle=LinkedHashMap capacity1=pass update_recency=pass miss=null");
    }
}
