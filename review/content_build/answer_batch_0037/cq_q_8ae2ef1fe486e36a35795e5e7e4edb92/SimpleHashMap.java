import java.util.Objects;

public final class SimpleHashMap<K, V> {
    private final Node<K, V>[] buckets;

    @SuppressWarnings("unchecked")
    public SimpleHashMap(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        this.buckets = (Node<K, V>[]) new Node<?, ?>[capacity];
    }

    public void put(K key, V value) {
        Objects.requireNonNull(key, "key");
        Objects.requireNonNull(value, "value");
        int index = index(key);
        for (Node<K, V> node = buckets[index]; node != null; node = node.next) {
            if (node.key.equals(key)) {
                node.value = value;
                return;
            }
        }
        buckets[index] = new Node<>(key, value, buckets[index]);
    }

    public V get(K key) {
        Objects.requireNonNull(key, "key");
        int index = index(key);
        for (Node<K, V> node = buckets[index]; node != null; node = node.next) {
            if (node.key.equals(key)) return node.value;
        }
        return null;
    }

    private int index(K key) {
        int h = key.hashCode();
        h ^= h >>> 16;
        return Math.floorMod(h, buckets.length);
    }

    private static final class Node<K, V> {
        private final K key;
        private V value;
        private final Node<K, V> next;

        private Node(K key, V value, Node<K, V> next) {
            this.key = key;
            this.value = value;
            this.next = next;
        }
    }
}
