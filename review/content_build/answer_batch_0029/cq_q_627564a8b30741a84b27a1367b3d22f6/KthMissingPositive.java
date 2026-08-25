final class KthMissingPositive {
    static long kthMissing(int[] arr, long k) {
        if (arr == null) {
            throw new IllegalArgumentException("arr must not be null");
        }
        if (k <= 0) {
            throw new IllegalArgumentException("k must be positive");
        }
        int left = 0;
        int right = arr.length;
        while (left < right) {
            int mid = left + (right - left) / 2;
            long missing = (long) arr[mid] - (mid + 1L);
            if (missing >= k) right = mid;
            else left = mid + 1;
        }
        return left + k;
    }
}
