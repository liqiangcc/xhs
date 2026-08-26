import java.util.Arrays;
import java.util.Random;

public final class SortedArrayDeduplicatorWriterTest {
    public static void main(String[] args) {
        check(new int[] {}, new int[] {});
        check(new int[] {1}, new int[] {1});
        check(new int[] {1,1,1,1}, new int[] {1});
        check(new int[] {1,1,2,2,3}, new int[] {1,2,3});
        check(new int[] {-3,-3,-1,0,0,2,2,2,9}, new int[] {-3,-1,0,2,9});
        check(new int[] {Integer.MIN_VALUE,Integer.MIN_VALUE,0,Integer.MAX_VALUE,Integer.MAX_VALUE}, new int[] {Integer.MIN_VALUE,0,Integer.MAX_VALUE});
        boolean threw=false;
        try { SortedArrayDeduplicator.deduplicate(null); } catch (IllegalArgumentException e) { threw=true; }
        if(!threw) throw new AssertionError("null must reject");

        Random r=new Random(0x8811D675L);
        for(int c=0;c<5000;c++){
            int n=r.nextInt(80);
            int[] a=new int[n];
            for(int i=0;i<n;i++) a[i]=r.nextInt(21)-10;
            Arrays.sort(a);
            int[] expected=Arrays.stream(a).distinct().toArray();
            check(a,expected);
        }
        System.out.println("PASS fixed=6 random=5000 null=reject sorted-prefix=exact");
    }

    private static void check(int[] input,int[] expected){
        int[] a=input.clone();
        int k=SortedArrayDeduplicator.deduplicate(a);
        if(k!=expected.length) throw new AssertionError("length mismatch input="+Arrays.toString(input));
        if(!Arrays.equals(Arrays.copyOf(a,k),expected)) throw new AssertionError("prefix mismatch input="+Arrays.toString(input)+" got="+Arrays.toString(Arrays.copyOf(a,k))+" expected="+Arrays.toString(expected));
    }
}
