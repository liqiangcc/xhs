import java.util.Arrays;
import java.util.Random;

public final class KSmallestTest {
    private static int fixed = 0;
    private static int randomized = 0;

    public static void main(String[] args) {
        check(new int[] {}, 0);
        check(new int[] {7}, 0);
        check(new int[] {7}, 1);
        check(new int[] {4, 1, 3, 2}, 2);
        check(new int[] {1, 1, 2}, 2);
        check(new int[] {-5, 7, -1, 0, -5}, 3);
        check(new int[] {Integer.MAX_VALUE, 0, Integer.MIN_VALUE, 1}, 2);
        check(new int[] {3, 2, 1}, 3);
        fixed = 8;

        requireThrowsNull(() -> KSmallest.kSmallest(null, 0));
        requireThrowsIllegal(() -> KSmallest.kSmallest(new int[] {1}, -1));
        requireThrowsIllegal(() -> KSmallest.kSmallest(new int[] {1}, 2));

        Random random = new Random(0x5EED70AFL);
        for (int round = 0; round < 5000; round++) {
            int len = random.nextInt(101);
            int[] input = new int[len];
            for (int i = 0; i < len; i++) {
                input[i] = random.nextInt();
            }
            int k = random.nextInt(len + 1);
            check(input, k);
            randomized++;
        }

        System.out.println("PASS fixed=" + fixed
                + " randomized=" + randomized
                + " oracle=full-sort-prefix input_immutable=true invalid_k=fail-fast");
    }

    private static void check(int[] input, int k) {
        int[] original = input.clone();
        int[] expected = oracle(input, k);
        int[] actual = KSmallest.kSmallest(input, k);
        require(Arrays.equals(actual, expected),
                "mismatch k=" + k + " input=" + Arrays.toString(input));
        require(Arrays.equals(input, original), "input must remain unchanged");
    }

    private static int[] oracle(int[] input, int k) {
        int[] sorted = input.clone();
        Arrays.sort(sorted);
        return Arrays.copyOf(sorted, k);
    }

    private static void requireThrowsNull(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected NullPointerException");
        } catch (NullPointerException expected) {
            // expected
        }
    }

    private static void requireThrowsIllegal(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
