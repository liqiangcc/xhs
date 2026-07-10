public final class LRUCacheTest {
    private static void equalsInt(int expected, int actual, String name) {
        if (expected != actual) {
            throw new AssertionError(name + ": expected=" + expected + ", actual=" + actual);
        }
    }

    private static void expectsIllegalCapacity() {
        try {
            new LRUCache(-1);
            throw new AssertionError("negative capacity must fail");
        } catch (IllegalArgumentException expected) {
            // Expected contract.
        }
    }

    public static void main(String[] args) {
        LRUCache capacityOne = new LRUCache(1);
        capacityOne.put(1, 1);
        capacityOne.put(2, 2);
        equalsInt(-1, capacityOne.get(1), "capacity-one evicts previous key");
        equalsInt(2, capacityOne.get(2), "capacity-one retains newest key");

        LRUCache refreshOrder = new LRUCache(2);
        refreshOrder.put(1, 1);
        refreshOrder.put(2, 2);
        equalsInt(1, refreshOrder.get(1), "get returns stored value");
        refreshOrder.put(3, 3);
        equalsInt(-1, refreshOrder.get(2), "get refreshes recency");
        equalsInt(1, refreshOrder.get(1), "refreshed entry remains");

        refreshOrder.put(1, 10);
        equalsInt(10, refreshOrder.get(1), "update changes value and keeps key");

        LRUCache zero = new LRUCache(0);
        zero.put(1, 1);
        equalsInt(-1, zero.get(1), "zero capacity stores nothing");

        expectsIllegalCapacity();
    }
}
