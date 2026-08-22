import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class SpiralMatrixTraversalTest {
    private static int fixedChecks;
    private static int randomizedChecks;

    public static void main(String[] args) {
        fixedCases();
        randomizedDifferentialCases();
        System.out.printf(
                "PASS fixed=%d randomized=%d oracle=visited-direction-walk input=unmodified%n",
                fixedChecks, randomizedChecks);
    }

    private static void fixedCases() {
        checkList(List.of(), SpiralMatrixTraversal.spiralOrder(null), "null");
        checkList(List.of(), SpiralMatrixTraversal.spiralOrder(new int[0][]), "zero rows");
        checkList(List.of(), SpiralMatrixTraversal.spiralOrder(new int[][] {{}}), "zero columns");
        checkList(List.of(7), SpiralMatrixTraversal.spiralOrder(new int[][] {{7}}), "one cell");
        checkList(List.of(1, 2, 3, 4),
                SpiralMatrixTraversal.spiralOrder(new int[][] {{1, 2, 3, 4}}), "one row");
        checkList(List.of(1, 2, 3, 4),
                SpiralMatrixTraversal.spiralOrder(new int[][] {{1}, {2}, {3}, {4}}), "one column");
        checkList(List.of(1, 2, 3, 6, 5, 4),
                SpiralMatrixTraversal.spiralOrder(new int[][] {{1, 2, 3}, {4, 5, 6}}), "wide 2x3");
        checkList(List.of(1, 2, 4, 6, 5, 3),
                SpiralMatrixTraversal.spiralOrder(new int[][] {{1, 2}, {3, 4}, {5, 6}}), "tall 3x2");
        checkList(List.of(1, 2, 3, 6, 9, 8, 7, 4, 5),
                SpiralMatrixTraversal.spiralOrder(new int[][] {
                        {1, 2, 3}, {4, 5, 6}, {7, 8, 9}
                }), "square 3x3");
        checkList(List.of(1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7),
                SpiralMatrixTraversal.spiralOrder(new int[][] {
                        {1, 2, 3, 4}, {5, 6, 7, 8}, {9, 10, 11, 12}
                }), "rectangular 3x4");
        checkList(List.of(Integer.MIN_VALUE, 0, Integer.MAX_VALUE, 0),
                SpiralMatrixTraversal.spiralOrder(new int[][] {
                        {Integer.MIN_VALUE, 0}, {0, Integer.MAX_VALUE}
                }), "duplicates and int extremes");

        int[][] input = {{1, 2, 3}, {4, 5, 6}};
        int[][] snapshot = deepCopy(input);
        SpiralMatrixTraversal.spiralOrder(input);
        check(true, Arrays.deepEquals(snapshot, input), "input unmodified");

        expectIllegalArgument(new int[][] {{1, 2}, {3}}, "ragged");
        expectIllegalArgument(new int[][] {{1}, null}, "null row");
        expectIllegalArgument(new int[][] {null}, "first row null");
    }

    private static void randomizedDifferentialCases() {
        Random random = new Random(0x2366a87aL);
        for (int iteration = 0; iteration < 5000; iteration++) {
            int rows = 1 + random.nextInt(20);
            int columns = 1 + random.nextInt(20);
            int[][] matrix = new int[rows][columns];
            for (int row = 0; row < rows; row++) {
                for (int column = 0; column < columns; column++) {
                    matrix[row][column] = random.nextInt();
                }
            }
            int[][] snapshot = deepCopy(matrix);

            List<Integer> expected = oracleSpiral(matrix);
            List<Integer> actual = SpiralMatrixTraversal.spiralOrder(matrix);
            if (!expected.equals(actual)) {
                throw new AssertionError(
                        "oracle mismatch at iteration " + iteration
                                + " rows=" + rows + " columns=" + columns);
            }
            if (actual.size() != rows * columns) {
                throw new AssertionError("wrong element count at iteration " + iteration);
            }
            if (!Arrays.deepEquals(snapshot, matrix)) {
                throw new AssertionError("input mutated at iteration " + iteration);
            }
            randomizedChecks++;
        }
    }

    /** Independent direction-walking oracle; it does not use shrinking boundaries. */
    private static List<Integer> oracleSpiral(int[][] matrix) {
        int rows = matrix.length;
        int columns = matrix[0].length;
        boolean[][] visited = new boolean[rows][columns];
        int[] dr = {0, 1, 0, -1};
        int[] dc = {1, 0, -1, 0};
        int direction = 0;
        int row = 0;
        int column = 0;
        List<Integer> result = new ArrayList<>(rows * columns);

        for (int step = 0; step < rows * columns; step++) {
            result.add(matrix[row][column]);
            visited[row][column] = true;

            int nextRow = row + dr[direction];
            int nextColumn = column + dc[direction];
            if (nextRow < 0 || nextRow >= rows || nextColumn < 0 || nextColumn >= columns
                    || visited[nextRow][nextColumn]) {
                direction = (direction + 1) % 4;
                nextRow = row + dr[direction];
                nextColumn = column + dc[direction];
            }
            row = nextRow;
            column = nextColumn;
        }
        return result;
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
            SpiralMatrixTraversal.spiralOrder(matrix);
            throw new AssertionError("expected IllegalArgumentException: " + label);
        } catch (IllegalArgumentException expected) {
            fixedChecks++;
        }
    }

    private static void checkList(List<Integer> expected, List<Integer> actual, String label) {
        fixedChecks++;
        if (!expected.equals(actual)) {
            throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
        }
    }

    private static void check(boolean expected, boolean actual, String label) {
        fixedChecks++;
        if (expected != actual) {
            throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
        }
    }
}
