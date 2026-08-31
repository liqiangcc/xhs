import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

public final class DoublyLinkedLRUReviewerTest {
    private static final Random RNG = new Random(0x62AD98FCL ^ 0x7E11A9L);

    private static final class Oracle {
        private final int capacity;
        private final Map<Integer, Integer> values = new HashMap<>();
        private final List<Integer> recency = new ArrayList<>(); // MRU -> LRU
        Oracle(int capacity) { this.capacity = capacity; }
        Integer get(int key) {
            if (!values.containsKey(key)) return null;
            Integer value = values.get(key);
            recency.remove(Integer.valueOf(key));
            recency.add(0, key);
            return value;
        }
        void put(int key, int value) {
            if (values.containsKey(key)) {
                values.put(key, value);
                recency.remove(Integer.valueOf(key));
                recency.add(0, key);
                return;
            }
            if (values.size() == capacity) {
                int victim = recency.remove(recency.size() - 1);
                values.remove(victim);
            }
            values.put(key, value);
            recency.add(0, key);
        }
        int size() { return values.size(); }
    }

    private static void eq(Object expected, Object actual, String label) {
        if (expected == null ? actual != null : !expected.equals(actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }

    public static void main(String[] args) {
        boolean zero = false, negative = false;
        try { new LRUCache(0); } catch (IllegalArgumentException expected) { zero = true; }
        try { new LRUCache(-3); } catch (IllegalArgumentException expected) { negative = true; }
        if (!zero || !negative) throw new AssertionError("non-positive capacity contract not enforced");

        LRUCache c = new LRUCache(2);
        eq(null, c.get(99), "initial-miss");
        c.put(1, 10); c.put(2, 20); eq(2, c.size(), "size-two");
        eq(10, c.get(1), "read-refreshes-one");
        c.put(3, 30); eq(null, c.get(2), "two-is-lru-after-read");
        eq(10, c.get(1), "one-survives"); eq(30, c.get(3), "three-present");
        c.put(1, 11); eq(11, c.get(1), "update-value");
        c.put(4, 40); eq(null, c.get(3), "update-refreshes-one");
        eq(11, c.get(1), "updated-one-survives"); eq(40, c.get(4), "four-present");
        eq(2, c.size(), "size-stays-capacity");

        LRUCache one = new LRUCache(1);
        one.put(7, 70); eq(70, one.get(7), "capacity1-hit");
        one.put(8, 80); eq(null, one.get(7), "capacity1-evict"); eq(80, one.get(8), "capacity1-new");

        int operations = 0;
        for (int scenario = 0; scenario < 90; scenario++) {
            int capacity = 1 + RNG.nextInt(9);
            LRUCache actual = new LRUCache(capacity);
            Oracle oracle = new Oracle(capacity);
            for (int step = 0; step < 500; step++) {
                int key = RNG.nextInt(23);
                if (RNG.nextInt(100) < 56) {
                    int value = RNG.nextInt();
                    actual.put(key, value);
                    oracle.put(key, value);
                } else {
                    eq(oracle.get(key), actual.get(key), "random-get-" + scenario + '-' + step);
                }
                if (actual.size() != oracle.size()) throw new AssertionError("size drift scenario=" + scenario + " step=" + step);
                operations++;
            }
            for (int key = 0; key < 23; key++) {
                eq(oracle.get(key), actual.get(key), "final-key-" + scenario + '-' + key);
            }
        }
        if (operations != 45000) throw new AssertionError("unexpected operation count " + operations);
        System.out.println("PASS reviewer random_ops=45000 oracle=list-map-model capacity1=pass read_refresh=pass update_refresh=pass miss=null");
    }
}
