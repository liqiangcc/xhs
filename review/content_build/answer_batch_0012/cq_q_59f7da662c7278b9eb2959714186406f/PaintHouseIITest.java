import java.util.Arrays;
import java.util.Random;

public final class PaintHouseIITest {
    private PaintHouseIITest() {}

    public static void main(String[] args) {
        assertEquals(5, PaintHouseII.minCostII(new int[][]{{1,5,3},{2,9,4}}), "official example 1");
        assertEquals(5, PaintHouseII.minCostII(new int[][]{{1,3},{2,4}}), "official example 2");
        assertEquals(2, PaintHouseII.minCostII(new int[][]{{7,6,2}}), "single house");
        assertEquals(10, PaintHouseII.minCostII(new int[][]{{5,5,5},{5,5,5}}), "equal minima");
        assertEquals(8, PaintHouseII.minCostII(new int[][]{{1,5},{2,3},{4,1}}), "two-color alternating");

        boolean impossibleRejected = false;
        try {
            PaintHouseII.minCostII(new int[][]{{1},{2}});
        } catch (IllegalArgumentException expected) {
            impossibleRejected = true;
        }
        if (!impossibleRejected) {
            throw new AssertionError("single-color multi-house input must be rejected");
        }

        Random random = new Random(265L);
        int randomCases = 5000;
        for (int caseIndex = 0; caseIndex < randomCases; caseIndex++) {
            int houses = 1 + random.nextInt(6);
            int colors = 2 + random.nextInt(5);
            int[][] costs = new int[houses][colors];
            for (int i = 0; i < houses; i++) {
                for (int j = 0; j < colors; j++) {
                    costs[i][j] = 1 + random.nextInt(20);
                }
            }
            int expected = oracle(costs);
            int actual = PaintHouseII.minCostII(copy(costs));
            if (expected != actual) {
                throw new AssertionError(
                    "differential mismatch expected=" + expected
                        + " actual=" + actual
                        + " costs=" + Arrays.deepToString(costs)
                );
            }
        }

        System.out.println("PASS random_cases=5000 seed=265 official_examples=2 boundary_cases=4");
    }

    private static int oracle(int[][] costs) {
        int houses = costs.length;
        int colors = costs[0].length;
        long[] previous = new long[colors];
        for (int color = 0; color < colors; color++) {
            previous[color] = costs[0][color];
        }

        for (int house = 1; house < houses; house++) {
            long[] current = new long[colors];
            Arrays.fill(current, Long.MAX_VALUE);
            for (int color = 0; color < colors; color++) {
                for (int previousColor = 0; previousColor < colors; previousColor++) {
                    if (previousColor == color) {
                        continue;
                    }
                    current[color] = Math.min(
                        current[color],
                        previous[previousColor] + costs[house][color]
                    );
                }
            }
            previous = current;
        }

        long answer = Long.MAX_VALUE;
        for (long value : previous) {
            answer = Math.min(answer, value);
        }
        return Math.toIntExact(answer);
    }

    private static int[][] copy(int[][] source) {
        int[][] result = new int[source.length][];
        for (int i = 0; i < source.length; i++) {
            result[i] = source[i].clone();
        }
        return result;
    }

    private static void assertEquals(int expected, int actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
        }
    }
}
