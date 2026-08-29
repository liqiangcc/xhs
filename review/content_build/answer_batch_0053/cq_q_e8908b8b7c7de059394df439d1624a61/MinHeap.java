import java.util.Arrays;
import java.util.NoSuchElementException;

public final class MinHeap {
    private int[] data = new int[8];
    private int size;

    public void add(int value) {
        ensureCapacity();
        int i = size++;
        data[i] = value;

        while (i > 0) {
            int parent = (i - 1) / 2;
            if (data[parent] <= data[i]) {
                break;
            }
            swap(parent, i);
            i = parent;
        }
    }

    public int peek() {
        if (size == 0) {
            throw new NoSuchElementException("heap is empty");
        }
        return data[0];
    }

    public int poll() {
        int result = peek();
        int last = data[--size];

        if (size > 0) {
            data[0] = last;
            int i = 0;

            while (true) {
                int left = i * 2 + 1;
                if (left >= size) {
                    break;
                }
                int right = left + 1;
                int smaller = right < size && data[right] < data[left]
                        ? right
                        : left;

                if (data[i] <= data[smaller]) {
                    break;
                }
                swap(i, smaller);
                i = smaller;
            }
        }
        return result;
    }

    public int size() {
        return size;
    }

    public boolean isEmpty() {
        return size == 0;
    }

    private void ensureCapacity() {
        if (size == data.length) {
            data = Arrays.copyOf(data, data.length * 2);
        }
    }

    private void swap(int a, int b) {
        int tmp = data[a];
        data[a] = data[b];
        data[b] = tmp;
    }
}
