import java.util.*;

public class writer_validation {
    static int longestIncreasingPath(int[][] matrix) {
        if (matrix == null || matrix.length == 0) return 0;
        int cols = matrix[0].length;
        if (cols == 0) return 0;
        for (int[] row : matrix) {
            if (row == null || row.length != cols) {
                throw new IllegalArgumentException("matrix must be rectangular");
            }
        }
        int rows = matrix.length;
        int[][] memo = new int[rows][cols];
        int best = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                best = Math.max(best, dfs(matrix, r, c, memo));
            }
        }
        return best;
    }

    private static int dfs(int[][] matrix, int r, int c, int[][] memo) {
        if (memo[r][c] != 0) return memo[r][c];
        int best = 1;
        int[][] dirs = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
        for (int[] d : dirs) {
            int nr = r + d[0], nc = c + d[1];
            if (nr < 0 || nr >= matrix.length || nc < 0 || nc >= matrix[0].length) continue;
            if (matrix[nr][nc] <= matrix[r][c]) continue;
            best = Math.max(best, 1 + dfs(matrix, nr, nc, memo));
        }
        memo[r][c] = best;
        return best;
    }

    static int oracle(int[][] a) {
        if (a == null || a.length == 0) return 0;
        int cols = a[0].length;
        if (cols == 0) return 0;
        for (int[] row : a) {
            if (row == null || row.length != cols) throw new IllegalArgumentException("matrix must be rectangular");
        }
        int rows = a.length;
        List<int[]> cells = new ArrayList<>();
        for (int r=0;r<rows;r++) for(int c=0;c<cols;c++) cells.add(new int[]{r,c});
        cells.sort(Comparator.comparingInt(x -> a[x[0]][x[1]]));
        int[][] dp = new int[rows][cols];
        int ans=0;
        int[][] dirs={{1,0},{-1,0},{0,1},{0,-1}};
        for (int[] cell: cells) {
            int r=cell[0], c=cell[1], cur=1;
            for (int[] d: dirs) {
                int nr=r+d[0], nc=c+d[1];
                if(nr<0||nr>=rows||nc<0||nc>=cols) continue;
                if(a[nr][nc] < a[r][c]) cur=Math.max(cur, dp[nr][nc]+1);
            }
            dp[r][c]=cur;
            ans=Math.max(ans,cur);
        }
        return ans;
    }

    static void check(int[][] a) {
        int got=longestIncreasingPath(a), expected=oracle(a);
        if(got!=expected) throw new AssertionError("got="+got+" expected="+expected+" matrix="+Arrays.deepToString(a));
    }

    static int exhaustive(int rows, int cols, int values) {
        int cells=rows*cols, total=1;
        for(int i=0;i<cells;i++) total*=values;
        for(int mask=0;mask<total;mask++) {
            int x=mask; int[][] a=new int[rows][cols];
            for(int i=0;i<cells;i++){a[i/cols][i%cols]=x%values; x/=values;}
            check(a);
        }
        return total;
    }

    public static void main(String[] args) {
        if(longestIncreasingPath(null)!=0) throw new AssertionError("null");
        if(longestIncreasingPath(new int[0][0])!=0) throw new AssertionError("empty rows");
        if(longestIncreasingPath(new int[][]{{}})!=0) throw new AssertionError("empty cols");
        boolean jagged=false; try{longestIncreasingPath(new int[][]{{1,2},{3}});}catch(IllegalArgumentException e){jagged=true;} if(!jagged)throw new AssertionError("jagged");
        int[][][] deterministic={
            {{7}},
            {{1,1,1}},
            {{9,9,4},{6,6,8},{2,1,1}},
            {{3,4,5},{3,2,6},{2,2,1}},
            {{-3,-2,-1},{-4,-5,0}},
            {{1,2,3,4}},
            {{4},{3},{2},{1}},
            {{1,2},{4,3}}
        };
        int[] expected={1,1,4,4,6,4,4,4};
        for(int i=0;i<deterministic.length;i++){
            int got=longestIncreasingPath(deterministic[i]);
            if(got!=expected[i]) throw new AssertionError("deterministic i="+i+" got="+got);
            check(deterministic[i]);
        }
        int exhaustive=0;
        exhaustive += exhaustive(1,1,3);
        exhaustive += exhaustive(1,3,3);
        exhaustive += exhaustive(2,2,3);
        exhaustive += exhaustive(2,3,3);
        Random rnd=new Random(0x970da913L);
        int randomized=20000;
        for(int t=0;t<randomized;t++){
            int rows=1+rnd.nextInt(6), cols=1+rnd.nextInt(6);
            int[][] a=new int[rows][cols];
            for(int r=0;r<rows;r++)for(int c=0;c<cols;c++)a[r][c]=rnd.nextInt(31)-15;
            check(a);
        }
        System.out.println("PASS deterministic="+deterministic.length+" exhaustive="+exhaustive+" randomized="+randomized+" oracle=value-sorted-dp strict=greater rectangular=validated empty=0");
    }
}
