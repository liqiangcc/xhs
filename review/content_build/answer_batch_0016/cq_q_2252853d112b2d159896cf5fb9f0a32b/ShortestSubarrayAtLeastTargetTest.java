import java.util.Random;

public final class ShortestSubarrayAtLeastTargetTest {
    private static int fixedChecks;
    private static int randomizedChecks;

    public static void main(String[] args) {
        fixedCases();
        randomizedAgainstBruteForce();
        System.out.printf("PASS fixed=%d randomized=%d oracle=quadratic-bruteforce%n", fixedChecks, randomizedChecks);
    }

    private static void fixedCases() {
        check(new int[] {2, 3, 1, 2, 4, 3}, 7, 2, "positive classic");
        check(new int[] {2, -1, 2}, 3, 3, "negative breaks positive-only shrink invariant");
        check(new int[] {84, -37, 32, 40, 95}, 167, 3, "mixed values");
        check(new int[] {1, 2}, 4, 0, "no solution");
        check(new int[] {}, 1, 0, "empty");
        check(new int[] {5}, 5, 1, "single exact");
        check(new int[] {-5, -2, -1}, -2, 1, "negative target");
        check(new int[] {Integer.MAX_VALUE, Integer.MAX_VALUE}, Integer.MAX_VALUE, 1, "prefix sum uses long");
        check(new int[] {Integer.MAX_VALUE, Integer.MAX_VALUE}, -1, 1, "very easy negative target");

        boolean threw = false;
        try {
            ShortestSubarrayAtLeastTarget.minLength(null, 1);
        } catch (NullPointerException expected) {
            threw = true;
        }
        if (!threw) {
            throw new AssertionError("null input must fail explicitly");
        }
        fixedChecks++;
    }

    private static void randomizedAgainstBruteForce() {
        Random random = new Random(0x2252853DL);
        for (int t = 0; t < 5000; t++) {
            int n = random.nextInt(25);
            int[] nums = new int[n];
            for (int i = 0; i < n; i++) {
                nums[i] = random.nextInt(41) - 20;
            }
            int target = random.nextInt(111) - 30;
            int expected = bruteForce(nums, target);
            int actual = ShortestSubarrayAtLeastTarget.minLength(nums, target);
            if (actual != expected) {
                throw new AssertionError("random mismatch target=" + target + " expected=" + expected + " actual=" + actual);
            }
            randomizedChecks++;
        }
    }

    private static int bruteForce(int[] nums, int target) {
        int best = nums.length + 1;
        for (int left = 0; left < nums.length; left++) {
            long sum = 0;
            for (int right = left; right < nums.length; right++) {
                sum += nums[right];
                if (sum >= target) {
                    best = Math.min(best, right - left + 1);
                }
            }
        }
        return best == nums.length + 1 ? 0 : best;
    }

    private static void check(int[] nums, int target, int expected, String label) {
        int actual = ShortestSubarrayAtLeastTarget.minLength(nums, target);
        if (actual != expected) {
            throw new AssertionError(label + ": expected=" + expected + " actual=" + actual);
        }
        fixedChecks++;
    }
}
