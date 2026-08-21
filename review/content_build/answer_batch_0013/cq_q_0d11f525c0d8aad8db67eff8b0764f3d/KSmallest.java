import java.util.Arrays;
import java.util.Comparator;
import java.util.Objects;
import java.util.PriorityQueue;

public final class KSmallest {
    private KSmallest() {}

    public static int[] kSmallest(int[] values, int k) {
        Objects.requireNonNull(values, "values");
        if (k < 0 || k > values.length) {
            throw new IllegalArgumentException("k must be between 0 and values.length");
        }
        if (k == 0) {
            return new int[0];
        }

        PriorityQueue<Integer> maxHeap =
                new PriorityQueue<>(k, Comparator.reverseOrder());

        for (int value : values) {
            if (maxHeap.size() < k) {
                maxHeap.add(value);
            } else if (value < maxHeap.peek()) {
                maxHeap.poll();
                maxHeap.add(value);
            }
        }

        int[] result = new int[k];
        int index = 0;
        while (!maxHeap.isEmpty()) {
            result[index++] = maxHeap.poll();
        }
        Arrays.sort(result);
        return result;
    }
}
