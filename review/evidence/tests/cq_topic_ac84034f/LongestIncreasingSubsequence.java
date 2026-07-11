import java.util.Arrays;

public final class LongestIncreasingSubsequence {
    private LongestIncreasingSubsequence() {}
    public static int lengthOfLIS(int[] values) {
        if (values == null || values.length == 0) return 0;
        int[] tails = new int[values.length];
        int size = 0;
        for (int value : values) {
            int left = 0, right = size;
            while (left < right) {
                int middle = left + (right - left) / 2;
                if (tails[middle] >= value) right = middle; else left = middle + 1;
            }
            tails[left] = value;
            if (left == size) size++;
        }
        return size;
    }
}
