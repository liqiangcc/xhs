import java.util.Arrays;
import java.util.NoSuchElementException;

public final class IntMinHeap {
    private int[] elements;
    private int size;

    public IntMinHeap() {
        this.elements = new int[8];
    }

    public IntMinHeap(int[] values) {
        if (values == null) {
            throw new NullPointerException("values");
        }
        this.elements = Arrays.copyOf(values, Math.max(8, values.length));
        this.size = values.length;
        for (int i = (size >>> 1) - 1; i >= 0; i--) {
            siftDown(i);
        }
    }

    public int size() {
        return size;
    }

    public boolean isEmpty() {
        return size == 0;
    }

    public void add(int value) {
        ensureCapacity(size + 1);
        elements[size] = value;
        siftUp(size);
        size++;
    }

    public int peek() {
        ensureNotEmpty();
        return elements[0];
    }

    public int poll() {
        ensureNotEmpty();
        int result = elements[0];
        int last = elements[--size];
        if (size > 0) {
            elements[0] = last;
            siftDown(0);
        }
        return result;
    }

    int[] snapshot() {
        return Arrays.copyOf(elements, size);
    }

    private void siftUp(int index) {
        int value = elements[index];
        while (index > 0) {
            int parent = parent(index);
            if (elements[parent] <= value) {
                break;
            }
            elements[index] = elements[parent];
            index = parent;
        }
        elements[index] = value;
    }

    private void siftDown(int index) {
        int value = elements[index];
        int half = size >>> 1;
        while (index < half) {
            int left = left(index);
            int right = left + 1;
            int smallest = left;
            if (right < size && elements[right] < elements[left]) {
                smallest = right;
            }
            if (elements[smallest] >= value) {
                break;
            }
            elements[index] = elements[smallest];
            index = smallest;
        }
        elements[index] = value;
    }

    private void ensureCapacity(int target) {
        if (target <= elements.length) {
            return;
        }
        int next = elements.length + (elements.length >>> 1);
        if (next < target) {
            next = target;
        }
        elements = Arrays.copyOf(elements, next);
    }

    private void ensureNotEmpty() {
        if (size == 0) {
            throw new NoSuchElementException("heap is empty");
        }
    }

    private static int parent(int index) {
        return (index - 1) >>> 1;
    }

    private static int left(int index) {
        return (index << 1) + 1;
    }
}
