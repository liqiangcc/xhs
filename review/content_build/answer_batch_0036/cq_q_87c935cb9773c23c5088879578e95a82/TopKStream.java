import java.util.Arrays;
import java.util.PrimitiveIterator;

public final class TopKStream {
    private TopKStream() {}

    public static long[] largestK(PrimitiveIterator.OfLong input, int k) {
        if (input == null) throw new IllegalArgumentException("input must not be null");
        if (k < 0) throw new IllegalArgumentException("k must be nonnegative");
        if (k == 0) return new long[0];

        long[] heap = new long[k];
        int size = 0;
        while (input.hasNext()) {
            long x = input.nextLong();
            if (size < k) {
                heap[size] = x;
                siftUp(heap, size);
                size++;
            } else if (x > heap[0]) {
                heap[0] = x;
                siftDown(heap, size, 0);
            }
        }

        long[] result = Arrays.copyOf(heap, size);
        Arrays.sort(result);
        reverse(result);
        return result;
    }

    private static void siftUp(long[] heap, int i) {
        while (i > 0) {
            int p = (i - 1) >>> 1;
            if (heap[p] <= heap[i]) return;
            long t = heap[p]; heap[p] = heap[i]; heap[i] = t;
            i = p;
        }
    }

    private static void siftDown(long[] heap, int size, int i) {
        while (true) {
            int left = i * 2 + 1;
            if (left >= size) return;
            int right = left + 1;
            int child = right < size && heap[right] < heap[left] ? right : left;
            if (heap[i] <= heap[child]) return;
            long t = heap[i]; heap[i] = heap[child]; heap[child] = t;
            i = child;
        }
    }

    private static void reverse(long[] a) {
        for (int l = 0, r = a.length - 1; l < r; l++, r--) {
            long t = a[l]; a[l] = a[r]; a[r] = t;
        }
    }
}
