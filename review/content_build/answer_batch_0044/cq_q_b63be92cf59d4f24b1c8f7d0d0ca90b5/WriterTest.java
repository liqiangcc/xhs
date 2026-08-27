import java.math.BigInteger;
import java.util.*;
public final class WriterTest {
    static BigInteger oracle(int amount, int[] coins) {
        BigInteger[][] ways=new BigInteger[coins.length+1][amount+1];
        for(int i=0;i<=coins.length;i++) Arrays.fill(ways[i],BigInteger.ZERO);
        ways[0][0]=BigInteger.ONE;
        for(int i=1;i<=coins.length;i++) {
            int c=coins[i-1];
            for(int s=0;s<=amount;s++) {
                BigInteger v=ways[i-1][s];
                if(s>=c) v=v.add(ways[i][s-c]);
                ways[i][s]=v;
            }
        }
        return ways[coins.length][amount];
    }
    static void check(int amount,int[] coins) {
        BigInteger got=CoinChangeCombinations.countCombinations(amount,coins), expected=oracle(amount,coins);
        if(!got.equals(expected)) throw new AssertionError("amount="+amount+" coins="+Arrays.toString(coins)+" got="+got+" expected="+expected);
    }
    public static void main(String[] args) {
        if(!CoinChangeCombinations.countCombinations(5,new int[]{1,2,5}).equals(BigInteger.valueOf(4))) throw new AssertionError("known 5/[1,2,5]");
        check(0,new int[]{}); check(7,new int[]{}); check(3,new int[]{2}); check(10,new int[]{10}); check(10,new int[]{5,2,1});
        try { CoinChangeCombinations.countCombinations(-1,new int[]{1}); throw new AssertionError("negative amount accepted"); } catch(IllegalArgumentException expected) {}
        try { CoinChangeCombinations.countCombinations(3,null); throw new AssertionError("null coins accepted"); } catch(IllegalArgumentException expected) {}
        try { CoinChangeCombinations.countCombinations(3,new int[]{0,1}); throw new AssertionError("zero coin accepted"); } catch(IllegalArgumentException expected) {}
        try { CoinChangeCombinations.countCombinations(3,new int[]{-1,1}); throw new AssertionError("negative coin accepted"); } catch(IllegalArgumentException expected) {}
        try { CoinChangeCombinations.countCombinations(3,new int[]{1,1}); throw new AssertionError("duplicate coin accepted"); } catch(IllegalArgumentException expected) {}
        Random r=new Random(20260828L); int cases=0;
        for(int t=0;t<5000;t++) {
            int n=1+r.nextInt(6); LinkedHashSet<Integer> set=new LinkedHashSet<>(); while(set.size()<n) set.add(1+r.nextInt(12));
            int[] coins=set.stream().mapToInt(Integer::intValue).toArray();
            for(int i=coins.length-1;i>0;i--){int j=r.nextInt(i+1),x=coins[i];coins[i]=coins[j];coins[j]=x;}
            int amount=r.nextInt(41); check(amount,coins); cases++;
        }
        BigInteger large=CoinChangeCombinations.countCombinations(1000,java.util.stream.IntStream.rangeClosed(1,100).toArray());
        if(large.bitLength()<=63) throw new AssertionError("large-count boundary did not exceed signed long");
        System.out.println("PASS known=4 boundaries=10 differential="+cases+" biginteger-bits="+large.bitLength());
    }
}
