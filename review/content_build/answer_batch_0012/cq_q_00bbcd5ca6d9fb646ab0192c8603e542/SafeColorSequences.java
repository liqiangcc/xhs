import java.math.BigInteger;

public final class SafeColorSequences {
    private static final int COLORS = 3;

    private SafeColorSequences() {}

    /**
     * Exact number of length-n sequences over three colors such that no
     * consecutive triple contains all three colors.
     *
     * The source note does not state a modulus, so this practice implementation
     * returns an exact BigInteger. n == 0 is defined as the empty sequence.
     */
    public static BigInteger countWays(int n) {
        if (n < 0) {
            throw new IllegalArgumentException("n must be non-negative");
        }
        if (n == 0) {
            return BigInteger.ONE;
        }
        if (n == 1) {
            return BigInteger.valueOf(COLORS);
        }

        BigInteger[][] dp = new BigInteger[COLORS][COLORS];
        for (int first = 0; first < COLORS; first++) {
            for (int second = 0; second < COLORS; second++) {
                dp[first][second] = BigInteger.ONE;
            }
        }

        for (int length = 3; length <= n; length++) {
            BigInteger[][] next = zeroMatrix();
            for (int previous = 0; previous < COLORS; previous++) {
                for (int last = 0; last < COLORS; last++) {
                    for (int current = 0; current < COLORS; current++) {
                        if (allDistinct(previous, last, current)) {
                            continue;
                        }
                        next[last][current] =
                                next[last][current].add(dp[previous][last]);
                    }
                }
            }
            dp = next;
        }

        BigInteger total = BigInteger.ZERO;
        for (int previous = 0; previous < COLORS; previous++) {
            for (int last = 0; last < COLORS; last++) {
                total = total.add(dp[previous][last]);
            }
        }
        return total;
    }

    private static boolean allDistinct(int a, int b, int c) {
        return a != b && b != c && a != c;
    }

    private static BigInteger[][] zeroMatrix() {
        BigInteger[][] matrix = new BigInteger[COLORS][COLORS];
        for (int i = 0; i < COLORS; i++) {
            for (int j = 0; j < COLORS; j++) {
                matrix[i][j] = BigInteger.ZERO;
            }
        }
        return matrix;
    }
}
