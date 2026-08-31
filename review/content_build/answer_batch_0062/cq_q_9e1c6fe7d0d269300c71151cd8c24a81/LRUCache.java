import java.util.HashMap;
import java.util.Map;

public final class LRUCache {
    private static final class Node {
        final int key;
        int value;
        Node prev;
        Node next;
        Node(int key, int value) { this.key = key; this.value = value; }
    }

    private final int capacity;
    private final Map<Integer, Node> index = new HashMap<>();
    private final Node head = new Node(0, 0);
    private final Node tail = new Node(0, 0);

    public LRUCache(int capacity) {
        if (capacity <= 0) throw new IllegalArgumentException("capacity must be positive");
        this.capacity = capacity;
        head.next = tail;
        tail.prev = head;
    }

    public Integer get(int key) {
        Node node = index.get(key);
        if (node == null) return null;
        moveToFront(node);
        return node.value;
    }

    public void put(int key, int value) {
        Node node = index.get(key);
        if (node != null) {
            node.value = value;
            moveToFront(node);
            return;
        }
        Node created = new Node(key, value);
        index.put(key, created);
        addAfterHead(created);
        if (index.size() > capacity) {
            Node victim = tail.prev;
            remove(victim);
            index.remove(victim.key);
        }
    }

    public int size() { return index.size(); }

    private void moveToFront(Node node) {
        remove(node);
        addAfterHead(node);
    }

    private void addAfterHead(Node node) {
        node.prev = head;
        node.next = head.next;
        head.next.prev = node;
        head.next = node;
    }

    private static void remove(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }
}
