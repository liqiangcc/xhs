import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;

public final class MergeIntervals {
    public static int[][] merge(int[][] intervals) {
        if (intervals == null || intervals.length == 0) {
            return new int[0][];
        }
        int[][] sorted = copyAndValidate(intervals);
        Arrays.sort(sorted, Comparator.comparingInt((int[] x) -> x[0]).thenComparingInt(x -> x[1]));
        List<int[]> result = new ArrayList<>();
        int currentStart = sorted[0][0];
        int currentEnd = sorted[0][1];
        for (int i = 1; i < sorted.length; i++) {
            int nextStart = sorted[i][0];
            int nextEnd = sorted[i][1];
            if (nextStart <= currentEnd) {
                currentEnd = Math.max(currentEnd, nextEnd);
            } else {
                result.add(new int[] {currentStart, currentEnd});
                currentStart = nextStart;
                currentEnd = nextEnd;
            }
        }
        result.add(new int[] {currentStart, currentEnd});
        return result.toArray(new int[result.size()][]);
    }

    private static int[][] copyAndValidate(int[][] intervals) {
        int[][] copy = new int[intervals.length][2];
        for (int i = 0; i < intervals.length; i++) {
            int[] interval = intervals[i];
            if (interval == null || interval.length != 2 || interval[0] > interval[1]) {
                throw new IllegalArgumentException("each interval must be [start,end] with start <= end");
            }
            copy[i][0] = interval[0];
            copy[i][1] = interval[1];
        }
        return copy;
    }
}
