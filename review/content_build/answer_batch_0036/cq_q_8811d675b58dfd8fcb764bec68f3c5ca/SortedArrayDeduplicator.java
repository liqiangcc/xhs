public final class SortedArrayDeduplicator {
    private SortedArrayDeduplicator() {}

    public static int deduplicate(int[] nums) {
        if (nums == null) {
            throw new IllegalArgumentException("nums must not be null");
        }
        if (nums.length == 0) {
            return 0;
        }

        int write = 1;
        for (int read = 1; read < nums.length; read++) {
            if (nums[read] != nums[write - 1]) {
                nums[write] = nums[read];
                write++;
            }
        }
        return write;
    }
}
