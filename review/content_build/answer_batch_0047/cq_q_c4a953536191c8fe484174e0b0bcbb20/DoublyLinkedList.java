public final class DoublyLinkedList {
    private static final class Node {
        final int value;
        Node prev;
        Node next;

        Node(int value) {
            this.value = value;
        }
    }

    private Node head;
    private Node tail;
    private int size;

    public void insert(int index, int value) {
        if (index < 0 || index > size) {
            throw new IndexOutOfBoundsException("index=" + index + ", size=" + size);
        }

        if (index == size) {
            linkLast(value);
            return;
        }

        Node next = nodeAt(index);
        Node prev = next.prev;
        Node node = new Node(value);

        node.prev = prev;
        node.next = next;
        next.prev = node;

        if (prev == null) {
            head = node;
        } else {
            prev.next = node;
        }
        size++;
    }

    private void linkLast(int value) {
        Node node = new Node(value);
        Node prev = tail;
        node.prev = prev;
        tail = node;

        if (prev == null) {
            head = node;
        } else {
            prev.next = node;
        }
        size++;
    }

    private Node nodeAt(int index) {
        if (index < (size >>> 1)) {
            Node p = head;
            for (int i = 0; i < index; i++) {
                p = p.next;
            }
            return p;
        }

        Node p = tail;
        for (int i = size - 1; i > index; i--) {
            p = p.prev;
        }
        return p;
    }
}
