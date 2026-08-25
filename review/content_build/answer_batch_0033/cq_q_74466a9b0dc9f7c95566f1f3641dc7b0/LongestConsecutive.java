import java.util.HashSet;
import java.util.Set;

public final class LongestConsecutive {
    public static int solve(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }
        if (nums.length == 0) {
            return 0;
        }

        Set<Integer> values = new HashSet<>();
        for (int x : nums) {
            values.add(x);
        }

        int best = 0;
        for (int x : values) {
            boolean hasPredecessor =
                    x != Integer.MIN_VALUE && values.contains(x - 1);
            if (hasPredecessor) {
                continue;
            }

            int length = 1;
            int current = x;
            while (current != Integer.MAX_VALUE && values.contains(current + 1)) {
                current++;
                length++;
            }
            if (length > best) {
                best = length;
            }
        }
        return best;
    }
}
