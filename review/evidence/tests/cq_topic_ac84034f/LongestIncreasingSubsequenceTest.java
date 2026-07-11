public final class LongestIncreasingSubsequenceTest {
    static void require(int actual,int expected){if(actual!=expected)throw new AssertionError(actual+" != "+expected);}
    public static void main(String[] args) {
        require(LongestIncreasingSubsequence.lengthOfLIS(null),0);
        require(LongestIncreasingSubsequence.lengthOfLIS(new int[]{}),0);
        require(LongestIncreasingSubsequence.lengthOfLIS(new int[]{42}),1);
        require(LongestIncreasingSubsequence.lengthOfLIS(new int[]{7,7,7,7}),1);
        require(LongestIncreasingSubsequence.lengthOfLIS(new int[]{5,4,3,2,1}),1);
        require(LongestIncreasingSubsequence.lengthOfLIS(new int[]{10,9,2,5,3,7,101,18}),4);
        require(LongestIncreasingSubsequence.lengthOfLIS(new int[]{0,1,0,3,2,3}),4);
        int[] values = new int[5];
        enumerate(values, 0);
    }

    static void enumerate(int[] values, int index) {
        if (index == values.length) {
            require(LongestIncreasingSubsequence.lengthOfLIS(values), quadraticStrictLis(values));
            return;
        }
        for (int value = -2; value <= 2; value++) { values[index] = value; enumerate(values, index + 1); }
    }

    static int quadraticStrictLis(int[] values) {
        int[] dp = new int[values.length];
        int best = 0;
        for (int i = 0; i < values.length; i++) {
            dp[i] = 1;
            for (int j = 0; j < i; j++) if (values[j] < values[i]) dp[i] = Math.max(dp[i], dp[j] + 1);
            best = Math.max(best, dp[i]);
        }
        return best;
    }
}
