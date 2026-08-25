import java.util.Random;

public final class NumMatrixFixture {
    static final class Actual {
        final long[][] p;final int rows,cols;
        Actual(int[][] m){
            if(m==null)throw new NullPointerException();
            if(m.length==0||m[0]==null||m[0].length==0)throw new IllegalArgumentException();
            rows=m.length;cols=m[0].length;p=new long[rows+1][cols+1];
            for(int r=0;r<rows;r++){
                if(m[r]==null||m[r].length!=cols)throw new IllegalArgumentException();
                for(int c=0;c<cols;c++)p[r+1][c+1]=(long)m[r][c]+p[r][c+1]+p[r+1][c]-p[r][c];
            }
        }
        long sum(int r1,int c1,int r2,int c2){
            if(r1<0||c1<0||r2<r1||c2<c1||r2>=rows||c2>=cols)throw new IndexOutOfBoundsException();
            return p[r2+1][c2+1]-p[r1][c2+1]-p[r2+1][c1]+p[r1][c1];
        }
    }
    static long brute(int[][]m,int r1,int c1,int r2,int c2){long s=0;for(int r=r1;r<=r2;r++)for(int c=c1;c<=c2;c++)s+=m[r][c];return s;}
    public static void main(String[]args){
        int[][] known={{3,0,1,4,2},{5,6,3,2,1},{1,2,0,1,5},{4,1,0,1,7},{1,0,3,0,5}};Actual k=new Actual(known);if(k.sum(2,1,4,3)!=8||k.sum(1,1,2,2)!=11||k.sum(1,2,2,4)!=12)throw new AssertionError("known examples");
        int[][] overflow={{Integer.MAX_VALUE,Integer.MAX_VALUE}};if(new Actual(overflow).sum(0,0,0,1)!=4294967294L)throw new AssertionError("long overflow boundary");
        int[][] snapshot={{1,2},{3,4}};Actual frozen=new Actual(snapshot);snapshot[0][0]=100;if(frozen.sum(0,0,1,1)!=10)throw new AssertionError("not immutable snapshot");
        boolean jag=false,bounds=false;try{new Actual(new int[][]{{1},{2,3}});}catch(IllegalArgumentException e){jag=true;}try{new Actual(new int[][]{{1}}).sum(0,0,1,0);}catch(IndexOutOfBoundsException e){bounds=true;}if(!jag||!bounds)throw new AssertionError("boundary contract");
        Random r=new Random(304L);int matrices=0,queries=0;
        for(int t=0;t<3000;t++){int rows=1+r.nextInt(7),cols=1+r.nextInt(7);int[][]m=new int[rows][cols];for(int i=0;i<rows;i++)for(int j=0;j<cols;j++)m[i][j]=r.nextInt(2001)-1000;Actual a=new Actual(m);matrices++;for(int q=0;q<20;q++){int r1=r.nextInt(rows),r2=r.nextInt(rows),c1=r.nextInt(cols),c2=r.nextInt(cols);if(r1>r2){int x=r1;r1=r2;r2=x;}if(c1>c2){int x=c1;c1=c2;c2=x;}if(a.sum(r1,c1,r2,c2)!=brute(m,r1,c1,r2,c2))throw new AssertionError("random mismatch");queries++;}}
        System.out.println("PASS known-examples matrices=3000 randomized-queries=60000 brute-force-oracle snapshot-immutable long-overflow jagged-and-bounds");
    }
}
