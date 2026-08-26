import java.util.ArrayDeque;
import java.util.Queue;

public final class Solution {
    private static final int[][] DIRS = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};

    public boolean hasPath(int[][] maze, int[] start, int[] destination) {
        int rows = maze.length;
        int cols = maze[0].length;
        boolean[][] visited = new boolean[rows][cols];
        Queue<int[]> queue = new ArrayDeque<>();
        queue.offer(new int[] {start[0], start[1]});
        visited[start[0]][start[1]] = true;

        while (!queue.isEmpty()) {
            int[] cur = queue.poll();
            if (cur[0] == destination[0] && cur[1] == destination[1]) {
                return true;
            }

            for (int[] dir : DIRS) {
                int r = cur[0];
                int c = cur[1];
                while (inBounds(r + dir[0], c + dir[1], rows, cols)
                        && maze[r + dir[0]][c + dir[1]] == 0) {
                    r += dir[0];
                    c += dir[1];
                }
                if (!visited[r][c]) {
                    visited[r][c] = true;
                    queue.offer(new int[] {r, c});
                }
            }
        }
        return false;
    }

    private boolean inBounds(int r, int c, int rows, int cols) {
        return r >= 0 && r < rows && c >= 0 && c < cols;
    }
}
