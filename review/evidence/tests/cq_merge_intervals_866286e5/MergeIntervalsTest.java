import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

public final class MergeIntervalsTest {
    private static final int[][] ATOMS = {{-1, -1}, {-1, 0}, {-1, 1}, {0, 0}, {0, 1}, {1, 1}};

    private static int[][] copy(int[][] values) {
        if (values == null) return null;
        int[][] result = new int[values.length][];
        for (int i = 0; i < values.length; i++) result[i] = values[i] == null ? null : values[i].clone();
        return result;
    }

    private static void requireEqual(int[][] actual, int[][] expected, String name) {
        if (!Arrays.deepEquals(actual, expected)) {
            throw new AssertionError(name + ": expected " + Arrays.deepToString(expected) + ", got " + Arrays.deepToString(actual));
        }
    }

    // Independent closure oracle: repeatedly absorb any interval intersecting the current component.
    private static int[][] referenceMerge(int[][] intervals) {
        boolean[] used = new boolean[intervals.length];
        List<int[]> components = new ArrayList<>();
        for (int seed = 0; seed < intervals.length; seed++) {
            if (used[seed]) continue;
            int start = intervals[seed][0], end = intervals[seed][1];
            used[seed] = true;
            boolean changed;
            do {
                changed = false;
                for (int i = 0; i < intervals.length; i++) {
                    if (!used[i] && intervals[i][0] <= end && start <= intervals[i][1]) {
                        start = Math.min(start, intervals[i][0]);
                        end = Math.max(end, intervals[i][1]);
                        used[i] = true;
                        changed = true;
                    }
                }
            } while (changed);
            components.add(new int[] {start, end});
        }
        components.sort(Comparator.comparingInt(interval -> interval[0]));
        return components.toArray(new int[0][0]);
    }

    private static void exhaustiveFourIntervalInputs() {
        int combinations = 1;
        for (int i = 0; i < 4; i++) combinations *= ATOMS.length;
        for (int encoding = 0; encoding < combinations; encoding++) {
            int[][] input = new int[4][2];
            int value = encoding;
            for (int i = 0; i < input.length; i++) {
                input[i] = ATOMS[value % ATOMS.length].clone();
                value /= ATOMS.length;
            }
            int[][] before = copy(input);
            requireEqual(MergeIntervals.merge(input), referenceMerge(before), "exhaustive " + encoding);
            requireEqual(input, before, "input preserved " + encoding);
        }
    }

    private static void requireIllegal(int[][] input) {
        try {
            MergeIntervals.merge(input);
            throw new AssertionError("expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    public static void main(String[] args) {
        requireEqual(MergeIntervals.merge(null), new int[0][0], "null");
        requireEqual(MergeIntervals.merge(new int[0][0]), new int[0][0], "empty");
        requireEqual(MergeIntervals.merge(new int[][] {{2, 2}}), new int[][] {{2, 2}}, "single");
        requireEqual(MergeIntervals.merge(new int[][] {{5, 7}, {1, 4}, {4, 5}}), new int[][] {{1, 7}}, "touching and unordered");
        requireEqual(MergeIntervals.merge(new int[][] {{1, 10}, {2, 3}, {-3, -1}}), new int[][] {{-3, -1}, {1, 10}}, "nested and negative");
        requireEqual(MergeIntervals.merge(new int[][] {{1, 2}, {7, 8}, {3, 6}}), new int[][] {{1, 2}, {3, 6}, {7, 8}}, "separated");
        requireIllegal(new int[][] {{3, 2}});
        requireIllegal(new int[][] {{1}});
        exhaustiveFourIntervalInputs();
    }
}
