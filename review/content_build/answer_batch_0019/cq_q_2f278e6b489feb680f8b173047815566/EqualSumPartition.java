public final class EqualSumPartition {
    private EqualSumPartition() {}

    /**
     * Candidate contract for the repository prompt:
     * - nums == null -> false
     * - elements are non-negative Java ints
     * - every input element belongs to exactly one of two groups
     * - either group may be empty
     * - total sum must fit a signed Java int so the pseudo-polynomial DP is representable
     * - the input array is not modified
     */
    public static boolean canPartition(int[] nums) {
        if (nums == null) {
            return false;
        }

        long total = 0L;
        for (int value : nums) {
            if (value < 0) {
                throw new IllegalArgumentException("candidate contract requires non-negative elements");
            }
            total += value;
            if (total > Integer.MAX_VALUE) {
                throw new IllegalArgumentException("candidate contract requires total sum <= Integer.MAX_VALUE");
            }
        }

        if ((total & 1L) != 0L) {
            return false;
        }

        int target = (int) (total / 2L);
        boolean[] reachable = new boolean[target + 1];
        reachable[0] = true;

        for (int value : nums) {
            for (int sum = target; sum >= value; --sum) {
                reachable[sum] = reachable[sum] || reachable[sum - value];
            }
        }
        return reachable[target];
    }
}
