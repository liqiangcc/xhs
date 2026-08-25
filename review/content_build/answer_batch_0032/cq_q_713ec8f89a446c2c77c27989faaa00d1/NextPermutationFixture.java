import java.util.Arrays;
import java.util.Random;

public final class NextPermutationFixture {
    static void actual(int[] nums) {
        if (nums == null || nums.length < 2) return;
        int i = nums.length - 2;
        while (i >= 0 && nums[i] >= nums[i + 1]) i--;
        if (i >= 0) {
            int j = nums.length - 1;
            while (nums[j] <= nums[i]) j--;
            swap(nums, i, j);
        }
        reverse(nums, i + 1, nums.length - 1);
    }
    static void reverse(int[] a,int l,int r){ while(l<r) swap(a,l++,r--); }
    static void swap(int[] a,int i,int j){ int t=a[i]; a[i]=a[j]; a[j]=t; }

    static int compare(int[] a, int[] b) {
        for (int i=0;i<a.length;i++) { int c=Integer.compare(a[i],b[i]); if(c!=0)return c; }
        return 0;
    }
    static int[] oracle(int[] input) {
        if (input == null) return null;
        int[] work=input.clone();
        Holder h=new Holder();
        permute(work,0,input,h);
        return h.bestGreater!=null ? h.bestGreater : h.minimum;
    }
    static final class Holder { int[] bestGreater; int[] minimum; }
    static void permute(int[] a,int pos,int[] original,Holder h){
        if(pos==a.length){
            int[] p=a.clone();
            if(h.minimum==null||compare(p,h.minimum)<0)h.minimum=p;
            if(compare(p,original)>0&&(h.bestGreater==null||compare(p,h.bestGreater)<0))h.bestGreater=p;
            return;
        }
        for(int i=pos;i<a.length;i++){ swap(a,pos,i); permute(a,pos+1,original,h); swap(a,pos,i); }
    }
    static void check(int[] input){
        int[] expected=oracle(input);
        int[] actual=input==null?null:input.clone();
        actual(actual);
        if(!Arrays.equals(actual,expected)) throw new AssertionError("input="+Arrays.toString(input)+" actual="+Arrays.toString(actual)+" expected="+Arrays.toString(expected));
    }
    public static void main(String[] args){
        check(null); check(new int[]{}); check(new int[]{1}); check(new int[]{1,2,3}); check(new int[]{1,3,2}); check(new int[]{3,2,1}); check(new int[]{1,1,5}); check(new int[]{1,5,1}); check(new int[]{2,2,0,1});
        Random r=new Random(0x713ec8L);
        for(int t=0;t<1200;t++){ int n=r.nextInt(8); int[] a=new int[n]; for(int i=0;i<n;i++)a[i]=r.nextInt(5)-2; check(a); }
        System.out.println("PASS fixed-boundaries randomized=1200 brute-force-lexicographic-oracle duplicates-and-wraparound");
    }
}
