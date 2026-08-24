import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

public final class CounterClockwiseMatrixTest {
    private static final long SEED = 0x085F9D4FL;

    public static void main(String[] args) {
        fixedCases();
        raggedRejected();
        randomizedAgainstDirectionOracle();
        System.out.println("PASS fixed=8 randomized=3000 oracle=direction-visited ragged=rejected");
    }

    private static void fixedCases() {
        assertList(List.of(), CounterClockwiseMatrix.fromTopLeft(null), "null");
        assertList(List.of(), CounterClockwiseMatrix.fromTopLeft(new int[0][]), "zero-rows");
        assertList(List.of(), CounterClockwiseMatrix.fromTopLeft(new int[][] { {} }), "zero-cols");
        assertList(List.of(1, 2, 3, 4), CounterClockwiseMatrix.fromTopLeft(new int[][] {{1,2,3,4}}), "single-row");
        assertList(List.of(1, 2, 3, 4), CounterClockwiseMatrix.fromTopLeft(new int[][] {{1},{2},{3},{4}}), "single-col");
        assertList(List.of(1,3,4,2), CounterClockwiseMatrix.fromTopLeft(new int[][] {{1,2},{3,4}}), "two-by-two");
        assertList(List.of(1,5,9,10,11,12,8,4,3,2,6,7),
            CounterClockwiseMatrix.fromTopLeft(new int[][] {{1,2,3,4},{5,6,7,8},{9,10,11,12}}), "three-by-four");
        assertList(List.of(1,4,7,10,11,12,9,6,3,2,5,8),
            CounterClockwiseMatrix.fromTopLeft(new int[][] {{1,2,3},{4,5,6},{7,8,9},{10,11,12}}), "four-by-three");
    }

    private static void raggedRejected() {
        assertThrows(() -> CounterClockwiseMatrix.fromTopLeft(new int[][] {{1,2}, {3}}), "ragged");
        assertThrows(() -> CounterClockwiseMatrix.fromTopLeft(new int[][] {{1}, null}), "null-row");
    }

    private static void randomizedAgainstDirectionOracle() {
        Random random = new Random(SEED);
        for (int round = 0; round < 3000; round++) {
            int rows = 1 + random.nextInt(12);
            int cols = 1 + random.nextInt(12);
            int[][] matrix = new int[rows][cols];
            int value = round * 1000;
            for (int r = 0; r < rows; r++) {
                for (int c = 0; c < cols; c++) {
                    matrix[r][c] = value++;
                }
            }
            assertList(directionOracle(matrix), CounterClockwiseMatrix.fromTopLeft(matrix), "random-" + round);
        }
    }

    private static List<Integer> directionOracle(int[][] matrix) {
        int rows = matrix.length;
        int cols = matrix[0].length;
        boolean[][] seen = new boolean[rows][cols];
        int[][] directions = {{1,0}, {0,1}, {-1,0}, {0,-1}};
        int direction = 0;
        int row = 0;
        int col = 0;
        List<Integer> result = new ArrayList<>(rows * cols);

        for (int count = 0; count < rows * cols; count++) {
            result.add(matrix[row][col]);
            seen[row][col] = true;
            if (count + 1 == rows * cols) {
                break;
            }
            int nextRow = row + directions[direction][0];
            int nextCol = col + directions[direction][1];
            if (nextRow < 0 || nextRow >= rows || nextCol < 0 || nextCol >= cols || seen[nextRow][nextCol]) {
                direction = (direction + 1) % directions.length;
                nextRow = row + directions[direction][0];
                nextCol = col + directions[direction][1];
            }
            row = nextRow;
            col = nextCol;
        }
        return result;
    }

    private static void assertList(List<Integer> expected, List<Integer> actual, String label) {
        if (!expected.equals(actual)) {
            throw new AssertionError(label + ": expected=" + expected + ", actual=" + actual);
        }
    }

    private static void assertThrows(Runnable action, String label) {
        try {
            action.run();
            throw new AssertionError(label + ": expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }
}
