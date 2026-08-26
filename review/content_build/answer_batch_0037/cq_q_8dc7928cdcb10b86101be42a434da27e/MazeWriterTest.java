import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Queue;
import java.util.Random;

public final class MazeWriterTest {
    private static long randomCases;
    public static void main(String[] args) {
        Solution s = new Solution();
        int[][] sample = {
            {0,0,1,0,0},
            {0,0,0,0,0},
            {0,0,0,1,0},
            {1,1,0,1,1},
            {0,0,0,0,0}
        };
        check(s, sample, new int[]{0,4}, new int[]{4,4}, true);
        check(s, sample, new int[]{0,4}, new int[]{3,2}, false);
        check(s, new int[][]{{0,0,0},{0,0,0},{0,0,0}}, new int[]{0,0}, new int[]{1,2}, false);
        check(s, new int[][]{{0}}, new int[]{0,0}, new int[]{0,0}, true);
        Random rnd = new Random(0x8DC7928CL);
        for (int rows=2; rows<=9; rows++) {
            for (int cols=2; cols<=9; cols++) {
                for (int round=0; round<35; round++) {
                    int[][] maze = randomMaze(rows, cols, rnd);
                    int[] start = randomOpen(maze, rnd);
                    int[] dest = randomOpen(maze, rnd);
                    boolean expected = reference(maze, start, dest);
                    check(s, maze, start, dest, expected);
                    randomCases++;
                }
            }
        }
        System.out.printf("PASS fixed=4 randomized=%d pass-through-not-stop=pass input-unmodified=pass%n", randomCases);
    }

    static void check(Solution s, int[][] maze, int[] start, int[] dest, boolean expected) {
        int[][] before = copy(maze);
        boolean actual = s.hasPath(maze, start, dest);
        if (actual != expected) throw new AssertionError("expected="+expected+" actual="+actual+" start="+Arrays.toString(start)+" dest="+Arrays.toString(dest));
        if (!Arrays.deepEquals(before, maze)) throw new AssertionError("maze mutated");
    }

    static boolean reference(int[][] maze, int[] start, int[] dest) {
        int rows=maze.length, cols=maze[0].length;
        int[][][] stop = new int[rows][cols][8];
        int[][] dirs={{1,0},{-1,0},{0,1},{0,-1}};
        for (int r=0;r<rows;r++) for (int c=0;c<cols;c++) if (maze[r][c]==0) {
            for (int d=0;d<4;d++) {
                int x=r,y=c;
                while (inside(x+dirs[d][0],y+dirs[d][1],rows,cols) && maze[x+dirs[d][0]][y+dirs[d][1]]==0) { x+=dirs[d][0]; y+=dirs[d][1]; }
                stop[r][c][2*d]=x; stop[r][c][2*d+1]=y;
            }
        }
        boolean[][] seen=new boolean[rows][cols];
        Queue<int[]> q=new ArrayDeque<>(); q.offer(new int[]{start[0],start[1]}); seen[start[0]][start[1]]=true;
        while(!q.isEmpty()) {
            int[] p=q.poll(); if(p[0]==dest[0]&&p[1]==dest[1]) return true;
            for(int d=0;d<4;d++) { int nr=stop[p[0]][p[1]][2*d], nc=stop[p[0]][p[1]][2*d+1]; if(!seen[nr][nc]) {seen[nr][nc]=true;q.offer(new int[]{nr,nc});} }
        }
        return false;
    }

    static int[][] randomMaze(int rows,int cols,Random rnd) {
        int[][] m=new int[rows][cols];
        for(int r=0;r<rows;r++) for(int c=0;c<cols;c++) m[r][c]=rnd.nextDouble()<0.28?1:0;
        boolean any=false; for(int[] row:m) for(int v:row) if(v==0) any=true;
        if(!any) m[rnd.nextInt(rows)][rnd.nextInt(cols)]=0;
        return m;
    }
    static int[] randomOpen(int[][] maze,Random rnd) { while(true){int r=rnd.nextInt(maze.length),c=rnd.nextInt(maze[0].length);if(maze[r][c]==0)return new int[]{r,c};} }
    static boolean inside(int r,int c,int rows,int cols){return r>=0&&r<rows&&c>=0&&c<cols;}
    static int[][] copy(int[][] a){int[][] b=new int[a.length][];for(int i=0;i<a.length;i++)b[i]=a[i].clone();return b;}
}
