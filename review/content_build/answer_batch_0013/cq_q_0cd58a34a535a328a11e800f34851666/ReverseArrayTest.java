import java.util.Arrays;
import java.util.Random;

public final class ReverseArrayTest {
    private static int fixed = 0;
    private static int randomized = 0;

    public static void main(String[] args) {
        check(new int[] {});
        check(new int[] {7});
        check(new int[] {1, 2});
        check(new int[] {1, 2, 3});
        check(new int[] {1, 2, 3, 4});
        check(new int[] {2, 2, 1, 2});
        check(new int[] {Integer.MIN_VALUE, 0, Integer.MAX_VALUE});
        fixed = 7;

        requireThrowsNull(() -> ReverseArray.reverseInPlace(null));
        requireThrowsNull(() -> ReverseArray.reversedCopy(null));

        Random random = new Random(0x5EEDC0DEL);
        for (int round = 0; round < 5000; round++) {
            int len = random.nextInt(101);
            int[] input = new int[len];
            for (int i = 0; i < len; i++) {
                input[i] = random.nextInt();
            }
            check(input);
            randomized++;
        }

        System.out.println("PASS fixed=" + fixed
                + " randomized=" + randomized
                + " oracle=index-mapping involution=true null=fail-fast");
    }

    private static void check(int[] input) {
        int[] original = input.clone();
        int[] expected = oracle(original);

        int[] inPlace = input.clone();
        ReverseArray.reverseInPlace(inPlace);
        require(Arrays.equals(inPlace, expected), "in-place mismatch");
        ReverseArray.reverseInPlace(inPlace);
        require(Arrays.equals(inPlace, original), "reverse-twice must restore original");

        int[] copyInput = input.clone();
        int[] copied = ReverseArray.reversedCopy(copyInput);
        require(Arrays.equals(copied, expected), "copy mismatch");
        require(Arrays.equals(copyInput, original), "copy variant must not mutate input");
    }

    private static int[] oracle(int[] input) {
        int[] expected = new int[input.length];
        for (int destination = 0; destination < input.length; destination++) {
            int source = input.length - 1 - destination;
            expected[destination] = input[source];
        }
        return expected;
    }

    private static void requireThrowsNull(Runnable action) {
        try {
            action.run();
            throw new AssertionError("expected NullPointerException");
        } catch (NullPointerException expected) {
            // expected
        }
    }

    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
