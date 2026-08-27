import java.util.*;

public final class StockIII {
    static int solve(int[] prices) {
        long buy1=Long.MIN_VALUE/4, sell1=0, buy2=Long.MIN_VALUE/4, sell2=0;
        for (int p : prices) {
            long nb1=Math.max(buy1,-1L*p);
            long ns1=Math.max(sell1,buy1+p);
            long nb2=Math.max(buy2,sell1-p);
            long ns2=Math.max(sell2,buy2+p);
            buy1=nb1; sell1=ns1; buy2=nb2; sell2=ns2;
        }
        return (int)sell2;
    }

    static int brute(int[] a) {
        int n=a.length,best=0;
        for(int b1=0;b1<n;b1++) for(int s1=b1+1;s1<n;s1++) {
            best=Math.max(best,a[s1]-a[b1]);
            for(int b2=s1+1;b2<n;b2++) for(int s2=b2+1;s2<n;s2++)
                best=Math.max(best,(a[s1]-a[b1])+(a[s2]-a[b2]));
        }
        return Math.max(best,0);
    }

    static void enumerate(int[] a,int i,int max) {
        if(i==a.length){ if(solve(a)!=brute(a)) throw new AssertionError("mismatch "+Arrays.toString(a)+" dp="+solve(a)+" brute="+brute(a)); return; }
        for(int v=0;v<=max;v++){a[i]=v;enumerate(a,i+1,max);}
    }

    public static void main(String[] args) {
        if(solve(new int[]{3,3,5,0,0,3,1,4})!=6) throw new AssertionError("official example 1");
        if(solve(new int[]{1,2,3,4,5})!=4) throw new AssertionError("official example 2");
        if(solve(new int[]{7,6,4,3,1})!=0) throw new AssertionError("falling");
        if(solve(new int[]{1})!=0) throw new AssertionError("single day");
        for(int n=1;n<=6;n++) enumerate(new int[n],0,3);
        System.out.println("PASS official=6,4,0,0 exhaustive-length=1..6 prices=0..3 vs independent date enumeration");
    }
}
