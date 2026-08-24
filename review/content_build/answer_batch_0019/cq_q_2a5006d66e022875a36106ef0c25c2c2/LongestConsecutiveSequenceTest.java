import java.util.Arrays;
import java.util.Random;

public final class LongestConsecutiveSequenceTest {
    public static void main(String[] args) {
        int fixed = runFixed();
        int randomized = runRandomized(5000, 20260824L);
        System.out.println("PASS fixed=" + fixed + " randomized=" + randomized
                + " oracle=sort-deduplicate-scan mutation=none");
    }

    private static int runFixed() {
        int count = 0;
        expect(0, LongestConsecutiveSequence.longestConsecutive(null), "null"); count++;
        expect(0, LongestConsecutiveSequence.longestConsecutive(new int[0]), "empty"); count++;
        expect(1, LongestConsecutiveSequence.longestConsecutive(new int[]{7}), "single"); count++;
        expect(4, LongestConsecutiveSequence.longestConsecutive(new int[]{100,4,200,1,3,2}), "unordered"); count++;
        expect(3, LongestConsecutiveSequence.longestConsecutive(new int[]{1,2,2,3}), "duplicates"); count++;
        expect(5, LongestConsecutiveSequence.longestConsecutive(new int[]{-2,-1,0,1,2}), "negative to positive"); count++;
        expect(2, LongestConsecutiveSequence.longestConsecutive(new int[]{Integer.MIN_VALUE, Integer.MIN_VALUE + 1, 0}), "min edge"); count++;
        expect(2, LongestConsecutiveSequence.longestConsecutive(new int[]{Integer.MAX_VALUE - 1, Integer.MAX_VALUE, 0}), "max edge"); count++;
        expect(1, LongestConsecutiveSequence.longestConsecutive(new int[]{5,5,5,5}), "all duplicate"); count++;
        int[] input = {9,1,4,7,3,-1,0,5,8,-1,6};
        int[] before = input.clone();
        expect(7, LongestConsecutiveSequence.longestConsecutive(input), "mixed");
        if (!Arrays.equals(before, input)) throw new AssertionError("mutation fixed");
        count++;
        return count;
    }

    private static int runRandomized(int rounds, long seed) {
        Random r = new Random(seed);
        for (int i = 0; i < rounds; i++) {
            int len = r.nextInt(60);
            int[] values = new int[len];
            for (int j = 0; j < len; j++) {
                int pick = r.nextInt(40);
                if (pick == 0) values[j] = Integer.MIN_VALUE;
                else if (pick == 1) values[j] = Integer.MAX_VALUE;
                else values[j] = r.nextInt(81) - 40;
            }
            int[] before = values.clone();
            int expected = oracle(values);
            int actual = LongestConsecutiveSequence.longestConsecutive(values);
            if (expected != actual) {
                throw new AssertionError("round=" + i + " expected=" + expected
                        + " actual=" + actual + " values=" + Arrays.toString(values));
            }
            if (!Arrays.equals(before, values)) {
                throw new AssertionError("mutation round=" + i);
            }
        }
        return rounds;
    }

    private static int oracle(int[] values) {
        if (values == null || values.length == 0) return 0;
        int[] copy = values.clone();
        Arrays.sort(copy);
        int best = 1;
        int current = 1;
        for (int i = 1; i < copy.length; i++) {
            if (copy[i] == copy[i - 1]) continue;
            if ((long) copy[i] == (long) copy[i - 1] + 1L) current++;
            else current = 1;
            best = Math.max(best, current);
        }
        return best;
    }

    private static void expect(int expected, int actual, String label) {
        if (expected != actual) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }
}
