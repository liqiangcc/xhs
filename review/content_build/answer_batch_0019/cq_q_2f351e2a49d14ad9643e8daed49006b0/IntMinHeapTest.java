import java.util.ArrayList;
import java.util.List;
import java.util.NoSuchElementException;
import java.util.PriorityQueue;
import java.util.Random;

public final class IntMinHeapTest {
    private static int fixed = 0;

    public static void main(String[] args) {
        fixedCases();
        randomizedCases();
        System.out.println("PASS fixed=" + fixed + " randomized=5000 oracle=java-priority-queue heap=min duplicates=supported empty=throws mutation=input-none");
    }

    private static void fixedCases() {
        IntMinHeap empty = new IntMinHeap();
        expectEmptyBehavior(empty);
        fixed++; // 1

        IntMinHeap emptyArray = new IntMinHeap(new int[0]);
        require(emptyArray.isEmpty() && emptyArray.size() == 0, "empty-array constructor");
        expectEmptyBehavior(emptyArray);
        fixed++; // 2

        IntMinHeap single = new IntMinHeap();
        single.add(7);
        require(single.size() == 1 && single.peek() == 7, "single peek");
        require(single.poll() == 7 && single.isEmpty(), "single poll");
        fixed++; // 3

        drainAndCheck(new IntMinHeap(new int[]{5, 1, 1, 3}), List.of(1, 1, 3, 5));
        fixed++; // 4

        int[] source = {9, -2, 4, 0, -2};
        int[] before = source.clone();
        drainAndCheck(new IntMinHeap(source), List.of(-2, -2, 0, 4, 9));
        require(java.util.Arrays.equals(source, before), "constructor mutated input");
        fixed++; // 5

        IntMinHeap ordering = new IntMinHeap();
        int[] values = {4, 2, 8, 1, 3, 7, 6, 5};
        for (int value : values) ordering.add(value);
        drainAndCheck(ordering, List.of(1, 2, 3, 4, 5, 6, 7, 8));
        fixed++; // 6

        drainAndCheck(new IntMinHeap(new int[]{-1, Integer.MIN_VALUE, 0, Integer.MAX_VALUE}),
                List.of(Integer.MIN_VALUE, -1, 0, Integer.MAX_VALUE));
        fixed++; // 7

        IntMinHeap repeated = new IntMinHeap();
        for (int i = 100; i >= -100; i--) repeated.add(i);
        List<Integer> expected = new ArrayList<>();
        for (int i = -100; i <= 100; i++) expected.add(i);
        drainAndCheck(repeated, expected);
        fixed++; // 8

        boolean npe = false;
        try {
            new IntMinHeap(null);
        } catch (NullPointerException expectedException) {
            npe = true;
        }
        require(npe, "null constructor must throw");
        fixed++; // 9

        IntMinHeap mix = new IntMinHeap(new int[]{3, 10, 5});
        require(mix.poll() == 3, "mix poll");
        mix.add(1);
        require(mix.peek() == 1, "mix peek after add");
        require(mix.poll() == 1, "mix poll after add");
        require(mix.poll() == 5, "mix third");
        require(mix.poll() == 10, "mix fourth");
        require(mix.isEmpty(), "mix empty");
        fixed++; // 10
    }

    private static void randomizedCases() {
        Random random = new Random(0x0019BEEFL);
        for (int i = 0; i < 5000; i++) {
            IntMinHeap actual = new IntMinHeap();
            PriorityQueue<Integer> oracle = new PriorityQueue<>();
            int operations = 1 + random.nextInt(200);
            for (int op = 0; op < operations; op++) {
                boolean add = oracle.isEmpty() || random.nextInt(100) < 63;
                if (add) {
                    int value = random.nextInt(2001) - 1000;
                    actual.add(value);
                    oracle.add(value);
                } else if (random.nextBoolean()) {
                    int a = actual.peek();
                    int b = oracle.peek();
                    require(a == b, "random peek mismatch case=" + i + " op=" + op);
                } else {
                    int a = actual.poll();
                    int b = oracle.remove();
                    require(a == b, "random poll mismatch case=" + i + " op=" + op);
                }
                require(actual.size() == oracle.size(), "random size mismatch case=" + i + " op=" + op);
                require(actual.isEmpty() == oracle.isEmpty(), "random empty mismatch case=" + i + " op=" + op);
                if (!oracle.isEmpty()) {
                    require(actual.peek() == oracle.peek(), "random root mismatch case=" + i + " op=" + op);
                }
                assertHeapInvariant(actual.snapshot(), i, op);
            }
            while (!oracle.isEmpty()) {
                require(actual.poll() == oracle.remove(), "random drain mismatch case=" + i);
            }
            require(actual.isEmpty(), "random drain not empty case=" + i);
            expectEmptyBehavior(actual);
        }
    }

    private static void drainAndCheck(IntMinHeap heap, List<Integer> expectedSorted) {
        assertHeapInvariant(heap.snapshot(), -1, fixed + 1);
        List<Integer> actual = new ArrayList<>();
        while (!heap.isEmpty()) {
            int before = heap.size();
            int peek = heap.peek();
            int poll = heap.poll();
            require(peek == poll, "peek/poll mismatch");
            require(heap.size() == before - 1, "size did not decrement");
            actual.add(poll);
            assertHeapInvariant(heap.snapshot(), -1, fixed + 1);
        }
        require(actual.equals(expectedSorted), "expected=" + expectedSorted + " actual=" + actual);
    }

    private static void expectEmptyBehavior(IntMinHeap heap) {
        boolean peekThrown = false;
        try {
            heap.peek();
        } catch (NoSuchElementException expected) {
            peekThrown = true;
        }
        boolean pollThrown = false;
        try {
            heap.poll();
        } catch (NoSuchElementException expected) {
            pollThrown = true;
        }
        require(peekThrown && pollThrown, "empty operations must throw");
    }

    private static void assertHeapInvariant(int[] values, int caseId, int opId) {
        for (int i = 1; i < values.length; i++) {
            int parent = (i - 1) >>> 1;
            if (values[parent] > values[i]) {
                throw new AssertionError("heap invariant violated case=" + caseId + " op=" + opId + " parent=" + parent + " child=" + i);
            }
        }
    }

    private static void require(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
}
