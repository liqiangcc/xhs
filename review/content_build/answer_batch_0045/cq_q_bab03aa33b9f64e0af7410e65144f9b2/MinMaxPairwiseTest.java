import java.util.*;
public final class MinMaxPairwiseTest {
    static void check(int[] a){int[] g=MinMaxPairwise.minMax(a);int lo=a[0],hi=a[0];for(int x:a){lo=Math.min(lo,x);hi=Math.max(hi,x);}if(g[0]!=lo||g[1]!=hi)throw new AssertionError(Arrays.toString(a)+" -> "+Arrays.toString(g)+" expected="+lo+","+hi);}
    static int counted(int[] a){int c=0,min,max,i;if((a.length&1)==0){c++;if(a[0]<=a[1]){min=a[0];max=a[1];}else{min=a[1];max=a[0];}i=2;}else{min=max=a[0];i=1;}while(i<a.length){int s,l;c++;if(a[i]<=a[i+1]){s=a[i];l=a[i+1];}else{s=a[i+1];l=a[i];}c++;if(s<min)min=s;c++;if(l>max)max=l;i+=2;}return c;}
    public static void main(String[] args){
        int[][] fixed={{7},{1,2},{2,1},{3,1,2},{4,4,4,4},{Integer.MIN_VALUE,0,Integer.MAX_VALUE,-1,9}};for(int[] a:fixed)check(a);
        Random r=new Random(20260828L);int random=0;for(int n=1;n<=101;n++)for(int t=0;t<100;t++){int[] a=new int[n];for(int i=0;i<n;i++)a[i]=r.nextInt();check(a);int expected=(n==1?0:((n&1)==0?3*n/2-2:3*(n-1)/2));if(counted(a)!=expected)throw new AssertionError("count n="+n+" got="+counted(a)+" expected="+expected);random++;}
        try{MinMaxPairwise.minMax(null);throw new AssertionError("null accepted");}catch(IllegalArgumentException ok){}try{MinMaxPairwise.minMax(new int[0]);throw new AssertionError("empty accepted");}catch(IllegalArgumentException ok){}
        System.out.println("PASS fixed="+fixed.length+" random="+random+" comparison-formulas=verified null-empty=rejected");
    }
}
