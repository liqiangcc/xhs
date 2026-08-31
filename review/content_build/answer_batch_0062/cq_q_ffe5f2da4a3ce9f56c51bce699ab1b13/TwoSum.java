import java.util.HashMap;
import java.util.Map;

public final class TwoSum {
    public static int[] twoSum(int[] nums, int target) {
        if (nums == null || nums.length < 2) return new int[0];
        Map<Integer, Integer> firstIndex = new HashMap<>();
        for (int j = 0; j < nums.length; j++) {
            long needLong = (long) target - nums[j];
            if (needLong >= Integer.MIN_VALUE && needLong <= Integer.MAX_VALUE) {
                Integer i = firstIndex.get((int) needLong);
                if (i != null) return new int[]{i, j};
            }
            firstIndex.putIfAbsent(nums[j], j);
        }
        return new int[0];
    }
}
