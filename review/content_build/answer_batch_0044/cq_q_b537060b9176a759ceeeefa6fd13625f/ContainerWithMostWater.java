public final class ContainerWithMostWater {
    public static long maxArea(int[] height) {
        if (height == null || height.length < 2) return 0L;
        for (int h : height) if (h < 0) throw new IllegalArgumentException("height must be non-negative");
        int left = 0, right = height.length - 1;
        long best = 0L;
        while (left < right) {
            long width = right - left;
            long boundedHeight = Math.min(height[left], height[right]);
            best = Math.max(best, boundedHeight * width);
            if (height[left] <= height[right]) left++; else right--;
        }
        return best;
    }
}
