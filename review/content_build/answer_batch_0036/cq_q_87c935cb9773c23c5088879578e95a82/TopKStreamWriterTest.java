import java.util.Arrays;
import java.util.PrimitiveIterator;
import java.util.Random;
import java.util.stream.LongStream;

public final class TopKStreamWriterTest {
    public static void main(String[] args) {
        check(new long[] {}, 100);
        check(new long[] {3,1,2}, 100);
        check(new long[] {5,5,5,4,4}, 3);
        check(new long[] {Long.MIN_VALUE,0,Long.MAX_VALUE,-1,1}, 2);
        check(new long[] {4,1,9,2,8,3,7,6,5}, 4);
        if(TopKStream.largestK(LongStream.of(1,2,3).iterator(),0).length!=0) throw new AssertionError("k=0");
        expect(() -> TopKStream.largestK(null,1));
        expect(() -> TopKStream.largestK(LongStream.of(1).iterator(),-1));
        Random r=new Random(0x87C935CBL);
        for(int c=0;c<5000;c++){
            int n=r.nextInt(150),k=r.nextInt(40);
            long[] a=new long[n]; for(int i=0;i<n;i++) a[i]=r.nextInt(101)-50;
            check(a,k);
        }
        System.out.println("PASS fixed=5 random=5000 duplicates=preserved extremes=pass invalid=reject");
    }
    private static void check(long[] a,int k){
        long[] sorted=a.clone(); Arrays.sort(sorted);
        int take=Math.min(k,sorted.length); long[] expected=new long[take];
        for(int i=0;i<take;i++) expected[i]=sorted[sorted.length-1-i];
        PrimitiveIterator.OfLong it=LongStream.of(a).iterator();
        long[] got=TopKStream.largestK(it,k);
        if(!Arrays.equals(got,expected)) throw new AssertionError("mismatch a="+Arrays.toString(a)+" k="+k+" got="+Arrays.toString(got)+" expected="+Arrays.toString(expected));
    }
    private static void expect(Runnable r){ boolean ok=false; try{r.run();}catch(IllegalArgumentException e){ok=true;} if(!ok) throw new AssertionError("expected IllegalArgumentException"); }
}
