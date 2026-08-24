import java.util.Arrays;
import java.util.Random;

public final class StrictDoubleDominantIndexTest {
    public static void main(String[] args) {
        int fixed = runFixedCases();
        int randomized = runRandomizedDifferential();
        System.out.printf(
                "PASS fixed=%d randomized=%d oracle=quadratic-definition input=unmodified%n",
                fixed,
                randomized);
    }

    private static int runFixedCases() {
        Case[] cases = {
            new Case(null, -1),
            new Case(new int[] {}, -1),
            new Case(new int[] {5}, 0),
            new Case(new int[] {3, 7, 1}, 1),
            new Case(new int[] {3, 6, 1}, -1),
            new Case(new int[] {6, 3}, -1),
            new Case(new int[] {7, 3}, 0),
            new Case(new int[] {1, 0, 0, 3}, 3),
            new Case(new int[] {5, 5, 1}, -1),
            new Case(new int[] {-3, -2}, 0),
            new Case(new int[] {-1, -1}, 0),
            new Case(new int[] {-1, 0}, 1),
            new Case(new int[] {0, -1}, 0),
            new Case(new int[] {Integer.MAX_VALUE, 1}, 0),
            new Case(new int[] {Integer.MAX_VALUE, 1_073_741_824}, -1),
            new Case(new int[] {Integer.MIN_VALUE, Integer.MIN_VALUE}, 0)
        };

        for (Case testCase : cases) {
            int[] before = testCase.nums == null ? null : testCase.nums.clone();
            int actual = StrictDoubleDominantIndex.findFirst(testCase.nums);
            if (actual != testCase.expected) {
                throw new AssertionError(
                        "fixed input=" + Arrays.toString(testCase.nums)
                                + " expected=" + testCase.expected
                                + " actual=" + actual);
            }
            if (!Arrays.equals(before, testCase.nums)) {
                throw new AssertionError("input mutated: " + Arrays.toString(testCase.nums));
            }
            int oracle = quadraticOracle(testCase.nums);
            if (actual != oracle) {
                throw new AssertionError(
                        "fixed oracle mismatch input=" + Arrays.toString(testCase.nums)
                                + " oracle=" + oracle
                                + " actual=" + actual);
            }
        }
        return cases.length;
    }

    private static int runRandomizedDifferential() {
        Random random = new Random(20260823L);
        int checks = 20_000;
        for (int c = 0; c < checks; c++) {
            int length = random.nextInt(25);
            int[] nums = new int[length];
            for (int i = 0; i < length; i++) {
                nums[i] = random.nextInt();
            }
            if (length > 0 && c % 7 == 0) {
                nums[random.nextInt(length)] = Integer.MAX_VALUE;
            }
            if (length > 1 && c % 11 == 0) {
                nums[random.nextInt(length)] = Integer.MIN_VALUE;
            }
            int[] before = nums.clone();
            int actual = StrictDoubleDominantIndex.findFirst(nums);
            int expected = quadraticOracle(nums);
            if (actual != expected) {
                throw new AssertionError(
                        "random input=" + Arrays.toString(nums)
                                + " expected=" + expected
                                + " actual=" + actual);
            }
            if (!Arrays.equals(before, nums)) {
                throw new AssertionError("random input mutated");
            }
        }
        return checks;
    }

    private static int quadraticOracle(int[] nums) {
        if (nums == null || nums.length == 0) {
            return -1;
        }
        for (int i = 0; i < nums.length; i++) {
            boolean qualifies = true;
            for (int j = 0; j < nums.length; j++) {
                if (i == j) {
                    continue;
                }
                if ((long) nums[i] <= 2L * nums[j]) {
                    qualifies = false;
                    break;
                }
            }
            if (qualifies) {
                return i;
            }
        }
        return -1;
    }

    private record Case(int[] nums, int expected) {}
}
