import java.util.ArrayList;
import java.util.List;

public final class SortedPairSum {
    private SortedPairSum() {}

    public static List<int[]> uniqueValuePairs(int[] sorted, int target) {
        List<int[]> result = new ArrayList<>();
        if (sorted == null || sorted.length < 2) {
            return result;
        }

        int left = 0;
        int right = sorted.length - 1;
        while (left < right) {
            int leftValue = sorted[left];
            int rightValue = sorted[right];
            long sum = (long) leftValue + rightValue;

            if (sum < target) {
                left++;
            } else if (sum > target) {
                right--;
            } else {
                result.add(new int[] {leftValue, rightValue});
                while (left < right && sorted[left] == leftValue) {
                    left++;
                }
                while (left < right && sorted[right] == rightValue) {
                    right--;
                }
            }
        }
        return result;
    }
}
