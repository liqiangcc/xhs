import java.util.HashMap;
import java.util.Map;

final class ReverseSumPairs {
    static long countPairs(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }
        Map<Long, Long> seen = new HashMap<>();
        long pairs = 0;
        for (int x : nums) {
            if (x < 0) {
                throw new IllegalArgumentException("this candidate defines reverse only for non-negative ints");
            }
            long key = (long) x + reverseNonNegativeInt(x);
            long previous = seen.getOrDefault(key, 0L);
            pairs += previous;
            seen.put(key, previous + 1);
        }
        return pairs;
    }

    static long reverseNonNegativeInt(int x) {
        long reversed = 0;
        int value = x;
        while (value > 0) {
            reversed = reversed * 10 + value % 10;
            value /= 10;
        }
        return reversed;
    }
}
