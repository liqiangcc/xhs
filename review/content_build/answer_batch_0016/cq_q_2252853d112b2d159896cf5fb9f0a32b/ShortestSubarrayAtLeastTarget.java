import java.util.Objects;

public final class ShortestSubarrayAtLeastTarget {
    private ShortestSubarrayAtLeastTarget() {}

    /**
     * Returns the minimum length of a contiguous subarray whose sum is at least target.
     * Returns 0 when no such non-empty subarray exists.
     */
    public static int minLength(int[] nums, int target) {
        Objects.requireNonNull(nums, "nums");
        int n = nums.length;
        long[] prefix = new long[n + 1];
        for (int i = 0; i < n; i++) {
            prefix[i + 1] = prefix[i] + nums[i];
        }

        int[] deque = new int[n + 1];
        int head = 0;
        int tail = 0;
        int best = n + 1;

        for (int i = 0; i <= n; i++) {
            while (head < tail && prefix[i] - prefix[deque[head]] >= target) {
                best = Math.min(best, i - deque[head]);
                head++;
            }
            while (head < tail && prefix[i] <= prefix[deque[tail - 1]]) {
                tail--;
            }
            deque[tail++] = i;
        }

        return best == n + 1 ? 0 : best;
    }
}
