import java.util.ArrayList;
import java.util.List;

public final class SinglyLinkedList<T> {
    private static final class Node<T> {
        private T value;
        private Node<T> next;

        private Node(T value) {
            this.value = value;
        }
    }

    private Node<T> head;
    private Node<T> tail;
    private int size;

    public int size() {
        return size;
    }

    public boolean isEmpty() {
        return size == 0;
    }

    public void add(T value) {
        Node<T> node = new Node<>(value);
        if (tail == null) {
            head = tail = node;
        } else {
            tail.next = node;
            tail = node;
        }
        size++;
    }

    public void insert(int index, T value) {
        checkPositionIndex(index);
        if (index == size) {
            add(value);
            return;
        }

        Node<T> node = new Node<>(value);
        if (index == 0) {
            node.next = head;
            head = node;
            if (tail == null) {
                tail = node;
            }
        } else {
            Node<T> prev = nodeAt(index - 1);
            node.next = prev.next;
            prev.next = node;
        }
        size++;
    }

    public T get(int index) {
        checkElementIndex(index);
        return nodeAt(index).value;
    }

    public T set(int index, T value) {
        checkElementIndex(index);
        Node<T> node = nodeAt(index);
        T old = node.value;
        node.value = value;
        return old;
    }

    public T remove(int index) {
        checkElementIndex(index);
        Node<T> removed;
        if (index == 0) {
            removed = head;
            head = head.next;
            size--;
            if (size == 0) {
                tail = null;
            }
            return removed.value;
        }

        Node<T> prev = nodeAt(index - 1);
        removed = prev.next;
        prev.next = removed.next;
        size--;
        if (removed == tail) {
            tail = prev;
        }
        return removed.value;
    }

    public List<T> toList() {
        List<T> result = new ArrayList<>(size);
        Node<T> current = head;
        while (current != null) {
            result.add(current.value);
            current = current.next;
        }
        return result;
    }

    void assertInvariants() {
        if (size == 0) {
            if (head != null || tail != null) {
                throw new AssertionError("empty list must have null head/tail");
            }
            return;
        }
        if (head == null || tail == null) {
            throw new AssertionError("non-empty list must have head/tail");
        }
        if (tail.next != null) {
            throw new AssertionError("tail.next must be null");
        }

        int count = 0;
        Node<T> current = head;
        Node<T> last = null;
        while (current != null) {
            count++;
            if (count > size) {
                throw new AssertionError("cycle or size undercount detected");
            }
            last = current;
            current = current.next;
        }
        if (count != size) {
            throw new AssertionError("reachable node count does not match size");
        }
        if (last != tail) {
            throw new AssertionError("tail must be the final reachable node");
        }
    }

    private Node<T> nodeAt(int index) {
        Node<T> current = head;
        for (int i = 0; i < index; i++) {
            current = current.next;
        }
        return current;
    }

    private void checkElementIndex(int index) {
        if (index < 0 || index >= size) {
            throw new IndexOutOfBoundsException("index=" + index + ", size=" + size);
        }
    }

    private void checkPositionIndex(int index) {
        if (index < 0 || index > size) {
            throw new IndexOutOfBoundsException("index=" + index + ", size=" + size);
        }
    }
}
