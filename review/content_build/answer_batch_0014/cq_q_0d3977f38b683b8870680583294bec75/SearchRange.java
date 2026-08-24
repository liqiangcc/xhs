import java.util.Objects;

public final class SearchRange {
    private SearchRange() {}

    public static int[] searchRange(int[] nums, int target) {
        Objects.requireNonNull(nums, "nums");

        int left = lowerBound(nums, target);
        if (left == nums.length || nums[left] != target) {
            return new int[] {-1, -1};
        }

        int rightExclusive = upperBound(nums, target);
        return new int[] {left, rightExclusive - 1};
    }

    static int lowerBound(int[] nums, int target) {
        int lo = 0;
        int hi = nums.length;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] < target) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        return lo;
    }

    static int upperBound(int[] nums, int target) {
        int lo = 0;
        int hi = nums.length;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] <= target) {
                lo = mid + 1;
            } else {
                hi = mid;
            }
        }
        return lo;
    }
}
