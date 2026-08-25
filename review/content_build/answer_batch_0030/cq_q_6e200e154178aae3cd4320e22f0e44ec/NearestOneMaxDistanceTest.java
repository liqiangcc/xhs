import java.util.ArrayList;
import java.util.List;
import java.util.Random;

public final class NearestOneMaxDistanceTest {
    private static void require(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }

    private static int oracle(int[][] grid) {
        List<int[]> ones = new ArrayList<>();
        int zeros = 0;
        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] == 1) ones.add(new int[]{r,c}); else zeros++;
            }
        }
        if (zeros == 0) return 0;
        if (ones.isEmpty()) return -1;
        int answer = 0;
        for (int r = 0; r < grid.length; r++) {
            for (int c = 0; c < grid[0].length; c++) {
                if (grid[r][c] != 0) continue;
                int best = Integer.MAX_VALUE;
                for (int[] one : ones) best = Math.min(best, Math.abs(r-one[0]) + Math.abs(c-one[1]));
                answer = Math.max(answer, best);
            }
        }
        return answer;
    }

    private static void check(int[][] grid, int expected, String label) {
        int actual = NearestOneMaxDistance.maxNearestOneDistance(grid);
        require(actual == expected, label + " actual=" + actual + " expected=" + expected);
        require(actual == oracle(grid), label + " oracle mismatch");
    }

    public static void main(String[] args) {
        check(new int[][]{{1}}, 0, "all-one-single");
        check(new int[][]{{0}}, -1, "all-zero-single");
        check(new int[][]{{1,0,0}}, 2, "single-row");
        check(new int[][]{{1},{0},{0},{0}}, 3, "single-column");
        check(new int[][]{{1,0,1},{0,0,0},{1,0,1}}, 2, "center-farthest");
        check(new int[][]{{1,0,0,0},{0,0,0,0}}, 4, "rectangle");

        Random random = new Random(20260825L);
        int randomized = 0;
        for (int m = 1; m <= 6; m++) {
            for (int n = 1; n <= 6; n++) {
                for (int t = 0; t < 200; t++) {
                    int[][] grid = new int[m][n];
                    for (int r = 0; r < m; r++) for (int c = 0; c < n; c++) grid[r][c] = random.nextBoolean() ? 1 : 0;
                    int expected = oracle(grid);
                    int actual = NearestOneMaxDistance.maxNearestOneDistance(grid);
                    require(actual == expected, "random mismatch " + m + "x" + n + " t=" + t + " actual=" + actual + " expected=" + expected);
                    randomized++;
                }
            }
        }

        boolean empty = false, ragged = false, nonBinary = false;
        try { NearestOneMaxDistance.maxNearestOneDistance(new int[0][]); } catch (IllegalArgumentException expected) { empty = true; }
        try { NearestOneMaxDistance.maxNearestOneDistance(new int[][]{{1,0},{1}}); } catch (IllegalArgumentException expected) { ragged = true; }
        try { NearestOneMaxDistance.maxNearestOneDistance(new int[][]{{1,2}}); } catch (IllegalArgumentException expected) { nonBinary = true; }
        require(empty && ragged && nonBinary, "validation boundaries failed");
        System.out.println("PASS fixed=6 randomized=" + randomized + " oracle=bruteforce-manhattan degenerate=explicit validation=yes");
    }
}
