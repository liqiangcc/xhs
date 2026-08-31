import java.util.*;

public final class TwoSumWriterTest {
    private static final Random RNG = new Random(0x62FFE5F2L);

    private static int[] oracle(int[] nums, int target) {
        if (nums == null || nums.length < 2) return new int[0];
        for (int j = 0; j < nums.length; j++) {
            for (int i = 0; i < j; i++) {
                if ((long) nums[i] + nums[j] == target) return new int[]{i,j};
            }
        }
        return new int[0];
    }

    private static void check(int[] nums, int target, String label) {
        int[] before = nums == null ? null : nums.clone();
        int[] expected = oracle(nums, target);
        int[] actual = TwoSum.twoSum(nums, target);
        if (!Arrays.equals(actual, expected)) throw new AssertionError(label + " expected=" + Arrays.toString(expected) + " actual=" + Arrays.toString(actual));
        if (nums != null && !Arrays.equals(nums, before)) throw new AssertionError(label + " mutated input");
    }

    public static void main(String[] args) {
        check(new int[]{2,7,11,15}, 9, "classic");
        check(new int[]{3,2,4}, 6, "middle-pair");
        check(new int[]{3,3}, 6, "duplicates");
        check(new int[]{1,2,3,4}, 100, "no-solution");
        check(new int[]{1,4,2,3}, 5, "multi-solution-earliest-right");
        check(new int[]{1,1,4}, 5, "earliest-complement-index");
        check(new int[]{Integer.MIN_VALUE, 0, Integer.MAX_VALUE}, -1, "extreme-valid");
        check(new int[]{Integer.MAX_VALUE, -1, 0}, Integer.MIN_VALUE, "overflow-complement-no-false-hit");
        check(new int[]{}, 0, "empty");
        check(null, 0, "null");

        for (int t=0; t<30000; t++) {
            int len = RNG.nextInt(18);
            int[] a = new int[len];
            for (int i=0; i<len; i++) {
                int mode=RNG.nextInt(30);
                a[i] = mode==0 ? Integer.MIN_VALUE : mode==1 ? Integer.MAX_VALUE : RNG.nextInt(101)-50;
            }
            int target;
            int mode=RNG.nextInt(20);
            if (mode==0) target=Integer.MIN_VALUE;
            else if (mode==1) target=Integer.MAX_VALUE;
            else target=RNG.nextInt(201)-100;
            check(a,target,"random-"+t);
        }
        System.out.println("PASS fixed=10 random_cases=30000 oracle=earliest-right-bruteforce overflow=pass input_unchanged=pass");
    }
}
