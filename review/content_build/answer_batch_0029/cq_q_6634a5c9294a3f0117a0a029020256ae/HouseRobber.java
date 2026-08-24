final class HouseRobber {
    static long rob(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }
        long prev2 = 0;
        long prev1 = 0;
        for (int money : nums) {
            long current = Math.max(prev1, prev2 + money);
            prev2 = prev1;
            prev1 = current;
        }
        return prev1;
    }
}
