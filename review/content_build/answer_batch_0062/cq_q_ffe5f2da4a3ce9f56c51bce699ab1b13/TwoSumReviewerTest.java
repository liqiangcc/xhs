import java.util.*;

public final class TwoSumReviewerTest {
    private static final Random RNG = new Random(0x62FFE5F3L);
    private static int exhaustiveCases = 0;

    private static void fail(String m) { throw new AssertionError(m); }

    private static int[] oracle(int[] nums, int target) {
        if (nums == null || nums.length < 2) return new int[0];
        for (int j=0; j<nums.length; j++) {
            for (int i=0; i<j; i++) {
                if ((long)nums[i] + nums[j] == target) return new int[]{i,j};
            }
        }
        return new int[0];
    }

    private static void check(int[] nums, int target, String label) {
        int[] before = nums == null ? null : nums.clone();
        int[] expected = oracle(nums,target);
        int[] actual = TwoSum.twoSum(nums,target);
        if (!Arrays.equals(actual,expected)) fail(label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
        if (actual.length != 0) {
            if (actual.length != 2 || actual[0] < 0 || actual[0] >= actual[1] || actual[1] >= nums.length) fail(label + " invalid indices");
            if ((long)nums[actual[0]] + nums[actual[1]] != target) fail(label + " wrong sum");
        }
        if (nums != null && !Arrays.equals(nums,before)) fail(label + " mutated input");
    }

    private static void enumerate(int[] a, int pos) {
        if (pos == a.length) {
            for (int target=-4; target<=4; target++) {
                exhaustiveCases++;
                check(a.clone(),target,"exhaustive-"+exhaustiveCases);
            }
            return;
        }
        for (int v=-2; v<=2; v++) { a[pos]=v; enumerate(a,pos+1); }
    }

    private static int randomValue() {
        int m=RNG.nextInt(24);
        if(m==0) return Integer.MIN_VALUE;
        if(m==1) return Integer.MAX_VALUE;
        return RNG.nextInt(121)-60;
    }

    public static void main(String[] args) {
        check(new int[]{2,7,11,15},9,"classic");
        check(new int[]{3,2,4},6,"middle-pair");
        check(new int[]{3,3},6,"duplicates");
        check(new int[]{1,2,3,4},100,"none");
        check(new int[]{1,4,2,3},5,"multiple");
        check(new int[]{1,1,4},5,"earliest-left");
        check(new int[]{Integer.MIN_VALUE,0,Integer.MAX_VALUE},-1,"extreme-valid");
        check(new int[]{Integer.MAX_VALUE,-1,0},Integer.MIN_VALUE,"overflow-no-false-hit");
        check(new int[]{7},14,"single");
        check(null,0,"null");

        for(int n=0;n<=5;n++) enumerate(new int[n],0);
        if(exhaustiveCases!=35154) fail("exhaustive count drift: "+exhaustiveCases);

        for(int t=0;t<35000;t++) {
            int n=RNG.nextInt(20); int[] a=new int[n];
            for(int i=0;i<n;i++) a[i]=randomValue();
            int m=RNG.nextInt(20); int target=m==0?Integer.MIN_VALUE:m==1?Integer.MAX_VALUE:RNG.nextInt(241)-120;
            check(a,target,"random-"+t);
        }
        System.out.println("PASS reviewer fixed=10 exhaustive=35154 random=35000 oracle=earliest-right-bruteforce overflow=pass input_unchanged=pass");
    }
}
