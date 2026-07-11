import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public final class ThreeSum {
    private ThreeSum() {}

    public static List<List<Integer>> threeSum(int[] nums) {
        List<List<Integer>> result = new ArrayList<>();
        if (nums == null || nums.length < 3) {
            return result;
        }
        int[] values = Arrays.copyOf(nums, nums.length);
        Arrays.sort(values);
        for (int i = 0; i < values.length - 2; i++) {
            if (i > 0 && values[i] == values[i - 1]) {
                continue;
            }
            if (values[i] > 0) {
                break;
            }
            int left = i + 1;
            int right = values.length - 1;
            while (left < right) {
                long sum = (long) values[i] + values[left] + values[right];
                if (sum < 0) {
                    left++;
                } else if (sum > 0) {
                    right--;
                } else {
                    result.add(Arrays.asList(values[i], values[left], values[right]));
                    int leftValue = values[left];
                    int rightValue = values[right];
                    while (left < right && values[left] == leftValue) {
                        left++;
                    }
                    while (left < right && values[right] == rightValue) {
                        right--;
                    }
                }
            }
        }
        return result;
    }

    public static List<List<Integer>> threeSumTarget(int[] nums, int target) {
        List<List<Integer>> result = new ArrayList<>();
        if (nums == null || nums.length < 3) {
            return result;
        }
        int[] values = Arrays.copyOf(nums, nums.length);
        Arrays.sort(values);
        for (int i = 0; i < values.length - 2; i++) {
            if (i > 0 && values[i] == values[i - 1]) {
                continue;
            }
            int left = i + 1;
            int right = values.length - 1;
            while (left < right) {
                long sum = (long) values[i] + values[left] + values[right];
                if (sum < target) {
                    left++;
                } else if (sum > target) {
                    right--;
                } else {
                    result.add(Arrays.asList(values[i], values[left], values[right]));
                    int leftValue = values[left];
                    int rightValue = values[right];
                    while (left < right && values[left] == leftValue) {
                        left++;
                    }
                    while (left < right && values[right] == rightValue) {
                        right--;
                    }
                }
            }
        }
        return result;
    }
}
