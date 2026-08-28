import java.util.ArrayList;
import java.util.List;

public final class DoublyLinkedList {
    public static final class Node {
        private final int value;
        private Node prev;
        private Node next;
        private DoublyLinkedList owner;

        private Node(int value, DoublyLinkedList owner) {
            this.value = value;
            this.owner = owner;
        }

        public int value() { return value; }
    }

    private final Node head = new Node(0, this);
    private final Node tail = new Node(0, this);
    private int size;

    public DoublyLinkedList() {
        head.next = tail;
        tail.prev = head;
    }

    public Node addFirst(int value) {
        return insertBetween(head, head.next, value);
    }

    public Node addLast(int value) {
        return insertBetween(tail.prev, tail, value);
    }

    public Node insertAfter(Node anchor, int value) {
        if (anchor == null || anchor.owner != this || anchor == tail) {
            throw new IllegalArgumentException("anchor must be a non-tail node of this list");
        }
        return insertBetween(anchor, anchor.next, value);
    }

    private Node insertBetween(Node left, Node right, int value) {
        if (left.next != right || right.prev != left) {
            throw new IllegalStateException("broken insertion boundary");
        }
        Node x = new Node(value, this);
        x.prev = left;
        x.next = right;
        left.next = x;
        right.prev = x;
        size++;
        return x;
    }

    public int size() { return size; }

    public List<Integer> valuesForward() {
        List<Integer> out = new ArrayList<>();
        for (Node p = head.next; p != tail; p = p.next) out.add(p.value);
        return out;
    }

    public List<Integer> valuesBackward() {
        List<Integer> out = new ArrayList<>();
        for (Node p = tail.prev; p != head; p = p.prev) out.add(p.value);
        return out;
    }
}
