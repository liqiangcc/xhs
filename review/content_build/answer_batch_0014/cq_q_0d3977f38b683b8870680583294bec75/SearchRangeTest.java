import java.util.Arrays;
import java.util.Random;

public final class SearchRangeTest {
    private static int fixed = 0;
    private static int randomized = 0;

    public static void main(String[] args) {
        check(new int[] {}, 0);
        check(new int[] {5}, 5);
        check(new int[] {5}, 4);
        check(new int[] {5, 7, 7, 8, 8, 10}, 8);
        check(new int[] {5, 7, 7, 8, 8, 10}, 6);
        check(new int[] {2, 2, 2, 2}, 2);
        check(new int[] {1, 2, 3, 4}, 1);
        check(new int[] {1, 2, 3, 4}, 4);
        check(new int[] {Integer.MIN_VALUE, -1, 0, Integer.MAX_VALUE, Integer.MAX_VALUE}, Integer.MAX_VALUE);
        check(new int[] {Integer.MIN_VALUE, Integer.MIN_VALUE, 0, 1}, Integer.MIN_VALUE);
        fixed = 10;

        Random random = new Random(0x0D3977F3L);
        for (int t = 0; t < 5000; t++) {
            int n = random.nextInt(81);
            int[] nums = new int[n];
            int current = random.nextInt(21) - 10;
            for (int i = 0; i < n; i++) {
                current += random.nextInt(3);
                nums[i] = current;
            }

            int target;
            if (t % 997 == 0) {
                target = Integer.MAX_VALUE;
            } else if (t % 991 == 0) {
                target = Integer.MIN_VALUE;
            } else {
                target = random.nextInt(81) - 20;
            }
            check(nums, target);
            randomized++;
        }

        expectNullFailure();
        System.out.println(
                "PASS fixed=" + fixed
                        + " randomized=" + randomized
                        + " oracle=linear-first-last"
                        + " integer_extremes=true null=fail-fast");
    }

    private static void check(int[] nums, int target) {
        int[] expected = oracle(nums, target);
        int[] actual = SearchRange.searchRange(nums, target);
        if (!Arrays.equals(expected, actual)) {
            throw new AssertionError(
                    "nums=" + Arrays.toString(nums)
                            + " target=" + target
                            + " expected=" + Arrays.toString(expected)
                            + " actual=" + Arrays.toString(actual));
        }
    }

    private static int[] oracle(int[] nums, int target) {
        int first = -1;
        int last = -1;
        for (int i = 0; i < nums.length; i++) {
            if (nums[i] == target) {
                if (first == -1) {
                    first = i;
                }
                last = i;
            }
        }
        return new int[] {first, last};
    }

    private static void expectNullFailure() {
        try {
            SearchRange.searchRange(null, 1);
            throw new AssertionError("expected NullPointerException");
        } catch (NullPointerException expected) {
            // explicit implementation contract
        }
    }
}
