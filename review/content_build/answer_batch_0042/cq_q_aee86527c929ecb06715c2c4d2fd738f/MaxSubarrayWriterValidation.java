import java.util.*;
public final class MaxSubarrayWriterValidation {
    static long brute(int[] a){long best=Long.MIN_VALUE;for(int i=0;i<a.length;i++){long s=0;for(int j=i;j<a.length;j++){s+=a[j];best=Math.max(best,s);}}return best;}
    static void check(int[] a){long got=Solution.maxSubarraySum(a),want=brute(a);if(got!=want)throw new AssertionError(Arrays.toString(a)+" got="+got+" want="+want);}
    static long exhaustive=0;
    static void gen(int[] a,int i,int[] vals){if(i==a.length){check(a);exhaustive++;return;}for(int v:vals){a[i]=v;gen(a,i+1,vals);}}
    public static void main(String[] args){
        check(new int[]{-2,1,-3,4,-1,2,1,-5,4}); check(new int[]{-5,-2,-7}); check(new int[]{0}); check(new int[]{Integer.MAX_VALUE,Integer.MAX_VALUE}); check(new int[]{Integer.MIN_VALUE});
        int[] vals={-3,-1,0,2,4};for(int n=1;n<=7;n++)gen(new int[n],0,vals);
        Random r=new Random(0x4B4144414EL);for(int t=0;t<20000;t++){int n=1+r.nextInt(80),a[]=new int[n];for(int i=0;i<n;i++)a[i]=r.nextInt(2001)-1000;check(a);}
        try{Solution.maxSubarraySum(new int[0]);throw new AssertionError("empty accepted");}catch(IllegalArgumentException expected){}
        try{Solution.maxSubarraySum(null);throw new AssertionError("null accepted");}catch(NullPointerException expected){}
        System.out.println("PASS fixed=5 exhaustive="+exhaustive+" random=20000 all-negative+zero+int-extremes=covered empty+null=rejected brute-oracle=match");
    }
}
