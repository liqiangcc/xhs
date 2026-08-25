public final class MedianTwoSortedArrays {
    private MedianTwoSortedArrays() {}

    public static double median(int[] nums1, int[] nums2) {
        if (nums1 == null || nums2 == null) throw new IllegalArgumentException("arrays must be non-null");
        if (nums1.length + nums2.length == 0) throw new IllegalArgumentException("at least one array must be non-empty");
        if (nums1.length > nums2.length) return median(nums2, nums1);
        int m = nums1.length, n = nums2.length;
        int leftSize = (m + n + 1) / 2;
        int low = 0, high = m;
        while (low <= high) {
            int i = low + (high - low) / 2;
            int j = leftSize - i;
            long aLeft = i == 0 ? Long.MIN_VALUE : nums1[i - 1];
            long aRight = i == m ? Long.MAX_VALUE : nums1[i];
            long bLeft = j == 0 ? Long.MIN_VALUE : nums2[j - 1];
            long bRight = j == n ? Long.MAX_VALUE : nums2[j];
            if (aLeft <= bRight && bLeft <= aRight) {
                long maxLeft = Math.max(aLeft, bLeft);
                if (((m + n) & 1) == 1) return maxLeft;
                long minRight = Math.min(aRight, bRight);
                return (maxLeft + minRight) / 2.0;
            }
            if (aLeft > bRight) high = i - 1;
            else low = i + 1;
        }
        throw new IllegalArgumentException("inputs must be sorted non-decreasingly");
    }
}
