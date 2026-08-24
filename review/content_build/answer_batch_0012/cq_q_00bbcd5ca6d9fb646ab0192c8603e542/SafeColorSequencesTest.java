import java.math.BigInteger;

public final class SafeColorSequencesTest {
    public static void main(String[] args) {
        expect(0, "1");
        expect(1, "3");
        expect(2, "9");
        expect(3, "21");
        expect(4, "51");
        expect(5, "123");
        expect(6, "297");

        for (int n = 0; n <= 10; n++) {
            BigInteger expected = BigInteger.valueOf(bruteForce(n));
            BigInteger actual = SafeColorSequences.countWays(n);
            if (!expected.equals(actual)) {
                throw new AssertionError("brute-force mismatch n=" + n
                        + " expected=" + expected + " actual=" + actual);
            }
        }

        BigInteger previousTwo = SafeColorSequences.countWays(1);
        BigInteger previousOne = SafeColorSequences.countWays(2);
        for (int n = 3; n <= 200; n++) {
            BigInteger actual = SafeColorSequences.countWays(n);
            BigInteger recurrence = previousOne.multiply(BigInteger.TWO).add(previousTwo);
            if (!actual.equals(recurrence)) {
                throw new AssertionError("recurrence mismatch n=" + n
                        + " expected=" + recurrence + " actual=" + actual);
            }
            previousTwo = previousOne;
            previousOne = actual;
        }

        try {
            SafeColorSequences.countWays(-1);
            throw new AssertionError("negative n must fail");
        } catch (IllegalArgumentException expected) {
            // expected
        }

        System.out.println("PASS exact_cases=7 brute_force_n=0..10 recurrence_n=3..200 negative_input=verified");
    }

    private static void expect(int n, String expected) {
        BigInteger actual = SafeColorSequences.countWays(n);
        if (!actual.equals(new BigInteger(expected))) {
            throw new AssertionError("n=" + n + " expected=" + expected + " actual=" + actual);
        }
    }

    private static long bruteForce(int n) {
        if (n == 0) {
            return 1;
        }
        int[] sequence = new int[n];
        return enumerate(sequence, 0);
    }

    private static long enumerate(int[] sequence, int index) {
        if (index == sequence.length) {
            return 1;
        }
        long count = 0;
        for (int color = 0; color < 3; color++) {
            sequence[index] = color;
            if (index >= 2
                    && sequence[index - 2] != sequence[index - 1]
                    && sequence[index - 1] != sequence[index]
                    && sequence[index - 2] != sequence[index]) {
                continue;
            }
            count += enumerate(sequence, index + 1);
        }
        return count;
    }
}
