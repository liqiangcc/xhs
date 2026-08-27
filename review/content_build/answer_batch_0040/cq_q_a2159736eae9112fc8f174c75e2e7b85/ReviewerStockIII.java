import java.util.*;
public final class ReviewerStockIII {
    static int oneTransaction(int[] a,int lo,int hi){
        if(lo>hi) return 0;
        int min=a[lo],best=0;
        for(int i=lo+1;i<=hi;i++){best=Math.max(best,a[i]-min);min=Math.min(min,a[i]);}
        return best;
    }
    static int splitOracle(int[] a){
        int n=a.length,best=oneTransaction(a,0,n-1);
        for(int split=0;split+1<n;split++) best=Math.max(best,oneTransaction(a,0,split)+oneTransaction(a,split+1,n-1));
        return best;
    }
    static void enumerate(int[] a,int i,int max){
        if(i==a.length){int expected=splitOracle(a),actual=StockIII.solve(a);if(actual!=expected)throw new AssertionError("mismatch "+Arrays.toString(a)+" expected="+expected+" actual="+actual);return;}
        for(int v=0;v<=max;v++){a[i]=v;enumerate(a,i+1,max);}
    }
    public static void main(String[] args){
        int[][] cases={{3,3,5,0,0,3,1,4},{1,2,3,4,5},{7,6,4,3,1},{1},{2,1,4,5,2,9,7}};
        int[] expected={6,4,0,0,11};
        for(int i=0;i<cases.length;i++)if(StockIII.solve(cases[i])!=expected[i])throw new AssertionError("boundary "+i);
        for(int n=1;n<=7;n++)enumerate(new int[n],0,3);
        System.out.println("PASS split-prefix-suffix-oracle length=1..7 prices=0..3 boundaries=6,4,0,0,11");
    }
}
