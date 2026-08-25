import java.util.Arrays;

public final class SpiralMatrixIITest {
    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }

    private static int[][] oracle(int n) {
        int[][] matrix = new int[n][n];
        boolean[][] seen = new boolean[n][n];
        int[][] dirs = {{0,1},{1,0},{0,-1},{-1,0}};
        int row = 0, col = 0, dir = 0;
        for (int value = 1; value <= n * n; value++) {
            matrix[row][col] = value;
            seen[row][col] = true;
            if (value == n * n) break;
            int nr = row + dirs[dir][0], nc = col + dirs[dir][1];
            if (nr < 0 || nr >= n || nc < 0 || nc >= n || seen[nr][nc]) {
                dir = (dir + 1) % 4;
                nr = row + dirs[dir][0];
                nc = col + dirs[dir][1];
            }
            row = nr;
            col = nc;
        }
        return matrix;
    }

    private static void assertMatrix(int[][] actual, int[][] expected, String label) {
        require(Arrays.deepEquals(actual, expected), label + " actual=" + Arrays.deepToString(actual) + " expected=" + Arrays.deepToString(expected));
    }

    private static void assertPermutation(int[][] matrix) {
        int n = matrix.length;
        boolean[] seen = new boolean[n * n + 1];
        for (int[] row : matrix) {
            require(row.length == n, "not square");
            for (int value : row) {
                require(value >= 1 && value <= n * n, "value out of range: " + value);
                require(!seen[value], "duplicate value: " + value);
                seen[value] = true;
            }
        }
        for (int value = 1; value <= n * n; value++) require(seen[value], "missing value: " + value);
    }

    public static void main(String[] args) {
        assertMatrix(SpiralMatrixII.generateMatrix(1), new int[][]{{1}}, "n=1");
        assertMatrix(SpiralMatrixII.generateMatrix(2), new int[][]{{1,2},{4,3}}, "n=2");
        assertMatrix(SpiralMatrixII.generateMatrix(3), new int[][]{{1,2,3},{8,9,4},{7,6,5}}, "n=3");
        int checked = 0;
        for (int n = 1; n <= 20; n++) {
            int[][] actual = SpiralMatrixII.generateMatrix(n);
            assertMatrix(actual, oracle(n), "oracle n=" + n);
            assertPermutation(actual);
            checked++;
        }
        boolean rejected = false;
        try { SpiralMatrixII.generateMatrix(0); } catch (IllegalArgumentException expected) { rejected = true; }
        require(rejected, "helper should reject non-positive n");
        System.out.println("PASS fixed=3 domain=1..20 oracle=direction-visited permutation=yes invalid-helper=yes checked=" + checked);
    }
}
