import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Random;

public final class SinglyLinkedListTest {
    private static int fixedChecks;
    private static int randomizedOperations;

    public static void main(String[] args) {
        fixedCases();
        randomizedDifferentialTest();
        System.out.println("PASS fixed=" + fixedChecks
                + " randomized_ops=" + randomizedOperations
                + " oracle=ArrayList"
                + " invariants=head-tail-size-acyclic");
    }

    private static void fixedCases() {
        SinglyLinkedList<Integer> list = new SinglyLinkedList<>();
        expectList(list, List.of());
        expectThrows(() -> list.get(0));
        fixedChecks++;

        list.add(10);
        list.assertInvariants();
        expectList(list, List.of(10));
        fixedChecks++;

        list.insert(0, 5);
        list.insert(2, 20);
        list.insert(2, 15);
        list.assertInvariants();
        expectList(list, List.of(5, 10, 15, 20));
        fixedChecks++;

        expectEquals(15, list.get(2), "get middle");
        expectEquals(15, list.set(2, 16), "set returns old value");
        expectList(list, List.of(5, 10, 16, 20));
        fixedChecks++;

        expectEquals(5, list.remove(0), "remove head");
        expectEquals(16, list.remove(1), "remove middle");
        expectEquals(20, list.remove(1), "remove tail");
        list.assertInvariants();
        expectList(list, List.of(10));
        fixedChecks++;

        expectEquals(10, list.remove(0), "remove only element");
        list.assertInvariants();
        expectList(list, List.of());
        fixedChecks++;

        SinglyLinkedList<Integer> nullable = new SinglyLinkedList<>();
        nullable.add(null);
        nullable.insert(0, 1);
        nullable.set(1, null);
        nullable.assertInvariants();
        if (nullable.size() != 2 || nullable.get(1) != null) {
            throw new AssertionError("null payload handling failed");
        }
        fixedChecks++;

        SinglyLinkedList<Integer> bounds = new SinglyLinkedList<>();
        expectThrows(() -> bounds.insert(-1, 1));
        expectThrows(() -> bounds.insert(1, 1));
        bounds.add(1);
        expectThrows(() -> bounds.get(-1));
        expectThrows(() -> bounds.get(1));
        expectThrows(() -> bounds.set(1, 2));
        expectThrows(() -> bounds.remove(1));
        bounds.assertInvariants();
        fixedChecks++;
    }

    private static void randomizedDifferentialTest() {
        Random random = new Random(20260824L);
        SinglyLinkedList<Integer> actual = new SinglyLinkedList<>();
        ArrayList<Integer> oracle = new ArrayList<>();

        for (int step = 0; step < 5000; step++) {
            int op = oracle.isEmpty() ? random.nextInt(2) : random.nextInt(5);
            switch (op) {
                case 0 -> {
                    Integer value = randomValue(random);
                    actual.add(value);
                    oracle.add(value);
                }
                case 1 -> {
                    int index = random.nextInt(oracle.size() + 1);
                    Integer value = randomValue(random);
                    actual.insert(index, value);
                    oracle.add(index, value);
                }
                case 2 -> {
                    int index = random.nextInt(oracle.size());
                    Integer expected = oracle.remove(index);
                    Integer got = actual.remove(index);
                    expectEquals(expected, got, "random remove");
                }
                case 3 -> {
                    int index = random.nextInt(oracle.size());
                    Integer value = randomValue(random);
                    Integer expected = oracle.set(index, value);
                    Integer got = actual.set(index, value);
                    expectEquals(expected, got, "random set");
                }
                case 4 -> {
                    int index = random.nextInt(oracle.size());
                    expectEquals(oracle.get(index), actual.get(index), "random get");
                }
                default -> throw new AssertionError("unexpected op");
            }
            actual.assertInvariants();
            expectList(actual, oracle);
            randomizedOperations++;
        }
    }

    private static Integer randomValue(Random random) {
        if (random.nextInt(20) == 0) {
            return null;
        }
        return random.nextInt(2001) - 1000;
    }

    private static <T> void expectList(SinglyLinkedList<T> actual, List<T> expected) {
        if (actual.size() != expected.size()) {
            throw new AssertionError("size mismatch expected=" + expected.size() + " actual=" + actual.size());
        }
        List<T> values = actual.toList();
        if (!values.equals(expected)) {
            throw new AssertionError("content mismatch expected=" + expected + " actual=" + values);
        }
        actual.assertInvariants();
    }

    private static void expectEquals(Object expected, Object actual, String message) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(message + " expected=" + expected + " actual=" + actual);
        }
    }

    private static void expectThrows(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected IndexOutOfBoundsException");
        } catch (IndexOutOfBoundsException expected) {
            // expected
        }
    }
}
