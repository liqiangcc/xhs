import java.util.HashMap;
import java.util.Map;

final class SubarrayMultipleOfK {
    static long countSubarraysMultipleOfK(int[] nums, int k) {
        requireInput(nums, k);
        long mod = Math.abs((long) k);
        Map<Long, Long> freq = new HashMap<>();
        freq.put(0L, 1L);
        long remainder = 0;
        long count = 0;
        for (int x : nums) {
            remainder = Math.floorMod(remainder + x, mod);
            long previous = freq.getOrDefault(remainder, 0L);
            count += previous;
            freq.put(remainder, previous + 1);
        }
        return count;
    }

    static boolean existsLengthAtLeastTwoMultipleOfK(int[] nums, int k) {
        requireInput(nums, k);
        long mod = Math.abs((long) k);
        Map<Long, Integer> firstIndex = new HashMap<>();
        firstIndex.put(0L, -1);
        long remainder = 0;
        for (int i = 0; i < nums.length; i++) {
            remainder = Math.floorMod(remainder + nums[i], mod);
            Integer first = firstIndex.get(remainder);
            if (first != null) {
                if (i - first >= 2) return true;
            } else {
                firstIndex.put(remainder, i);
            }
        }
        return false;
    }

    private static void requireInput(int[] nums, int k) {
        if (nums == null) throw new IllegalArgumentException("nums must not be null");
        if (k == 0) throw new IllegalArgumentException("this candidate defines the modulo contract only for k != 0");
    }
}
