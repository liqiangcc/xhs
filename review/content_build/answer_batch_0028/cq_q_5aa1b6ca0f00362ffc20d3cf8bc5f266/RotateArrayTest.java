import java.util.*;

class RotateArrayTest {
    static void rotate(int[] nums, int k) {
        int n = nums.length;
        if (n <= 1) return;
        k %= n;
        if (k == 0) return;
        reverse(nums, 0, n - 1);
        reverse(nums, 0, k - 1);
        reverse(nums, k, n - 1);
    }
    static void reverse(int[] a, int l, int r) {
        while (l < r) { int t=a[l]; a[l++]=a[r]; a[r--]=t; }
    }
    static int[] oracle(int[] input, int k) {
        int n=input.length;
        int[] out=new int[n];
        if(n==0) return out;
        k%=n;
        for(int i=0;i<n;i++) out[(i+k)%n]=input[i];
        return out;
    }
    static void check(int[] input, int k) {
        int[] actual=input.clone();
        int[] expected=oracle(input,k);
        rotate(actual,k);
        if(!Arrays.equals(actual,expected)) throw new AssertionError(Arrays.toString(input)+" k="+k+" expected="+Arrays.toString(expected)+" actual="+Arrays.toString(actual));
    }
    public static void main(String[] args) {
        check(new int[]{1,2,3,4,5,6,7},3);
        check(new int[]{-1,-100,3,99},2);
        check(new int[]{1},0);
        check(new int[]{1},100000);
        check(new int[]{1,2},0);
        check(new int[]{1,2},2);
        check(new int[]{1,2,3},10);
        check(new int[]{5,5,5,5},3);
        Random rnd=new Random(189);
        for(int t=0;t<5000;t++){
            int n=1+rnd.nextInt(128), k=rnd.nextInt(100001);
            int[] a=new int[n];
            for(int i=0;i<n;i++) a[i]=rnd.nextInt();
            check(a,k);
        }
        System.out.println("PASS fixed=8 randomized=5000 oracle=copy-right-rotation complexity=in-place-three-reversals");
    }
}
