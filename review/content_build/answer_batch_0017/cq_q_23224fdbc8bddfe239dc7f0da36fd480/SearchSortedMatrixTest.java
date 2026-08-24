import java.util.Arrays;
import java.util.Random;

public final class SearchSortedMatrixTest {
    private static int fixedChecks;
    private static int randomizedChecks;

    public static void main(String[] args) {
        fixedCases();
        randomizedDifferentialCases();
        System.out.printf("PASS fixed=%d randomized=%d oracle=full-scan input=unmodified%n",
                fixedChecks, randomizedChecks);
    }

    private static void fixedCases() {
        check(false, SearchSortedMatrix.contains(null, 1), "null");
        check(false, SearchSortedMatrix.contains(new int[0][], 1), "zero rows");
        check(false, SearchSortedMatrix.contains(new int[][] {{}}, 1), "zero columns");
        check(true, SearchSortedMatrix.contains(new int[][] {{7}}, 7), "single hit");
        check(false, SearchSortedMatrix.contains(new int[][] {{7}}, 8), "single miss");
        check(true, SearchSortedMatrix.contains(new int[][] {{1, 2, 4, 9}}, 4), "one row");
        check(true, SearchSortedMatrix.contains(new int[][] {{1}, {3}, {3}, {8}}, 3), "one column duplicates");

        int[][] typical = {
                {1, 4, 7, 11, 15},
                {2, 5, 8, 12, 19},
                {3, 6, 9, 16, 22},
                {10, 13, 14, 17, 24},
                {18, 21, 23, 26, 30}
        };
        int[][] snapshot = deepCopy(typical);
        check(true, SearchSortedMatrix.contains(typical, 5), "typical hit");
        check(false, SearchSortedMatrix.contains(typical, 20), "typical miss");
        check(true, Arrays.deepEquals(snapshot, typical), "typical unmodified");

        int[][] duplicates = {
                {-5, -2, 0, 0},
                {-5, 0, 0, 3},
                {-1, 0, 4, 4}
        };
        check(true, SearchSortedMatrix.contains(duplicates, 0), "duplicates");
        check(false, SearchSortedMatrix.contains(duplicates, 2), "duplicate matrix miss");

        int[][] extremes = {
                {Integer.MIN_VALUE, -1},
                {0, Integer.MAX_VALUE}
        };
        check(true, SearchSortedMatrix.contains(extremes, Integer.MIN_VALUE), "min value");
        check(true, SearchSortedMatrix.contains(extremes, Integer.MAX_VALUE), "max value");

        expectIllegalArgument(new int[][] {{1, 2}, {3}}, "ragged");
        expectIllegalArgument(new int[][] {{1}, null}, "null row");
    }

    private static void randomizedDifferentialCases() {
        Random random = new Random(0x23224fdbL);
        for (int iteration = 0; iteration < 5000; iteration++) {
            int rows = 1 + random.nextInt(20);
            int columns = 1 + random.nextInt(20);
            int[][] matrix = buildMonotoneMatrix(rows, columns, random);
            int[][] snapshot = deepCopy(matrix);

            int existingRow = random.nextInt(rows);
            int existingColumn = random.nextInt(columns);
            int existingTarget = matrix[existingRow][existingColumn];
            compareWithOracle(matrix, existingTarget);

            int arbitraryTarget = -100 + random.nextInt(400);
            compareWithOracle(matrix, arbitraryTarget);

            if (!Arrays.deepEquals(snapshot, matrix)) {
                throw new AssertionError("input mutated at iteration " + iteration);
            }
            randomizedChecks += 2;
        }
    }

    private static int[][] buildMonotoneMatrix(int rows, int columns, Random random) {
        int[][] matrix = new int[rows][columns];
        for (int row = 0; row < rows; row++) {
            for (int column = 0; column < columns; column++) {
                int floor = -50;
                if (row > 0) floor = Math.max(floor, matrix[row - 1][column]);
                if (column > 0) floor = Math.max(floor, matrix[row][column - 1]);
                matrix[row][column] = floor + random.nextInt(4);
            }
        }
        return matrix;
    }

    private static void compareWithOracle(int[][] matrix, int target) {
        boolean expected = fullScan(matrix, target);
        boolean actual = SearchSortedMatrix.contains(matrix, target);
        if (expected != actual) {
            throw new AssertionError("oracle mismatch target=" + target + " matrix=" + Arrays.deepToString(matrix));
        }
    }

    private static boolean fullScan(int[][] matrix, int target) {
        for (int[] row : matrix) {
            for (int value : row) {
                if (value == target) return true;
            }
        }
        return false;
    }

    private static int[][] deepCopy(int[][] matrix) {
        int[][] copy = new int[matrix.length][];
        for (int i = 0; i < matrix.length; i++) {
            copy[i] = matrix[i] == null ? null : matrix[i].clone();
        }
        return copy;
    }

    private static void expectIllegalArgument(int[][] matrix, String label) {
        try {
            SearchSortedMatrix.contains(matrix, 0);
            throw new AssertionError("expected IllegalArgumentException: " + label);
        } catch (IllegalArgumentException expected) {
            fixedChecks++;
        }
    }

    private static void check(boolean expected, boolean actual, String label) {
        fixedChecks++;
        if (expected != actual) {
            throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
        }
    }
}
