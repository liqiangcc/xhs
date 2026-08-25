import java.util.ArrayDeque;

public final class NearestOneMaxDistance {
    private NearestOneMaxDistance() {}

    public static int maxNearestOneDistance(int[][] grid) {
        validate(grid);
        int m = grid.length, n = grid[0].length;
        ArrayDeque<int[]> queue = new ArrayDeque<>();
        boolean[][] seen = new boolean[m][n];
        int zeroCount = 0;
        for (int r = 0; r < m; r++) {
            for (int c = 0; c < n; c++) {
                if (grid[r][c] == 1) {
                    queue.addLast(new int[]{r, c, 0});
                    seen[r][c] = true;
                } else {
                    zeroCount++;
                }
            }
        }
        if (zeroCount == 0) return 0;
        if (queue.isEmpty()) return -1;
        int answer = 0;
        int[][] dirs = {{1,0},{-1,0},{0,1},{0,-1}};
        while (!queue.isEmpty()) {
            int[] cur = queue.removeFirst();
            for (int[] d : dirs) {
                int nr = cur[0] + d[0], nc = cur[1] + d[1];
                if (nr < 0 || nr >= m || nc < 0 || nc >= n || seen[nr][nc]) continue;
                seen[nr][nc] = true;
                int distance = cur[2] + 1;
                answer = Math.max(answer, distance);
                queue.addLast(new int[]{nr, nc, distance});
            }
        }
        return answer;
    }

    private static void validate(int[][] grid) {
        if (grid == null || grid.length == 0 || grid[0] == null || grid[0].length == 0) throw new IllegalArgumentException("grid must be a non-empty rectangle");
        int n = grid[0].length;
        for (int[] row : grid) {
            if (row == null || row.length != n) throw new IllegalArgumentException("grid must be rectangular");
            for (int value : row) if (value != 0 && value != 1) throw new IllegalArgumentException("grid must be binary");
        }
    }
}
