import java.util.HashSet;
import java.util.Set;

public final class LongestConsecutiveSequence {
    private LongestConsecutiveSequence() {}

    /**
     * Candidate contract: for an int array, return the maximum number of distinct
     * integer values that can form a +1-by-value consecutive run, regardless of
     * input order. Duplicates do not extend the run. Null/empty input returns 0.
     * The input array is not mutated.
     */
    public static int longestConsecutive(int[] values) {
        if (values == null || values.length == 0) {
            return 0;
        }
        Set<Long> set = new HashSet<>();
        for (int value : values) {
            set.add((long) value);
        }

        int best = 0;
        for (long value : set) {
            if (set.contains(value - 1L)) {
                continue;
            }
            int length = 1;
            long current = value;
            while (set.contains(current + 1L)) {
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
