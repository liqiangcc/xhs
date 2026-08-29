import java.util.Arrays;
import java.util.NoSuchElementException;
import java.util.Random;
import java.util.TreeMap;

public final class MinHeapTest {
    public static void main(String[] args) {
        emptyContract();
        deterministicCases();
        randomizedAgainstIndependentMultiset();
        largeDrainAgainstSortedOracle();
        System.out.println(
                "PASS empty=throws duplicates-extremes=preserved random-ops=50000 large-drain=200000");
    }

    private static void emptyContract() {
        MinHeap heap = new MinHeap();
        assertTrue(heap.isEmpty(), "new heap must be empty");
        assertEquals(0, heap.size(), "new heap size");
        expectNoSuchElement(heap::peek);
        expectNoSuchElement(heap::poll);
    }

    private static void deterministicCases() {
        MinHeap heap = new MinHeap();
        int[] values = {
                5, 1, 3, 1, -7, 0, Integer.MAX_VALUE, Integer.MIN_VALUE, 9, 9
        };
        for (int value : values) {
            heap.add(value);
        }

        int[] expected = values.clone();
        Arrays.sort(expected);
        for (int value : expected) {
            assertEquals(value, heap.peek(), "peek before deterministic poll");
            assertEquals(value, heap.poll(), "deterministic poll");
        }
        assertTrue(heap.isEmpty(), "deterministic heap must drain");
    }

    private static void randomizedAgainstIndependentMultiset() {
        MinHeap heap = new MinHeap();
        TreeMap<Integer, Integer> oracle = new TreeMap<>();
        Random random = new Random(0x5eed53L);

        for (int step = 0; step < 50_000; step++) {
            int op = random.nextInt(100);
            if (oracle.isEmpty() || op < 58) {
                int value;
                if (step % 997 == 0) {
                    value = Integer.MIN_VALUE;
                } else if (step % 991 == 0) {
                    value = Integer.MAX_VALUE;
                } else {
                    value = random.nextInt(401) - 200;
                }
                heap.add(value);
                oracle.merge(value, 1, Integer::sum);
            } else if (op < 78) {
                assertEquals(oracle.firstKey(), heap.peek(), "random peek");
            } else {
                int expected = removeFirst(oracle);
                assertEquals(expected, heap.poll(), "random poll");
            }

            assertEquals(totalCount(oracle), heap.size(), "random size");
            assertEquals(oracle.isEmpty(), heap.isEmpty(), "random empty state");
            if (!oracle.isEmpty()) {
                assertEquals(oracle.firstKey(), heap.peek(), "random minimum");
            }
        }

        while (!oracle.isEmpty()) {
            assertEquals(removeFirst(oracle), heap.poll(), "random drain");
        }
        assertTrue(heap.isEmpty(), "random heap must drain");
    }

    private static void largeDrainAgainstSortedOracle() {
        final int n = 200_000;
        Random random = new Random(0x53b00bL);
        MinHeap heap = new MinHeap();
        int[] oracle = new int[n];

        for (int i = 0; i < n; i++) {
            int value = random.nextInt();
            oracle[i] = value;
            heap.add(value);
        }

        Arrays.sort(oracle);
        for (int value : oracle) {
            assertEquals(value, heap.poll(), "large sorted drain");
        }
        assertTrue(heap.isEmpty(), "large heap must drain");
    }

    private static int removeFirst(TreeMap<Integer, Integer> oracle) {
        int first = oracle.firstKey();
        int count = oracle.get(first);
        if (count == 1) {
            oracle.remove(first);
        } else {
            oracle.put(first, count - 1);
        }
        return first;
    }

    private static int totalCount(TreeMap<Integer, Integer> oracle) {
        int total = 0;
        for (int count : oracle.values()) {
            total += count;
        }
        return total;
    }

    private static void expectNoSuchElement(IntSupplier action) {
        try {
            action.getAsInt();
            throw new AssertionError("expected NoSuchElementException");
        } catch (NoSuchElementException expected) {
            // expected
        }
    }

    private static void assertTrue(boolean actual, String message) {
        if (!actual) {
            throw new AssertionError(message);
        }
    }

    private static void assertEquals(boolean expected, boolean actual, String message) {
        if (expected != actual) {
            throw new AssertionError(message + ": expected=" + expected + " actual=" + actual);
        }
    }

    private static void assertEquals(int expected, int actual, String message) {
        if (expected != actual) {
            throw new AssertionError(message + ": expected=" + expected + " actual=" + actual);
        }
    }

    @FunctionalInterface
    private interface IntSupplier {
        int getAsInt();
    }
}
