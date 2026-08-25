import java.util.Arrays;

public final class MinSubarrayPartition {
    public static int minSegments(int[] nums, long k) {
        int n = nums.length;
        long[] prefix = new long[n + 1];
        for (int i = 0; i < n; i++) prefix[i + 1] = prefix[i] + nums[i];
        int inf = n + 1;
        int[] dp = new int[n + 1];
        Arrays.fill(dp, inf);
        dp[0] = 0;
        for (int i = 1; i <= n; i++) {
            for (int j = 0; j < i; j++) {
                if (dp[j] != inf && prefix[i] - prefix[j] <= k) dp[i] = Math.min(dp[i], dp[j] + 1);
            }
        }
        return dp[n] == inf ? -1 : dp[n];
    }
}
