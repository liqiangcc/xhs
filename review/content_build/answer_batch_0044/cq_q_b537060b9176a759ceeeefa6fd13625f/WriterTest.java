import java.util.*;
public final class WriterTest {
    static long brute(int[] a) {
        long best=0;
        for(int i=0;i<a.length;i++) for(int j=i+1;j<a.length;j++) best=Math.max(best,(long)Math.min(a[i],a[j])*(j-i));
        return best;
    }
    static void check(int[] a) {
        long got=ContainerWithMostWater.maxArea(a), expected=brute(a);
        if(got!=expected) throw new AssertionError(Arrays.toString(a)+" got="+got+" expected="+expected);
    }
    public static void main(String[] args) {
        check(new int[]{1,8,6,2,5,4,8,3,7});
        check(new int[]{}); check(new int[]{5}); check(new int[]{0,0}); check(new int[]{5,5});
        check(new int[]{1,2,3,4,5}); check(new int[]{5,4,3,2,1}); check(new int[]{2,3,10,5,7,8,9});
        if(ContainerWithMostWater.maxArea(null)!=0L) throw new AssertionError("null boundary");
        try { ContainerWithMostWater.maxArea(new int[]{1,-1,2}); throw new AssertionError("negative accepted"); } catch(IllegalArgumentException expected) {}
        Random r=new Random(20260828L);
        for(int n=2;n<=18;n++) for(int t=0;t<300;t++) { int[] a=new int[n]; for(int i=0;i<n;i++) a[i]=r.nextInt(31); check(a); }
        System.out.println("PASS known=49 boundaries differential=5100 negative=rejected null=0");
    }
}
