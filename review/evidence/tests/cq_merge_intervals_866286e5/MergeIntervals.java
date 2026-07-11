import java.util.Arrays;

public final class MergeIntervals {
    private MergeIntervals() {}

    public static int[][] merge(int[][] intervals) {
        if (intervals == null || intervals.length == 0) return new int[0][0];
        int[][] ordered = new int[intervals.length][2];
        for (int i = 0; i < intervals.length; i++) {
            if (intervals[i] == null || intervals[i].length != 2 || intervals[i][0] > intervals[i][1]) {
                throw new IllegalArgumentException("each interval must satisfy start <= end");
            }
            ordered[i][0] = intervals[i][0];
            ordered[i][1] = intervals[i][1];
        }
        Arrays.sort(ordered, (left, right) -> Integer.compare(left[0], right[0]));
        int[][] merged = new int[ordered.length][2];
        int count = 0;
        int start = ordered[0][0], end = ordered[0][1];
        for (int i = 1; i < ordered.length; i++) {
            int[] next = ordered[i];
            if (next[0] <= end) {
                end = Math.max(end, next[1]);
            } else {
                merged[count++] = new int[] {start, end};
                start = next[0];
                end = next[1];
            }
        }
        merged[count++] = new int[] {start, end};
        return Arrays.copyOf(merged, count);
    }
}
